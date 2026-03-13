# Send Slack Message Action

Sends a markdown message to a Slack channel.

Unlike `rtCamp/action-slack-notify`, this action uses `slackapi/slack-github-action` and does not require Docker.

## Inputs

| Input              | Description                                           | Required |
|--------------------|-------------------------------------------------------|----------|
| `channel`          | Slack channel (without `#`) to post the message into. | Yes      |
| `message-markdown` | The message to send, in markdown format.              | Yes      |

## Implementation Details

This action depends on:

- [LoveToKnow/slackify-markdown-action](https://github.com/LoveToKnow/slackify-markdown-action) to convert markdown to Slack's mrkdwn format
- [slackapi/slack-github-action](https://github.com/slackapi/slack-github-action) to send the message via `chat.postMessage`
