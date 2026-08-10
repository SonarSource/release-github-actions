"""
Unit tests for detect_rule_props_changed.

Each detection test builds a throwaway git repository, tags a baseline, applies a change and
runs the detector end to end. Exercising real `git diff` output is the point: the matcher's
whole job is to tell genuine declaration changes apart from diff noise, and hand-written diff
fixtures would not reproduce the hunk framing that noise arrives in.
"""

import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from detect_rule_props_changed import (  # noqa: E402
    ATTRIBUTE_REGEX,
    MAX_REPORTED_FILES,
    RULESET,
    DetectionRule,
    detect,
    emit,
    find_matches,
    iter_hunks,
    main,
    parse_extra_patterns,
    pathspec_matches,
    report,
    resolve_base_ref,
)

BASELINE_TAG = '1.0.0.100'

# A check class as the Java analyzers write them: the annotation, and an import of it.
JAVA_CHECK = """\
package org.sonar.python.checks;

import java.util.regex.Pattern;
import org.sonar.check.Rule;
import org.sonar.check.RuleProperty;

@Rule(key = "S100")
public class NamingCheck {

  private static final String MESSAGE = "Rename this.";

  @RuleProperty(
    key = "format",
    description = "Regular expression the names are checked against.",
    defaultValue = "^[a-z][a-zA-Z0-9]*$")
  public String format = "^[a-z][a-zA-Z0-9]*$";

  public void check() {
    Pattern.compile(format);
  }
}
"""


def git(repo, *args):
    subprocess.run(['git'] + list(args), cwd=repo, check=True,
                   capture_output=True, text=True)


