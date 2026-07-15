---
type: GitHub Action
title: Get Jira Version
description: Converts a release version (major.minor.patch.build) into Jira's version naming convention.
resource: https://github.com/SonarSource/release-github-actions/tree/master/get-jira-version
tags: [action, jira, version]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Takes a release version and derives the Jira-compatible form by keeping only
major.minor.patch and stripping a trailing `.0`. Depends on
[get-release-version](/actions/get-release-version.md) to obtain the release version.

# Schema

| Output | Description |
|---|---|
| `jira-version-name` | The Jira-formatted version |

Also exported as the `JIRA_VERSION_NAME` environment variable.

# Citations

[1] [get-jira-version/README.md](/../get-jira-version/README.md)
