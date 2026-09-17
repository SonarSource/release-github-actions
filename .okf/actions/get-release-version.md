---
type: GitHub Action
title: Get Release Version
description: Extracts the release version and commit SHA from the repox commit status on a branch.
resource: https://github.com/SonarSource/release-github-actions/tree/master/get-release-version
tags: [action, version, repox]
timestamp: 2026-09-17T00:00:00Z
---

# Overview

Calls the GitHub API for the commit status on a branch (default `master`). Prefers the exact
`repox-<repo-name>-<branch>` context — the repo's own promoted-build status — falling back to
any context starting with `repox-<branch>` if that isn't present, extracts the version from the
status description via `jq`, and asserts it matches `X.Y.Z.BUILD` (Maven) or `X.Y.Z+BUILD`
(semver build metadata) before exporting it. Every downstream job in
[automated-release](/workflows/automated-release.md) keys off this output; the
parse itself is still inline shell with no unit test — see
[risk: fragile version parsing](/risks/fragile-version-parsing.md).

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