class DetectorTestCase(unittest.TestCase):
    """Base class providing a scratch git repository with a tagged baseline."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        git(self.repo, 'init', '-q', '-b', 'master')
        git(self.repo, 'config', 'user.email', 'test@example.com')
        git(self.repo, 'config', 'user.name', 'Test')
        git(self.repo, 'config', 'commit.gpgsign', 'false')

    def write(self, relative_path, content):
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def commit(self, message='change'):
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '-q', '-m', message)

    def tag_baseline(self, tag=BASELINE_TAG):
        git(self.repo, 'tag', tag)

    def run_detect(self, include_test_sources=False, rules=None, base_ref=BASELINE_TAG):
        return detect(str(self.repo), base_ref, 'HEAD',
                      rules if rules is not None else RULESET, include_test_sources)

    def assertDetected(self, msg=''):
        matches = self.run_detect()
        self.assertTrue(matches, msg or f'expected a detection, got none. {matches}')
        return matches

    def assertNotDetected(self, msg=''):
        matches = self.run_detect()
        self.assertFalse(matches, msg or f'expected no detection, got {matches}')


class TestJavaAnnotation(DetectorTestCase):
    """The @RuleProperty convention used by sonar-python, sonar-java, sonar-go, sonar-iac."""

    def setUp(self):
        super().setUp()
        self.path = 'checks/src/main/java/org/sonar/python/checks/NamingCheck.java'
        self.write(self.path, JAVA_CHECK)
        self.commit('baseline')
        self.tag_baseline()

    def test_added_property_is_detected(self):
        self.write(self.path, JAVA_CHECK.replace(
            '  public void check() {',
            '  @RuleProperty(key = "maximum", defaultValue = "10")\n'
            '  public int maximum = 10;\n\n'
            '  public void check() {'))
        self.commit()
        self.assertDetected()

    def test_removed_property_is_detected(self):
        without_property = JAVA_CHECK.replace(
            '  @RuleProperty(\n'
            '    key = "format",\n'
            '    description = "Regular expression the names are checked against.",\n'
            '    defaultValue = "^[a-z][a-zA-Z0-9]*$")\n', '')
        self.assertNotEqual(without_property, JAVA_CHECK, 'fixture replacement did not apply')
        self.write(self.path, without_property)
        self.commit()
        self.assertDetected()

    def test_renamed_property_key_is_detected(self):
        """The real sonar-java 8.25 -> 8.26 change: noavThreshold -> nodvThreshold."""
        self.write(self.path, JAVA_CHECK.replace('key = "format"', 'key = "namingFormat"'))
        self.commit()
        self.assertDetected()

    def test_changed_default_value_is_detected(self):
        """The attribute rule: only the defaultValue line moves, not the annotation itself."""
        self.write(self.path, JAVA_CHECK.replace(
            'defaultValue = "^[a-z][a-zA-Z0-9]*$")',
            'defaultValue = "^[A-Z][a-zA-Z0-9]*$")'))
        self.commit()
        matches = self.assertDetected()
        self.assertTrue(any('defaultValue' in line for _, line in matches))

    def test_added_import_near_annotation_is_not_detected(self):
        """
        Regression for the dominant false positive in real history: adding an unrelated import
        puts `import org.sonar.check.RuleProperty;` in the hunk as context.
        """
        self.write(self.path, JAVA_CHECK.replace(
            'import java.util.regex.Pattern;',
            'import java.util.List;\nimport java.util.regex.Pattern;'))
        self.commit()
        self.assertNotDetected()

    def test_unrelated_constant_near_annotation_is_not_detected(self):
        """A constant three lines above the annotation shares its hunk but is not a property."""
        self.write(self.path, JAVA_CHECK.replace(
            'private static final String MESSAGE = "Rename this.";',
            'private static final String MESSAGE = "Please rename this.";'))
        self.commit()
        self.assertNotDetected()

    def test_unrelated_body_change_is_not_detected(self):
        self.write(self.path, JAVA_CHECK.replace(
            'Pattern.compile(format);',
            'Pattern.compile(format, 0);'))
        self.commit()
        self.assertNotDetected()

    def test_no_change_at_all_is_not_detected(self):
        self.write('README.md', 'unrelated\n')
        self.commit()
        self.assertNotDetected()


class TestOtherConventions(DetectorTestCase):
    """The non-@RuleProperty conventions: Kotlin, C#, central RuleParameter lists, SonarJS."""

    def test_kotlin_annotation_is_detected(self):
        path = 'sonar-kotlin-checks/src/main/java/org/sonarsource/kotlin/checks/LineCheck.kt'
        self.write(path, 'class LineCheck {\n  val max = 120\n}\n')
        self.commit('baseline')
        self.tag_baseline()
        self.write(path,
                   'class LineCheck {\n'
                   '  @RuleProperty(key = "maximumLineLength", defaultValue = "120")\n'
                   '  val max = 120\n}\n')
        self.commit()
        self.assertDetected()

    def test_csharp_attribute_is_detected(self):
        """sonar-dotnet-enterprise declares parameters with a [RuleParameter] attribute."""
        path = 'analyzers/src/SonarAnalyzer.CSharp/Rules/FunctionComplexity.cs'
        self.write(path, 'public class FunctionComplexity\n{\n    public int Maximum { get; set; }\n}\n')
        self.commit('baseline')
        self.tag_baseline()
        self.write(path,
                   'public class FunctionComplexity\n{\n'
                   '    [RuleParameter("threshold", PropertyType.Integer, "Max complexity.", 10)]\n'
                   '    public int Maximum { get; set; }\n}\n')
        self.commit()
        self.assertDetected()

    def test_central_rule_parameter_list_is_detected(self):
        """sonar-swift and sonar-dart list every parameter in one RulesDefinition."""
        path = 'src/main/java/com/sonarsource/dart/plugin/DartRulesDefinition.java'
        baseline = ('public class DartRulesDefinition {\n'
                    '  public static List<RuleParameter> parameters() {\n'
                    '    return List.of(\n'
                    '        new RuleParameter("S107", "max", "7", "Max params", INTEGER));\n'
                    '  }\n}\n')
        self.write(path, baseline)
        self.commit('baseline')
        self.tag_baseline()
        self.write(path, baseline.replace(
            '        new RuleParameter("S107", "max", "7", "Max params", INTEGER));',
            '        new RuleParameter("S107", "max", "7", "Max params", INTEGER),\n'
            '        new RuleParameter("S1192", "threshold", "3", "Duplicates", INTEGER));'))
        self.commit()
        self.assertDetected()

    def test_sonarjs_config_ts_new_field_is_detected(self):
        """
        SonarJS generates and gitignores its @RuleProperty classes, so config.ts is the only
        tracked declaration. Mirrors the real 13.2 -> 13.3 'propNamePattern' addition.
        """
        path = 'packages/analysis/src/jsts/rules/S6478/config.ts'
        baseline = ("import type { ESLintConfiguration } from '../helpers/configs.js';\n"
                    'export const fields = [\n'
                    '  [\n'
                    '    {\n'
                    "      field: 'allowAsProps',\n"
                    '      default: false,\n'
                    '    },\n'
                    '  ],\n'
                    '] as const satisfies ESLintConfiguration;\n')
        self.write(path, baseline)
        self.commit('baseline')
        self.tag_baseline()
        self.write(path, baseline.replace(
            '    },\n  ],\n',
            '    },\n'
            '    {\n'
            "      field: 'propNamePattern',\n"
            "      default: '{render*,*Enhancer}',\n"
            '    },\n  ],\n'))
        self.commit()
        self.assertDetected()

    def test_sonarjs_config_ts_unrelated_change_is_not_detected(self):
        path = 'packages/analysis/src/jsts/rules/S6478/config.ts'
        baseline = ("import type { ESLintConfiguration } from '../helpers/configs.js';\n"
                    'const ROLES = [];\n'
                    'export const fields = [\n'
                    '  [\n'
                    '    {\n'
                    "      field: 'allowAsProps',\n"
                    '      default: false,\n'
                    '    },\n'
                    '  ],\n'
                    '] as const satisfies ESLintConfiguration;\n')
        self.write(path, baseline)
        self.commit('baseline')
        self.tag_baseline()
        self.write(path, baseline.replace("const ROLES = [];", "const ROLES = ['listbox'];"))
        self.commit()
        self.assertNotDetected()

    def test_non_rule_file_is_ignored(self):
        """A .ts file outside a rules/<key>/config.ts path is not a declaration site."""
        path = 'packages/analysis/src/jsts/helpers/configs.ts'
        self.write(path, 'export const x = 1;\n')
        self.commit('baseline')
        self.tag_baseline()
        self.write(path, "export const x = 1;\nexport const field = 'format';\n")
        self.commit()
        self.assertNotDetected()


