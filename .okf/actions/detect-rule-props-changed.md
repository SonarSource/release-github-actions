---
type: GitHub Action
title: Detect Rule Property Changes
description: Diffs the previous release tag against the release commit to decide whether any rule property declaration changed.
resource: https://github.com/SonarSource/release-github-actions/tree/master/detect-rule-props-changed
tags: [action, release, rule-properties, jira]
timestamp: 2026-08-10T00:00:00Z
---

# Overview

Computes the *Rule Properties Changed* field (`customfield_11263`, SC-4654) that
[create-jira-release-ticket](/actions/create-jira-release-ticket.md) writes onto the REL ticket.
Before this action the value came from the hand-answered `rule-props-changed` input on
[automated-release](/workflows/automated-release.md), which 42 caller repositories passed by hand
and almost always hardcoded to `false`. That input is now a deprecated no-op — see
[input sprawl](/risks/input-sprawl.md).

Called from the `prepare-release` job, which exposes the result as the `rule-props-changed`,
`rule-props-base-ref` and `rule-props-matched-files` job outputs.

# Fail-safe

The answer is asymmetric: an undetected rule property change reaching SQC is a production
surprise, an unnecessary "Yes" is one manual check. So **every path that cannot produce an answer
resolves to `true`** — no reachable tag, a shallow checkout, an unresolvable ref, malformed
`extra-patterns`, a failing `git diff`, or an unforeseen exception.

The fallback is enforced at three levels, because each one covers a hole the level below cannot:

1. **Script** — never exits non-zero. A non-zero exit writes no outputs at all, and an absent
   output reads downstream as "unchanged" — precisely the failure the fallback exists to prevent.
   Output values are collapsed to a single line: `$GITHUB_OUTPUT` is one `key=value` per line, so
   a newline inside a git error message could otherwise inject `rule-props-changed=false`.
2. **`action.yml`** — wraps the interpreter call, so a detector that cannot start (broken
   interpreter, unreadable script) still writes the safe outputs.
3. **[automated-release](/workflows/automated-release.md)** — the detect step is
   `continue-on-error`, and the ticket expression is `== 'false' && 'No' || 'Yes'`, so a failed
   or skipped step yields an empty output that maps to `Yes` rather than `No`.

# Detection

Baseline is the nearest tag **reachable from** the release commit
(`git describe --tags --abbrev=0`). Reachability is what makes maintenance-branch releases
correct: the newest tag in the repository is usually not an ancestor of a dot release. If that tag
points at the release commit itself (a re-run, after the tag was created) the action steps back
one release rather than comparing the commit with itself. The action checks out with
`fetch-depth: 0` so tags and history are present.

Analyzers do not share one convention, so the ruleset carries one entry per convention:

| Pattern | Files | Analyzers |
|---|---|---|
| `@RuleProperty(` | `*.java`, `*.kt` | sonar-python, sonar-java, sonar-go, sonar-iac, sonar-kotlin |
| `new RuleParameter(` | `*.java`, `*.kt` | sonar-swift, sonar-dart (central `*RulesDefinition.java`) |
| `[RuleParameter(` | `*.cs` | sonar-dotnet-enterprise |
| `field:` / `default:` / `displayName:` | `*/rules/*/config.ts` | SonarJS |

**SonarJS is why the TypeScript entry exists**: its `@RuleProperty` Java classes are generated and
gitignored (`sonar-plugin/javascript-checks/src/main/java/.../.gitignore` ignores `S*.java`), so
they never appear in a diff. The tracked declaration is the `config.ts` they are generated from.

Matching runs on **changed lines**, not the whole diff. A line counts when it is not an
`import`/`using` line and either declares a rule property, or edits a declaration attribute
(`key`, `defaultValue`, `description`, `type`, `paramKey`) inside a hunk that shows the
declaration. Grepping the raw diff instead produces frequent false positives, because
`import org.sonar.check.RuleProperty;` appears as *context* whenever an unrelated import is added
to a check class — replaying a plain grep over 35 real release-tag pairs surfaced 8 such files,
which the changed-line matcher reports cleanly.

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `branch` | Branch being released, used as the checkout ref | No | `master` |
| `base-ref` | Ref to compare against | No | nearest reachable tag |
| `head-ref` | Commit being released | No | `HEAD` |
| `extra-patterns` | Extra `<pathspec>::<regex>` rules, one per line | No | - |
| `include-test-sources` | Scan test sources too | No | `false` |

| Output | Description |
|---|---|
| `rule-props-changed` | `"true"` / `"false"`; `"true"` also when no comparison was possible |
| `base-ref` | Baseline compared against; empty when no comparison was made |
| `match-count` | Number of changed lines that altered a declaration |
| `matched-files` | Comma-separated files, capped at 20 |
| `detection-status` | `"detected"` / `"assumed-changed"` |

# Notes

- A default held in a distant constant (`defaultValue = "" + DEFAULT_THRESHOLD`) is only detected
  when the declaration block itself changes.
- Test sources are excluded by default: changing a test fixture is not a released behaviour change.
- `rule-props-changed=true` with `match-count=0` is the fallback, not a contradiction — read
  `detection-status` to tell the two apart.

# Citations

[1] [detect-rule-props-changed/README.md](/../detect-rule-props-changed/README.md)
