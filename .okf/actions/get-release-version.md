---
type: GitHub Action
title: Get Release Version
description: Extracts the release version and commit SHA from the repox commit status on a branch.
resource: https://github.com/SonarSource/release-github-actions/tree/master/get-release-version
tags: [action, version, repox]
timestamp: 2026-09-16T00:00:00Z
---

# Overview

Calls the GitHub API for the combined commit status on a branch (default `master`), filters for a
context starting with `repox`, and extracts the version from the status description via `jq`.
It also exposes the response's commit SHA, so consumers can use the exact commit whose status
supplied the version. [automated-release](/workflows/automated-release.md) uses both outputs for
the selected-branch releasability check. The version parse remains tied to the human-readable
status description — see [risk: fragile version parsing](/risks/fragile-version-parsing.md).

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `github-token` | GitHub token for API calls | No | `${{ github.token }}` |
| `branch` | Branch to read the version from | No | `master` |

| Output | Description |
|---|---|
| `release-version` | The extracted release version |
| `commit-sha` | The commit SHA whose repox status supplied the version |

Also exported as the `RELEASE_VERSION` environment variable. Requires `statuses: read`.

# Citations

[1] [get-release-version/README.md](/../get-release-version/README.md)