class TestTestSourceHandling(DetectorTestCase):
    def setUp(self):
        super().setUp()
        self.path = 'checks/src/test/java/org/sonar/python/checks/NamingCheckTest.java'
        self.write(self.path, 'class NamingCheckTest {\n}\n')
        self.commit('baseline')
        self.tag_baseline()
        self.write(self.path,
                   'class NamingCheckTest {\n'
                   '  @RuleProperty(key = "format", defaultValue = "x")\n'
                   '  String format;\n}\n')
        self.commit()

    def test_test_sources_excluded_by_default(self):
        self.assertFalse(self.run_detect(include_test_sources=False))

    def test_test_sources_included_on_request(self):
        self.assertTrue(self.run_detect(include_test_sources=True))


class TestBaseRefResolution(DetectorTestCase):
    def test_nearest_reachable_tag_is_used(self):
        self.write('a.txt', '1\n')
        self.commit('first')
        git(self.repo, 'tag', '1.0.0.100')
        self.write('a.txt', '2\n')
        self.commit('second')
        git(self.repo, 'tag', '1.1.0.200')
        self.write('a.txt', '3\n')
        self.commit('third')
        self.assertEqual(resolve_base_ref(str(self.repo), 'HEAD', ''), '1.1.0.200')

    def test_maintenance_branch_ignores_newer_unreachable_tag(self):
        """A newer tag on master must not become the baseline for a dot release."""
        self.write('a.txt', '1\n')
        self.commit('first')
        git(self.repo, 'tag', '1.0.0.100')
        git(self.repo, 'checkout', '-q', '-b', 'branch-1.0')
        self.write('a.txt', 'fix\n')
        self.commit('hotfix')
        git(self.repo, 'checkout', '-q', 'master')
        self.write('a.txt', 'next\n')
        self.commit('feature')
        git(self.repo, 'tag', '2.0.0.900')
        git(self.repo, 'checkout', '-q', 'branch-1.0')
        self.assertEqual(resolve_base_ref(str(self.repo), 'HEAD', ''), '1.0.0.100')

    def test_explicit_base_ref_wins(self):
        self.write('a.txt', '1\n')
        self.commit('first')
        git(self.repo, 'tag', '1.0.0.100')
        git(self.repo, 'tag', 'custom-baseline')
        self.assertEqual(
            resolve_base_ref(str(self.repo), 'HEAD', 'custom-baseline'), 'custom-baseline')

    def test_rerun_steps_back_past_the_release_tag(self):
        """
        On a re-run the release tag already points at HEAD. Comparing it against itself would
        report no changes, so the previous release must be used instead.
        """
        self.write('a.txt', '1\n')
        self.commit('first')
        git(self.repo, 'tag', '1.0.0.100')
        self.write('a.txt', '2\n')
        self.commit('release commit')
        git(self.repo, 'tag', '1.1.0.200')
        self.assertEqual(resolve_base_ref(str(self.repo), 'HEAD', ''), '1.0.0.100')

    def test_rerun_without_an_earlier_release_returns_none(self):
        self.write('a.txt', '1\n')
        self.commit('only commit')
        git(self.repo, 'tag', '1.0.0.100')
        self.assertIsNone(resolve_base_ref(str(self.repo), 'HEAD', ''))

    def test_rerun_detects_changes_against_the_previous_release(self):
        """End to end: the property change is still found when the release tag already exists."""
        path = 'checks/src/main/java/Check.java'
        self.write(path, JAVA_CHECK)
        self.commit('previous release')
        git(self.repo, 'tag', '1.0.0.100')
        self.write(path, JAVA_CHECK.replace('key = "format"', 'key = "pattern"'))
        self.commit('release commit')
        git(self.repo, 'tag', '1.1.0.200')

        base = resolve_base_ref(str(self.repo), 'HEAD', '')
        self.assertTrue(self.run_detect(base_ref=base))

    def test_no_tag_returns_none(self):
        self.write('a.txt', '1\n')
        self.commit('only commit')
        self.assertIsNone(resolve_base_ref(str(self.repo), 'HEAD', ''))

    def test_unresolvable_explicit_base_ref_exits(self):
        self.write('a.txt', '1\n')
        self.commit('only commit')
        with self.assertRaises(SystemExit) as ctx:
            resolve_base_ref(str(self.repo), 'HEAD', 'no-such-tag')
        self.assertEqual(ctx.exception.code, 1)


