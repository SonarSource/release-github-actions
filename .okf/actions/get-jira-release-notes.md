---
type: GitHub Action
title: Get Jira Release Notes
description: Fetches Jira issues for a fixVersion and formats them into release notes plus the release notes URL.
resource: https://github.com/SonarSource/release-github-actions/tree/master/get-jira-release-notes
tags: [action, jira, release-notes]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Retrieves the version ID for a project/version name, fetches all issues with that `fixVersion`,
and formats them into categorized release notes (Markdown and Jira wiki markup), alongside the
Jira release-notes URL. Falls back to [get-jira-version](/actions/get-jira-version.md) when
neither `jira-version-name` nor `JIRA_VERSION_NAME` is supplied. Used by
[create-jira-release-ticket](/actions/create-jira-release-ticket.md) and by
[automated-release](/workflows/automated-release.md) when `release-notes` is left empty.

# Schema

Uses [shared Jira helpers](/shared/jira-common.md) and Vault-sourced credentials.

# Citations

[1] [get-jira-release-notes/README.md](/../get-jira-release-notes/README.md)
