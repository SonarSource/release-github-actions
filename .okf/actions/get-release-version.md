---
type: GitHub Action
title: Get Release Version
description: Extracts the release version from the repox commit status on a branch.
resource: https://github.com/SonarSource/release-github-actions/tree/master/get-release-version
tags: [action, version, repox]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Calls the GitHub API for the commit status on a branch (default `master`), filters for a
context starting with `repox`, and extracts the version from the status description via `jq`.
Every downstream job in [automated-release](/workflows/automated-release.md) keys off this
output, yet the parse is inline shell with no unit test — see
[risk: fragile version parsing](/risks/fragile-version-parsing.md).

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `github-token` | GitHub token for API calls | No | `${{ github.token }}` |
| `branch` | Branch to read the version from | No | `master` |

| Output | Description |
|---|---|
| `release-version` | The extracted release version |

Also exported as the `RELEASE_VERSION` environment variable. Requires `statuses: read`.

# Citations

[1] [get-release-version/README.md](/../get-release-version/README.md)