class TestExtraPatterns(unittest.TestCase):
    def test_parses_pathspec_and_regex(self):
        rules = parse_extra_patterns('*.scala::@RuleParam\\(')
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].pathspecs, ['*.scala'])
        self.assertTrue(rules[0].regex.search('  @RuleParam(key = "x")'))

    def test_ignores_blank_lines_and_comments(self):
        self.assertEqual(parse_extra_patterns('\n# a comment\n\n'), [])

    def test_rejects_line_without_separator(self):
        with self.assertRaises(SystemExit):
            parse_extra_patterns('*.scala@RuleParam')

    def test_rejects_empty_side(self):
        with self.assertRaises(SystemExit):
            parse_extra_patterns('*.scala::')

    def test_rejects_invalid_regex(self):
        with self.assertRaises(SystemExit):
            parse_extra_patterns('*.scala::([unclosed')


class TestExtraPatternsDetection(DetectorTestCase):
    def test_extra_pattern_detects_custom_convention(self):
        path = 'src/main/scala/Check.scala'
        self.write(path, 'class Check {\n  val max = 1\n}\n')
        self.commit('baseline')
        self.tag_baseline()
        self.write(path, 'class Check {\n  @RuleParam("max")\n  val max = 1\n}\n')
        self.commit()
        self.assertFalse(self.run_detect(), 'scala is not covered by the built-in ruleset')
        rules = RULESET + parse_extra_patterns(r'*.scala::@RuleParam\(')
        self.assertTrue(self.run_detect(rules=rules))


class TestPathspecMatching(unittest.TestCase):
    def test_star_spans_directories(self):
        self.assertTrue(pathspec_matches('a/b/c/Check.java', '*.java'))
        self.assertFalse(pathspec_matches('a/b/c/Check.kt', '*.java'))

    def test_nested_rules_config_matches_at_any_depth(self):
        self.assertTrue(pathspec_matches(
            'packages/analysis/src/jsts/rules/S100/config.ts', '*/rules/*/config.ts'))
        self.assertFalse(pathspec_matches(
            'packages/analysis/src/jsts/helpers/config.ts', '*/rules/*/config.ts'))

    def test_dot_is_literal(self):
        self.assertFalse(pathspec_matches('Checkxjava', '*.java'))


