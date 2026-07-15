---
type: GitHub Action
title: Create Jira Version
description: Creates a new version in a Jira project, optionally auto-determining the next version number.
resource: https://github.com/SonarSource/release-github-actions/tree/master/create-jira-version
tags: [action, jira, version]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Connects to Jira and creates a new version in the specified project, either using a provided
version name or deriving the next one via [get-jira-version](/actions/get-jira-version.md).
Called as part of releasing the current version and preparing the next one in
[automated-release](/workflows/automated-release.md) (via
[release-jira-version](/actions/release-jira-version.md)'s flow). No "already exists" check is
performed before creation — see [risk: no idempotency on mutating steps](/risks/no-idempotency.md).

# Schema

| Input | Description |
|---|---|
| `jira-project-key` | Jira project key (e.g. `SONARIAC`); also settable via `JIRA_PROJECT_KEY` |

Uses [shared Jira helpers](/shared/jira-common.md) and Vault-sourced credentials.

# Citations

[1] [create-jira-version/README.md](/../create-jira-version/README.md)
