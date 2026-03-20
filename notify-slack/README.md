# Notify Slack Action

This GitHub Action sends a Slack notification. It supports two modes:
- **Failure mode** (default): summarizes failed jobs in a workflow run, intended for use with `if: failure()`.
- **Custom message mode**: sends a free-text message directly, useful for informational notifications such as PR creation alerts.

## Description

The action posts a message to a Slack channel containing either:
- A link to the failed GitHub Actions run and a list of failed jobs (failure mode), or
- A custom message provided by the caller (custom message mode).

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) to retrieve the Slack token from Vault
- [rtCamp/action-slack-notify](https://github.com/rtCamp/action-slack-notify) to send the Slack message

## Inputs

| Input           | Description                                                                                            | Required | Default   |
|-----------------|--------------------------------------------------------------------------------------------------------|----------|-----------|
| `project-name`  | The display name of the project; used in the Slack username.                                           | Yes      | -         |
| `icon`          | Emoji icon for the Slack message (Slack emoji code).                                                   | No       | `:alert:` |
| `slack-channel` | Slack channel (without `#`) to post the notification into.                                             | Yes      | -         |
| `jobs`          | A GitHub needs-like object string of jobs and their results (e.g., from `toJSON(needs)`). Required when `message` is not set. | No | - |
| `message`       | A custom free-text Slack message. When provided, skips job-failure parsing and sends this message directly. | No  | -         |
| `color`         | Slack attachment color (`good`, `danger`, `warning`, or a hex code).                                   | No       | `danger`  |

## Outputs

No outputs are produced by this action.

## Usage

### Failure notification (in a dedicated failure notification job)

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

### Custom message (e.g. PR ready for review)

```yaml
- uses: SonarSource/release-github-actions/notify-slack@v1
  with:
    project-name: 'My Project'
    slack-channel: 'team-channel'
    icon: ':memo:'
    color: good
    message: |
      *my-repo* rule metadata PR is ready for review:
      https://github.com/org/my-repo/pull/42
```

### Custom icon (failure mode)

```yaml
- uses: SonarSource/release-github-actions/notify-slack@v1
  if: failure()
  with:
    project-name: 'My Project'
    slack-channel: 'engineering-alerts'
    icon: ':rocket:'
    jobs: ${{ toJSON(needs) }}
```

## Implementation Details

The action is a composite action that:
- Fetches `SLACK_TOKEN` from Vault path `development/kv/data/slack` using `vault-action-wrapper`
- When `message` is not set: parses the `jobs` JSON input to extract failed job names and constructs a message with the run URL
- When `message` is set: sends the provided message directly, skipping job-failure parsing
- Uses `rtCamp/action-slack-notify` to send a minimal styled message (no title/footer)
- Sets the attachment color from the `color` input (defaults to `danger`)
- Sets Slack username to: `<project-name> CI Notifier`

## Prerequisites

- Vault policy granting access to `development/kv/data/slack` must be configured for the repository.
- The secret at that path must contain a key named `token`.
- The Slack channel provided must exist and the token must have permission to post there.

## Notes

- For failure notifications, use `if: failure()` on the step or job; otherwise it will also fire on success.
- Do not prefix the channel with `#`.
- Message formatting is intentionally minimal for quick triage in alert-focused channels.
