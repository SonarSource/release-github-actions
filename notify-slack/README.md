# Notify Slack on Failure Action

This GitHub Action sends a Slack notification summarizing failed jobs in a workflow run when used with an `if: failure()` condition.

## Description

The action posts a concise message to a Slack channel containing:
1. A link to the failed GitHub Actions run
2. A list of failed jobs provided by the workflow
3. A custom project-branded username and icon

It is intended to be used as the last step (or in a dedicated job) guarded by `if: failure()` so that it only triggers on failures.

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) to retrieve the Slack token from Vault
- [rtCamp/action-slack-notify](https://github.com/rtCamp/action-slack-notify) to send the Slack message

## Inputs

| Input           | Description                                                            | Required | Default   |
|-----------------|------------------------------------------------------------------------|----------|-----------|
| `project-name`  | The display name of the project; used in the Slack username.           | Yes      | -         |
| `icon`          | Emoji icon for the Slack message (Slack emoji code).                   | No       | `:alert:` |
| `slack-channel` | Slack channel (without `#`) to post the notification into.             | Yes      | -         |
| `jobs`          | Comma-separated list of job names to report as failed (provided by you). | Yes    | -         |

Note: The list of failed jobs must be provided via the `jobs` input by your workflow logic.

## Outputs

No outputs are produced by this action.

## Usage

### Basic usage (in a dedicated failure notification job)

```yaml
jobs:
  notify_on_failure:
    needs: [ build, test, deploy ]  # Example job dependencies
    runs-on: ubuntu-latest
    if: failure()
    permissions:
      statuses: read
      id-token: write
    steps:
      - uses: SonarSource/release-github-actions/notify-slack@v1
        with:
          project-name: 'My Project'
          slack-channel: 'engineering-alerts'
          jobs: ${{ toJSON(needs) }}
```

### Minimal usage (only required inputs)

```yaml
- uses: SonarSource/release-github-actions/notify-slack@v1
  if: failure()
  with:
    project-name: 'My Project'
    slack-channel: 'engineering-alerts'
    jobs: 'build, test'
```

### Custom icon

```yaml
- uses: SonarSource/release-github-actions/notify-slack@v1
  if: failure()
  with:
    project-name: 'My Project'
    slack-channel: 'engineering-alerts'
    icon: ':rocket:'
    jobs: 'build, test'
```

## Implementation Details

The action is a composite action that:
- Fetches `SLACK_TOKEN` from Vault path `development/kv/data/slack` using `vault-action-wrapper`
- Uses a workflow-provided `jobs` input (comma-separated string) to populate the "Failed Jobs" section
- Constructs a Slack message with run URL and the provided failed jobs list
- Uses `rtCamp/action-slack-notify` to send a minimal styled message (no title/footer) with danger color
- Sets Slack username to: `<project-name> CI Notifier`
- If the `jobs` list is empty or not provided, the "Failed Jobs" line will be blank

## Prerequisites

- Vault policy granting access to `development/kv/data/slack` must be configured for the repository.
- The secret at that path must contain a key named `token`.
- The Slack channel provided must exist and the token must have permission to post there.

## Notes

- Use `if: failure()` on the step or job; otherwise it will also fire on success.
- `project-name`, `slack-channel`, and `jobs` are required inputs (no defaults).
- Do not prefix the channel with `#`.
- Message formatting is intentionally minimal for quick triage in alert-focused channels.
- How you compute the failed jobs list is up to your workflow; you can use prior steps to gather job results and pass them to this action via `jobs`.
