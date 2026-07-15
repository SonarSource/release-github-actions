---
type: GitHub Action
title: Create Jira Release Ticket
description: Creates the "Ask for release" ticket in Jira that anchors the rest of the release process.
resource: https://github.com/SonarSource/release-github-actions/tree/master/create-jira-release-ticket
tags: [action, jira, release-ticket]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Creates an "Ask for release" ticket in Jira with custom fields populated (short description,
release notes link, rule-props-changed, etc.), optionally auto-fetching the release version and
release notes URL, and optionally transitioning it to "Start Progress". This is the first
Jira-side mutation in [automated-release](/workflows/automated-release.md) — see
[risk: no idempotency on mutating steps](/risks/no-idempotency.md), since nothing checks whether
a REL ticket for this version already exists before creating a new one.

# Schema

Depends on [get-release-version](/actions/get-release-version.md) (when version not provided),
[update-release-ticket-status](/actions/update-release-ticket-status.md) (when starting
progress), and [get-jira-release-notes](/actions/get-jira-release-notes.md) (when no release
notes URL is supplied). Uses [shared Jira helpers](/shared/jira-common.md) and Vault-sourced
credentials.

# Citations

[1] [create-jira-release-ticket/README.md](/../create-jira-release-ticket/README.md)
