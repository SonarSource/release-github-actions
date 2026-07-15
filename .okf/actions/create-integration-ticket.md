---
type: GitHub Action
title: Create Integration Ticket
description: Creates a Jira integration ticket with a custom summary and links it to an existing release ticket.
resource: https://github.com/SonarSource/release-github-actions/tree/master/create-integration-ticket
tags: [action, jira, integration-ticket]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Python-based action that connects to Jira, validates the release ticket exists, creates a new
ticket in a target Jira project (e.g. `SLVS`, `SLVSCODE`, `SLE`, `SLI`, `SQS`, `SQC`), sets its
description, and links it to the release ticket. Used by
[automated-release](/workflows/automated-release.md) to fan out IDE/CLI integration tickets
after a release.

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `release-ticket-key` | Key of the ticket to link to (e.g. `REL-123`) | Yes | - |
| `target-jira-project` | Key of the project to create the ticket in | Yes | - |

Uses the shared [Jira integration helpers](/shared/jira-common.md) and Vault-sourced
credentials.

# Citations

[1] [create-integration-ticket/README.md](/../create-integration-ticket/README.md)
