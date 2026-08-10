#!/usr/bin/env python3
"""
Detect whether any rule property (a.k.a. rule parameter) declaration changed between the
previous release and the commit being released.

The result feeds the "Rule Properties Changed" field (customfield_11263) on the Jira REL
ticket, which used to be answered by hand via the `rule-props-changed` workflow input.

Analyzers do not agree on how rule properties are declared, so the detector carries one
rule per convention (see RULESET below). Notably, SonarJS generates its `@RuleProperty`
Java classes and gitignores them, so the only declaration that ever shows up in a diff is
the TypeScript `config.ts` those classes are generated from.

Matching deliberately looks at *changed* lines rather than grepping the whole diff: the
`import org.sonar.check.RuleProperty;` line appears as diff context whenever an unrelated
import is added to a check class, and grepping that produces frequent false positives.
"""

import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))
from jira_common import eprint  # noqa: E402


class DetectionRule:
    """A file selector plus the regex identifying a rule-property declaration in it."""

    def __init__(self, name, pathspecs, pattern):
        self.name = name
        self.pathspecs = pathspecs
        self.regex = re.compile(pattern)

    def matches_file(self, path):
        return any(pathspec_matches(path, spec) for spec in self.pathspecs)


# One entry per declaration convention found across the analyzers.
RULESET = [
    # sonar-python, sonar-java, sonar-go, sonar-iac, sonar-kotlin, ...
    DetectionRule('annotation', ['*.java', '*.kt'], r'@RuleProperty\s*\('),
    # sonar-swift, sonar-dart: parameters listed centrally in a *RulesDefinition.java
    DetectionRule('rule-parameter-ctor', ['*.java', '*.kt'], r'\bnew\s+RuleParameter\s*\('),
    # sonar-dotnet-enterprise
    DetectionRule('csharp-attribute', ['*.cs'], r'\[\s*RuleParameter\s*\('),
    # SonarJS: ESLintConfiguration fields; the generated Java equivalents are gitignored
    DetectionRule('eslint-config', ['*/rules/*/config.ts'],
                  r'^\s*(field|default|displayName)\s*:'),
]

# An attribute of a declaration, e.g. `defaultValue = "10"`. Only counted inside a hunk that
# also shows the declaration itself, so an unrelated `MESSAGE = "..."` nearby cannot trigger it.
ATTRIBUTE_REGEX = re.compile(r'\b(key|defaultValue|description|type|paramKey)\s*=')

# Import lines never constitute a rule-property change, even though they name the symbol.
IMPORT_REGEX = re.compile(r'^\s*(import|using|from)\b')

# Test sources declare rule properties too, but changing them is not a released behaviour change.
TEST_EXCLUDE_PATHSPECS = [
    ':(exclude)*/src/test/*',
    ':(exclude)*/src/integrationTest/*',
    ':(exclude)*/its/*',
    ':(exclude)*Test.java',
    ':(exclude)*Test.kt',
    ':(exclude)*Test.cs',
    ':(exclude)*Tests.cs',
]

HUNK_HEADER_REGEX = re.compile(r'^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@')

MAX_REPORTED_FILES = 20


def pathspec_matches(path, spec):
    """
    Match a git pathspec glob against a repository-relative path.

    Unlike fnmatch, `*` here also spans `/`, so `*.java` matches a nested file and
    `*/rules/*/config.ts` matches at any depth -- the semantics git itself applies.
    """
    regex = '^' + '.*'.join(re.escape(part) for part in spec.split('*')) + '$'
    return re.match(regex, path) is not None


