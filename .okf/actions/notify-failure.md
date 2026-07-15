---
type: GitHub Action
title: Notify Failure
description: Sends a rich Slack failure notification assembled automatically from GitHub context, commit info, and job logs.
resource: https://github.com/SonarSource/release-github-actions/tree/master/notify-failure
tags: [action, slack, ci, observability]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

On CI failure, fetches commit info and job logs via the GitHub API and posts a structured Slack
message: repo/branch/workflow, failed job names, run attempt, last commit, a root-cause line
extracted from job logs, a Develocity build-scan link if present, and links to the run. All
sections included by default; individually excludable. Depends on
[vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for the Slack token.

# Citations

[1] [notify-failure/README.md](/../notify-failure/README.md)
