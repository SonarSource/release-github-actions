---
type: GitHub Action
title: Notify Slack on Failure
description: Sends a Slack notification when a job fails.
resource: https://github.com/SonarSource/release-github-actions/tree/master/notify-slack
tags: [action, slack, ci]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Minimal action that posts a job-failure notification to Slack. Lighter-weight than
[notify-failure](/actions/notify-failure.md), which assembles a richer message with root-cause
extraction. Depends on
[vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for the Slack token.

# Citations

[1] [notify-slack/README.md](/../notify-slack/README.md)
