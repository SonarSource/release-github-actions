---
type: GitHub Action
title: Resolve KTLO Epic
description: Finds the current Keep-The-Lights-On epic in a Jira project via a regex match on in-progress epic summaries.
resource: https://github.com/SonarSource/release-github-actions/tree/master/resolve-ktlo-epic
tags: [action, jira, ktlo]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Queries Jira for in-progress epics whose summary matches a configurable regex (default `KTLO`).
Zero matches → logs a warning and outputs an empty string without failing (callers proceed
without a parent epic). Multiple matches → picks the first and warns. Used by
[automated-release](/workflows/automated-release.md) via `ktlo-jira-project-key` /
`ktlo-epic-name-pattern` to attach integration tickets to the active KTLO epic.

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `jira-project` | Jira project key to search | Yes | - |
| `epic-name-pattern` | Regex matched case-insensitively against epic summaries | No | `KTLO` |
| `use-jira-sandbox` | Use sandbox instead of production | No | - |

| Output | Description |
|---|---|
| `epic-key` | Matching epic key, or empty string if none found |

# Citations

[1] [resolve-ktlo-epic/README.md](/../resolve-ktlo-epic/README.md)