def run_git(args, cwd):
    result = subprocess.run(['git'] + args, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def commit_of(repo, ref):
    code, out, _ = run_git(['rev-parse', '--verify', f'{ref}^{{commit}}'], repo)
    return out.strip() if code == 0 else None


def resolve_base_ref(repo, head_ref, explicit_base):
    """
    Return the ref to diff against, or None when the repository has no prior release.

    Without an explicit base we take the nearest tag reachable from HEAD, which stays
    correct on maintenance branches where the newest tag overall is not an ancestor.
    """
    if explicit_base:
        if commit_of(repo, explicit_base) is None:
            eprint(f"::error::base-ref '{explicit_base}' cannot be resolved.")
            sys.exit(1)
        return explicit_base

    code, out, _ = run_git(['describe', '--tags', '--abbrev=0', head_ref], repo)
    if code != 0 or not out.strip():
        return None
    tag = out.strip()

    # On a re-run the release tag already exists and points at the commit being released.
    # Comparing it with itself would report no changes, so step back one release.
    if commit_of(repo, tag) == commit_of(repo, head_ref):
        eprint(f"Tag {tag} already points at the release commit (re-run?); "
               f"stepping back to the release before it.")
        code, out, _ = run_git(['describe', '--tags', '--abbrev=0', f'{tag}^'], repo)
        if code != 0 or not out.strip():
            return None
        return out.strip()

    return tag


def parse_extra_patterns(raw):
    """Parse `<pathspec>::<regex>` lines into additional detection rules."""
    rules = []
    for lineno, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '::' not in line:
            eprint(f"::error::extra-patterns line {lineno} is not '<pathspec>::<regex>': {line}")
            sys.exit(1)
        pathspec, pattern = (part.strip() for part in line.split('::', 1))
        if not pathspec or not pattern:
            eprint(f"::error::extra-patterns line {lineno} has an empty pathspec or regex: {line}")
            sys.exit(1)
        try:
            rules.append(DetectionRule(f'extra:{pathspec}', [pathspec], pattern))
        except re.error as exc:
            eprint(f"::error::extra-patterns line {lineno} has an invalid regex: {exc}")
            sys.exit(1)
    return rules


def collect_pathspecs(rules, include_test_sources):
    pathspecs = []
    for rule in rules:
        for spec in rule.pathspecs:
            if spec not in pathspecs:
                pathspecs.append(spec)
    if not include_test_sources:
        pathspecs += TEST_EXCLUDE_PATHSPECS
    return pathspecs


def iter_hunks(diff_lines):
    """
    Yield (path, hunk_lines) for every hunk in a unified diff.

    Hunk bodies are consumed using the line counts in the `@@` header rather than by
    looking for the next marker, so added content that itself looks like a diff header
    (`+++ foo`) cannot desynchronise the parse.
    """
    current_file = None
    index, total = 0, len(diff_lines)

    while index < total:
        line = diff_lines[index]

        if line.startswith('diff --git '):
            current_file = None
            index += 1
            continue

        if line.startswith('+++ '):
            path = line[4:].strip()
            if path == '/dev/null':
                current_file = None
            else:
                current_file = path[2:] if path.startswith('b/') else path
            index += 1
            continue

        header = HUNK_HEADER_REGEX.match(line)
        if not header:
            index += 1
            continue

        remaining_old = int(header.group(1)) if header.group(1) is not None else 1
        remaining_new = int(header.group(2)) if header.group(2) is not None else 1
        body = []
        index += 1

        while index < total and (remaining_old > 0 or remaining_new > 0):
            body_line = diff_lines[index]
            sign = body_line[:1]
            if sign == '+':
                remaining_new -= 1
            elif sign == '-':
                remaining_old -= 1
            elif sign == ' ' or body_line == '':
                remaining_old -= 1
                remaining_new -= 1
            elif sign == '\\':  # "\ No newline at end of file"
                pass
            else:
                break
            body.append(body_line)
            index += 1

        if current_file:
            yield current_file, body


def find_matches(diff_lines, rules):
    """
    Return [(path, changed_line)] for every changed line that alters a rule property.

    A line counts when it is not an import and either declares a rule property itself, or
    edits a declaration attribute within a hunk that shows the declaration.
    """
    matches = []
    for path, hunk in iter_hunks(diff_lines):
        applicable = [rule for rule in rules if rule.matches_file(path)]
        if not applicable:
            continue

        texts = [line[1:] if line[:1] in ' +-' else line for line in hunk]
        has_marker = any(rule.regex.search(text) for text in texts for rule in applicable)

        for line, text in zip(hunk, texts):
            if line[:1] not in '+-' or IMPORT_REGEX.match(text):
                continue
            declares = any(rule.regex.search(text) for rule in applicable)
            if declares or (has_marker and ATTRIBUTE_REGEX.search(text)):
                matches.append((path, line.rstrip()))
    return matches


def detect(repo, base_ref, head_ref, rules, include_test_sources):
    pathspecs = collect_pathspecs(rules, include_test_sources)
    code, out, err = run_git(
        ['diff', '-U3', f'{base_ref}..{head_ref}', '--'] + pathspecs, repo)
    if code != 0:
        eprint(f"::error::git diff {base_ref}..{head_ref} failed: {err.strip()}")
        sys.exit(1)
    return find_matches(out.splitlines(), rules)


def report(matches, base_ref):
    """Log a human-readable breakdown to stderr and return the affected files, in order."""
    files = []
    for path, _ in matches:
        if path not in files:
            files.append(path)

    if not matches:
        eprint(f"✅ No rule property changes found between {base_ref} and the release commit.")
        return files

    eprint(f"🔎 Found {len(matches)} rule property change(s) across {len(files)} file(s) "
           f"since {base_ref}:")
    for path in files[:MAX_REPORTED_FILES]:
        eprint(f"  {path}")
        for match_path, line in matches:
            if match_path == path:
                eprint(f"    {line}")
    if len(files) > MAX_REPORTED_FILES:
        eprint(f"  ... and {len(files) - MAX_REPORTED_FILES} more file(s)")
    return files


def emit(rule_props_changed, base_ref, matches, files):
    print(f"rule-props-changed={'true' if rule_props_changed else 'false'}")
    print(f"base-ref={base_ref}")
    print(f"match-count={len(matches)}")
    print(f"matched-files={','.join(files[:MAX_REPORTED_FILES])}")


def main():
    parser = argparse.ArgumentParser(
        description='Detect rule property changes between the previous release and HEAD.')
    parser.add_argument('--repo', default='.', help='Path to the git repository.')
    parser.add_argument('--base-ref', default='',
                        help='Baseline ref. Defaults to the nearest tag reachable from HEAD.')
    parser.add_argument('--head-ref', default='HEAD', help='The commit being released.')
    parser.add_argument('--extra-patterns', default='',
                        help="Newline-separated '<pathspec>::<regex>' detection rules.")
    parser.add_argument('--include-test-sources', default='false',
                        help='Set to "true" to scan test sources as well.')
    args = parser.parse_args()

    include_test_sources = args.include_test_sources.strip().lower() == 'true'
    rules = RULESET + parse_extra_patterns(args.extra_patterns)

    base_ref = resolve_base_ref(args.repo, args.head_ref, args.base_ref.strip())
    if base_ref is None:
        eprint('::warning::No release tag reachable from HEAD, so there is no baseline to '
               'diff against. Reporting no rule property changes.')
        emit(False, '', [], [])
        return

    eprint(f"Comparing {base_ref}..{args.head_ref} for rule property changes "
           f"(test sources {'included' if include_test_sources else 'excluded'}).")

    matches = detect(args.repo, base_ref, args.head_ref, rules, include_test_sources)
    files = report(matches, base_ref)
    emit(bool(matches), base_ref, matches, files)


if __name__ == '__main__':
    main()
