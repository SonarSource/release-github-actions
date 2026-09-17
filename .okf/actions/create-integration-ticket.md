---
type: GitHub Action
title: Create Integration Ticket
description: Creates a Jira integration ticket with a custom summary and links it to an existing release ticket.
resource: https://github.com/SonarSource/release-github-actions/tree/master/create-integration-ticket
tags: [action, jira, integration-ticket]
timestamp: 2026-08-05T00:00:00Z
---

# Overview

Python-based action that connects to Jira, validates the release ticket exists, creates a new
ticket in a target Jira project (e.g. `SLCORE`, `SLVS`, `SLVSCODE`, `SLE`, `SLI`, `SQS`, `SQC`), sets its
description, and links it to the release ticket. Used by
[automated-release](/workflows/automated-release.md) to fan out IDE/CLI integration tickets
after a release.

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `release-ticket-key` | Key of the ticket to link to (e.g. `REL-123`) | Yes | - |
| `target-jira-project` | Key of the project to create the ticket in | Yes | - |

Also accepts `parent-epic`, `edition` and `team`, applied to the created ticket. Uses the shared
[Jira integration helpers](/shared/jira-common.md) and Vault-sourced credentials.

# Optional Jira fields

`parent-epic`, `edition` and `team` are applied during `create_issue`, so a value Jira rejects —
or a field missing from the project's create screen — fails the step rather than being silently
dropped. Availability differs per project (`SONAR`: both; `SC`: team only), which is why
[automated-release](/workflows/automated-release.md) exposes `sqs-ticket-edition` and a shared
`sqs-sqc-ticket-team`, but no `sqc-ticket-edition`.

Covered by a real Jira sandbox job that re-reads the created tickets and asserts the stored
values — the only check that catches a wrong custom field ID or value shape. It runs against
fixed sandbox state (`SONAR-22193`, a fixed team UUID) instead of a setup script, like
[get-jira-release-notes](/actions/get-jira-release-notes.md).

# Citations

[1] [create-integration-ticket/README.md](/../create-integration-ticket/README.md)
