# Notify Slack Action

This GitHub Action sends a Slack notification with a custom message.

## Description

The action posts a message to a Slack channel. The caller is responsible for building the message string.

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) to retrieve the Slack token from Vault

## Inputs

| Input           | Description                                                                                            | Required | Default   |
|-----------------|--------------------------------------------------------------------------------------------------------|----------|-----------|
| `project-name`  | The display name of the project; used in the Slack username.                                           | Yes      | -         |
| `icon`          | Emoji icon for the Slack message (Slack emoji code).                                                   | No       | `:alert:` |
| `slack-channel` | Slack channel (without `#`) to post the notification into.                                             | Yes      | -         |
| `message`       | The Slack message to send (mrkdwn format).                                                             | Yes      | -         |
| `color`         | Slack attachment color (`good`, `danger`, `warning`, or a hex code).                                   | No       | `danger`  |
| `jobs`          | **Deprecated.** A GitHub needs-like object of jobs and results. When `message` is not set, a failed-jobs summary is built from this input. Build the message in the caller and pass it via `message` instead. | No | - |

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
      - name: Build failure message
        id: msg
        if: failure()
        run: |
          FAILED=$(echo '${{ toJSON(needs) }}' | jq -r 'to_entries | map(select(.value.result == "failure") | .key) | join(", ")')
          echo "message=*Run:* ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}\n*Failed Jobs:* $FAILED" >> $GITHUB_OUTPUT
      - uses: SonarSource/release-github-actions/notify-slack@v1
        with:
          project-name: 'My Project'
          slack-channel: 'engineering-alerts'
          message: ${{ steps.msg.outputs.message }}
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

## Implementation Details

The action is a composite action that:
- Fetches `SLACK_TOKEN` from Vault path `development/kv/data/slack` using `vault-action-wrapper`
- Uses a Python script (`notify_slack.py`) with the `requests` library to call the Slack API directly — no Docker dependency
- Sets the attachment color from the `color` input (defaults to `danger`)
- Sets Slack username to: `<project-name> CI Notifier`

## Prerequisites

- Vault policy granting access to `development/kv/data/slack` must be configured for the repository.
- The secret at that path must contain a key named `token`.
- The Slack channel provided must exist and the token must have permission to post there.

## Notes

- For failure notifications, use `if: failure()` on the step or job; otherwise it will also fire on success.
- Do not prefix the channel with `#`.
- Message formatting uses mrkdwn (Slack's markdown dialect).