class TestHunkParsing(unittest.TestCase):
    def test_single_line_hunk_without_counts(self):
        diff = ['diff --git a/A.java b/A.java',
                '--- a/A.java',
                '+++ b/A.java',
                '@@ -1 +1 @@',
                '-old',
                '+new']
        self.assertEqual(list(iter_hunks(diff)), [('A.java', ['-old', '+new'])])

    def test_added_line_resembling_a_file_header_does_not_desync(self):
        """A body line rendering as '+++ x' must be consumed as content, not a new header."""
        diff = ['diff --git a/A.java b/A.java',
                '--- a/A.java',
                '+++ b/A.java',
                '@@ -1,1 +1,2 @@',
                ' context',
                '+++ not a header',
                'diff --git a/B.java b/B.java',
                '--- a/B.java',
                '+++ b/B.java',
                '@@ -1 +1 @@',
                '-x',
                '+y']
        hunks = list(iter_hunks(diff))
        self.assertEqual(hunks[0], ('A.java', [' context', '+++ not a header']))
        self.assertEqual(hunks[1], ('B.java', ['-x', '+y']))

    def test_no_newline_marker_is_not_counted(self):
        diff = ['+++ b/A.java',
                '@@ -1 +1 @@',
                '-old',
                '\\ No newline at end of file',
                '+new']
        (path, body), = list(iter_hunks(diff))
        self.assertEqual(path, 'A.java')
        self.assertIn('+new', body)

    def test_truncated_hunk_body_stops_cleanly(self):
        """A body shorter than its header claims must not run past the end of the diff."""
        diff = ['+++ b/A.java',
                '@@ -1,5 +1,5 @@',
                ' context',
                'garbage that is not a diff body line']
        (path, body), = list(iter_hunks(diff))
        self.assertEqual(path, 'A.java')
        self.assertEqual(body, [' context'])

    def test_deleted_file_target_is_skipped(self):
        diff = ['diff --git a/A.java b/A.java',
                '--- a/A.java',
                '+++ /dev/null',
                '@@ -1 +0,0 @@',
                '-@RuleProperty(key = "x")']
        self.assertEqual(list(iter_hunks(diff)), [])


class TestMatchingRules(unittest.TestCase):
    """Direct checks on the matcher, independent of git."""

    @staticmethod
    def diff(*body):
        return ['+++ b/Check.java', f'@@ -1,{len(body)} +1,{len(body)} @@', *body]

    def test_import_line_never_matches(self):
        matches = find_matches(
            self.diff('+import org.sonar.check.RuleProperty;'), RULESET)
        self.assertEqual(matches, [])

    def test_attribute_needs_a_declaration_in_the_hunk(self):
        without = find_matches(self.diff('+  description = "changed";'), RULESET)
        self.assertEqual(without, [], 'attribute alone must not match')

        with_marker = find_matches(
            self.diff(' @RuleProperty(', '+  description = "changed";', ' )'), RULESET)
        self.assertEqual(len(with_marker), 1)

    def test_file_with_no_applicable_rule_is_skipped(self):
        diff = ['+++ b/docs/notes.md',
                '@@ -1 +1 @@',
                '+@RuleProperty(key = "x")']
        self.assertEqual(find_matches(diff, RULESET), [])

    def test_context_line_alone_never_matches(self):
        self.assertEqual(find_matches(self.diff(' @RuleProperty(key = "x")'), RULESET), [])

    def test_attribute_regex_ignores_unrelated_assignment(self):
        self.assertIsNone(ATTRIBUTE_REGEX.search('String MESSAGE = "hello";'))
        self.assertIsNotNone(ATTRIBUTE_REGEX.search('defaultValue = "10"'))


