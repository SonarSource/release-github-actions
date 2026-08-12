# Detect Rule Property Changes

Detects whether any **rule property** (rule parameter) declaration changed between the previous
release and the commit being released.

The result feeds the *Rule Properties Changed* field (`customfield_11263`) on the Jira release
ticket — see SC-4654. That field used to be answered by hand through the `rule-props-changed`
workflow input; this action computes it instead.

## How it works

1. Resolves a baseline: the nearest tag reachable from the release commit
   (`git describe --tags --abbrev=0`). Reachability matters — on a maintenance branch the newest
   tag in the repository is usually *not* an ancestor, and comparing against it would be wrong.
   If that tag turns out to point at the release commit itself — which happens when a release is
   re-run after its tag was created — the action steps back to the release before it, rather than
   comparing the commit with itself and reporting no changes.
2. Runs `git diff -U3 <baseline>..<head>` restricted to files that can declare rule properties.
3. Flags a changed line when it is not an `import`/`using` line **and** either
   - declares a rule property itself, or
   - edits a declaration attribute (`key`, `defaultValue`, `description`, `type`, `paramKey`)
     inside a hunk that shows the declaration.

## Fail-safe: "cannot tell" means "changed"

If the comparison cannot be made, the action reports `rule-props-changed=true` — never `false` —
and sets `detection-status=assumed-changed`.

The two wrong answers are not equally costly. A rule property change that reaches SQC
unannounced is a production surprise; a spurious `Yes` on the release ticket costs one manual
check. So every path that cannot produce an answer resolves to `true`:

| Situation | Annotation |
|---|---|
| No release tag reachable from the release commit (first release) | `::warning::` |
| The release tag points at the release commit and no earlier tag is reachable | `::warning::` |
| Shallow checkout — the previous release and its history may be missing | `::warning::` |
| `base-ref` or `head-ref` cannot be resolved | `::error::` |
| Malformed `extra-patterns` — a requested convention is not being scanned | `::error::` |
| `git diff` fails, git cannot be run, or the detector hits an unforeseen bug | `::error::` |

The script **never exits non-zero**, deliberately. A non-zero exit writes no outputs at all, and
an absent output reads downstream as "not changed" — exactly the answer the fallback exists to
prevent. `action.yml` wraps the call as well, so a detector that cannot start at all still
produces the safe outputs, and `automated-release.yml` treats anything other than an explicit
`false` as `Yes`.

## Conventions recognised

Analyzers do not declare rule properties the same way, so the action carries one rule per
convention:

| Pattern                                    | Files                  | Analyzers |
|--------------------------------------------|------------------------|-----------|
| `@RuleProperty(`                            | `*.java`, `*.kt`       | sonar-python, sonar-java, sonar-go, sonar-iac, sonar-kotlin, … |
| `new RuleParameter(`                        | `*.java`, `*.kt`       | sonar-swift, sonar-dart (central `*RulesDefinition.java`) |
| `[RuleParameter(`                           | `*.cs`                 | sonar-dotnet-enterprise |
| `field:` / `default:` / `displayName:`      | `*/rules/*/config.ts`  | SonarJS |

SonarJS is the reason the TypeScript rule exists: its `@RuleProperty` Java classes are generated
and **gitignored**, so they never appear in a diff. The tracked declaration is the `config.ts`
the classes are generated from.

Anything not covered can be added per repository through `extra-patterns`.

## Why not just grep the diff for `RuleProperty`?

Because `import org.sonar.check.RuleProperty;` shows up as diff *context* whenever an unrelated
import is added to a check class. Replaying a plain grep over 35 real release-tag pairs across
sonar-python, sonar-go, sonar-iac, sonar-java and SonarJS produced 8 false-positive files. The
changed-line matcher above reports the same history with no false positives.

## Inputs

| Input                  | Description                                                                                                   | Required | Default  |
|------------------------|---------------------------------------------------------------------------------------------------------------|----------|----------|
| `branch`               | The branch being released, used as the checkout ref                                                            | No       | `master` |
| `base-ref`             | Ref to compare against. Defaults to the nearest tag reachable from the release commit                          | No       | -        |
| `head-ref`             | The commit being released                                                                                      | No       | `HEAD`   |
| `extra-patterns`       | Extra detection rules, one `<pathspec>::<regex>` per line, appended to the built-in ruleset                    | No       | -        |
| `include-test-sources` | Scan test sources too. Excluded by default, since changing a test fixture is not a released behaviour change   | No       | `false`  |

## Outputs

| Output               | Description                                                                                     |
|----------------------|---------------------------------------------------------------------------------------------------|
| `rule-props-changed` | `"true"` when a rule property declaration changed **or the comparison was impossible**, `"false"` otherwise |
| `base-ref`           | The baseline actually compared against; empty when no comparison was made                          |
| `match-count`        | Number of changed lines that altered a declaration                                                 |
| `matched-files`      | Comma-separated files containing the changes (capped at 20)                                        |
| `detection-status`   | `"detected"` when the diff was compared, `"assumed-changed"` when the fallback fired                |

Read `detection-status` when you need to tell a detected change from an assumed one — with the
fallback, `rule-props-changed=true` alone does not mean anything was found.

## Usage

```yaml
- name: Detect Rule Property Changes
  id: detect-rule-props
  uses: SonarSource/release-github-actions/detect-rule-props-changed@v1
  with:
    branch: master

- name: Use the result
  run: echo "Rule properties changed: ${{ steps.detect-rule-props.outputs.rule-props-changed }}"
```

With an extra convention for an analyzer the built-in ruleset does not cover:

```yaml
- uses: SonarSource/release-github-actions/detect-rule-props-changed@v1
  with:
    extra-patterns: |
      *.scala::@RuleParam\(
      */rules/*/params.yaml::^\s*name:
```

The action checks out the repository itself with `fetch-depth: 0`, because the tags and the
history back to the previous release must be present.

## Limitations

- **Defaults held in distant constants.** A declaration such as
  `defaultValue = "" + DEFAULT_THRESHOLD` is detected when the declaration block changes, but not
  when only the far-away `DEFAULT_THRESHOLD` constant does.
- **Description-only edits in `config.ts`** are not flagged, since rewording help text does not
  change a rule's parameters.
- The `matched-files` output is capped at 20 entries; `match-count` always reports the true total.

## Testing

```bash
cd detect-rule-props-changed
pip install pytest pytest-cov
python -m pytest test_detect_rule_props_changed.py -v \
  --cov=detect_rule_props_changed --cov-report=term-missing
```

The tests build throwaway git repositories and run the detector end to end, so real `git diff`
output is exercised — including the import-context false positive taken from sonar-python history
and every fallback path, each asserting that the answer is `true` and that the process still
exits 0.
