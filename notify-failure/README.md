# Notify Failure Action

This GitHub Action sends a rich Slack failure notification automatically assembled from GitHub context and the GitHub API — no message-building boilerplate required.

## Description

When a CI job fails, this action fetches relevant context (commit info, job logs) from the GitHub API and posts a structured Slack message containing:

- Repository, branch, and workflow name
- Failed job names
- Run attempt number (shows when a job has been retried)
- Last commit author and commit message
- Root cause: first meaningful error line extracted from the failed job logs
- Develocity build scan link (if present in the logs)
- Links to view the run and re-run failed jobs

All sections are included by default. Individual sections can be excluded via inputs.

## Dependencies

- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) to retrieve the Slack token from Vault
- GitHub token (`github.token`) for reading commit info and job logs via the GitHub API

## Example Slack Output

```
🚨 CI Failure — SonarSource/sonar-php

Workflow: Java CI  •  Branch: `main`  •  Attempt: 2
Triggered by: janedoe
PR: #42 Fix authentication bug
Failed Jobs: qa_plugin (step: Run unit tests), build

🚨 Flaky: This workflow has failed 3 consecutive times on this branch

🔬 Root Cause: error: method analyze(UCFG) is not public
🧪 Test Failures: 3 failures, 1 error (across 42 tests)
📊 Build Scan: View Develocity Scan

🔍 View Run & Re-run Failed Jobs
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `project-name` | The display name of the project; used in the Slack username. | Yes | - |
| `slack-channel` | Slack channel to post to (without `#`). | Yes | - |
| `needs` | The `toJSON(needs)` object from the caller workflow, used to identify which jobs failed. | Yes | - |
| `github-token` | GitHub token for API calls (read commits and job logs). | No | `${{ github.token }}` |
| `include-pr-info` | Include PR title and link when the run is associated with a pull request. | No | `true` |
| `include-failed-step` | Include the name of the failed step within each failed job. | No | `true` |
| `include-test-counts` | Include failed test counts parsed from Maven surefire output in job logs. | No | `true` |
| `include-flakiness` | Include a flakiness indicator when the workflow has failed consecutively on this branch. | No | `true` |
| `include-root-cause` | Include a root cause line extracted from failed job logs. | No | `true` |
| `include-develocity` | Include a Develocity build scan link if found in the logs. | No | `true` |
| `include-run-attempt` | Include the run attempt number. | No | `true` |

## Outputs

No outputs are produced by this action.

## Usage

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: ./gradlew build

  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - run: ./gradlew test

  notify_on_failure:
    needs: [build, test]
    runs-on: ubuntu-latest
    if: failure()
    permissions:
      id-token: write
      actions: read   # needed to read job logs
    steps:
      - uses: SonarSource/release-github-actions/notify-failure@v1
        with:
          project-name: 'My Project'
          slack-channel: 'squad-alerts'
          needs: ${{ toJSON(needs) }}
```

### Excluding sections

```yaml
- uses: SonarSource/release-github-actions/notify-failure@v1
  with:
    project-name: 'My Project'
    slack-channel: 'squad-alerts'
    needs: ${{ toJSON(needs) }}
    include-develocity: 'false'
    include-run-attempt: 'false'
```

## Prerequisites

- Vault policy granting access to `development/kv/data/slack` must be configured for the repository.
- The job must have `id-token: write` permission (for Vault) and `actions: read` permission (for reading job logs via the GitHub API).

## Notes

- Root cause extraction uses heuristics (javac error lines, Maven `BUILD FAILURE`, `Exception in thread`, etc.) and may not always find the most relevant line. It is best-effort.
- Develocity scan links are extracted by regex from job logs. If a project does not use Develocity, the section is simply omitted.
- When `github.token` is used (the default), it has read access to the repository's actions data. No additional token configuration is needed for most public or internal repositories.
