---
type: GitHub Action
title: Send Slack Message
description: Sends a caller-provided markdown message to a Slack channel.
resource: https://github.com/SonarSource/release-github-actions/tree/master/slack-message
tags: [action, slack]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Posts a markdown message (converted to Slack mrkdwn) to a channel. Unlike
`rtCamp/action-slack-notify`, uses `slackapi/slack-github-action` and needs no Docker. The
caller builds the message string; this action only delivers it. Depends on
`LoveToKnow/slackify-markdown-action` for markdown conversion and
`slackapi/slack-github-action` for `chat.postMessage`.

# Schema

| Input | Description | Required |
|---|---|---|
| `channel` | Slack channel (without `#`) | Yes |
| `message-markdown` | Message in markdown format | Yes |

# Citations

[1] [slack-message/README.md](/../slack-message/README.md)