class TestReportingAndOutput(unittest.TestCase):
    """The stdout contract action.yml redirects into $GITHUB_OUTPUT."""

    def capture(self, fn, *args):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = fn(*args)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_emit_prints_every_output_key(self):
        _, out, _ = self.capture(emit, True, '1.0.0.100', [('A.java', '+x')], ['A.java'])
        self.assertEqual(out.splitlines(), [
            'rule-props-changed=true',
            'base-ref=1.0.0.100',
            'match-count=1',
            'matched-files=A.java',
        ])

    def test_emit_false_when_nothing_changed(self):
        _, out, _ = self.capture(emit, False, '1.0.0.100', [], [])
        self.assertIn('rule-props-changed=false', out)
        self.assertIn('matched-files=', out)

    def test_emit_caps_the_file_list(self):
        files = [f'F{i}.java' for i in range(MAX_REPORTED_FILES + 5)]
        _, out, _ = self.capture(emit, True, 'tag', [], files)
        listed = [line for line in out.splitlines() if line.startswith('matched-files=')][0]
        self.assertEqual(len(listed[len('matched-files='):].split(',')), MAX_REPORTED_FILES)

    def test_report_deduplicates_files_and_keeps_order(self):
        matches = [('B.java', '+b1'), ('A.java', '+a'), ('B.java', '+b2')]
        files, _, err = self.capture(report, matches, '1.0.0.100')
        self.assertEqual(files, ['B.java', 'A.java'])
        self.assertIn('3 rule property change(s) across 2 file(s)', err)

    def test_report_announces_a_clean_result(self):
        files, _, err = self.capture(report, [], '1.0.0.100')
        self.assertEqual(files, [])
        self.assertIn('No rule property changes', err)

    def test_report_truncates_long_file_lists(self):
        matches = [(f'F{i}.java', '+x') for i in range(MAX_REPORTED_FILES + 3)]
        _, _, err = self.capture(report, matches, 'tag')
        self.assertIn('and 3 more file(s)', err)


class TestMainCli(DetectorTestCase):
    """End-to-end through main(), the entry point action.yml calls."""

    def run_main(self, *extra_args):
        argv = ['detect_rule_props_changed.py', '--repo', str(self.repo), *extra_args]
        stdout, stderr = StringIO(), StringIO()
        with patch.object(sys, 'argv', argv), redirect_stdout(stdout), redirect_stderr(stderr):
            main()
        outputs = dict(line.split('=', 1) for line in stdout.getvalue().strip().splitlines())
        return outputs, stderr.getvalue()

    def test_reports_true_for_a_real_property_change(self):
        path = 'checks/src/main/java/Check.java'
        self.write(path, JAVA_CHECK)
        self.commit('baseline')
        self.tag_baseline()
        self.write(path, JAVA_CHECK.replace('key = "format"', 'key = "pattern"'))
        self.commit()

        outputs, err = self.run_main()
        self.assertEqual(outputs['rule-props-changed'], 'true')
        self.assertEqual(outputs['base-ref'], BASELINE_TAG)
        self.assertEqual(outputs['matched-files'], path)
        self.assertIn('rule property change(s)', err)

    def test_reports_false_and_warns_without_a_baseline_tag(self):
        self.write('a.txt', '1\n')
        self.commit('only commit')

        outputs, err = self.run_main()
        self.assertEqual(outputs['rule-props-changed'], 'false')
        self.assertEqual(outputs['base-ref'], '')
        self.assertEqual(outputs['match-count'], '0')
        self.assertIn('::warning::', err)

    def test_include_test_sources_flag_is_honoured(self):
        path = 'checks/src/test/java/CheckTest.java'
        self.write(path, 'class CheckTest {}\n')
        self.commit('baseline')
        self.tag_baseline()
        self.write(path, 'class CheckTest {\n  @RuleProperty(key = "x")\n  String x;\n}\n')
        self.commit()

        self.assertEqual(self.run_main()[0]['rule-props-changed'], 'false')
        outputs, _ = self.run_main('--include-test-sources', 'true')
        self.assertEqual(outputs['rule-props-changed'], 'true')

    def test_bad_diff_range_exits_with_an_error_annotation(self):
        self.write('a.txt', '1\n')
        self.commit('only commit')
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as ctx:
            detect(str(self.repo), 'no-such-ref', 'HEAD', RULESET, False)
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn('::error::', stderr.getvalue())


class TestRuleset(unittest.TestCase):
    def test_every_builtin_rule_has_a_valid_pathspec_and_name(self):
        for rule in RULESET:
            self.assertIsInstance(rule, DetectionRule)
            self.assertTrue(rule.name)
            self.assertTrue(rule.pathspecs)

    def test_annotation_rule_requires_the_at_sign(self):
        """`import ...RuleProperty;` must not satisfy the declaration regex."""
        annotation = next(r for r in RULESET if r.name == 'annotation')
        self.assertIsNone(annotation.regex.search('import org.sonar.check.RuleProperty;'))
        self.assertIsNotNone(annotation.regex.search('  @RuleProperty(key = "x")'))


if __name__ == '__main__':
    unittest.main()
