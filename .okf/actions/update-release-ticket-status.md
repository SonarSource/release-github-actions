---
type: GitHub Action
title: Update Release Ticket Status
description: Transitions an "Ask for release" Jira ticket to a new status and optionally reassigns it.
resource: https://github.com/SonarSource/release-github-actions/tree/master/update-release-ticket-status
tags: [action, jira, release-ticket]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Fetches the release ticket, optionally reassigns it, and transitions it to the target status
(`Start Progress` or `Technical Release Done`). Used by
[create-jira-release-ticket](/actions/create-jira-release-ticket.md) (to start progress) and by
[automated-release](/workflows/automated-release.md) to close out the ticket lifecycle, assigning
it to `pm-email` after the technical release.

# Schema

| Input | Description | Required |
|---|---|---|
| `release-ticket-key` | Jira ticket key (e.g. `REL-1234`) | Yes |
| `status` | Target status; must be a valid transition | Yes |
| `assignee` | Email of the user to assign | No |

Uses [shared Jira helpers](/shared/jira-common.md) and Vault-sourced credentials.

# Citations

[1] [update-release-ticket-status/README.md](/../update-release-ticket-status/README.md)
