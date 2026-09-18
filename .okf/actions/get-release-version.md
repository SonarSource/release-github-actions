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
any context starting with `repox-<branch>` if that isn't present, and extracts the version from
the status description via `jq`. It also exposes the response's commit SHA, so consumers can use
the exact commit whose status supplied the version — [automated-release](/workflows/automated-release.md)
uses both outputs for the selected-branch releasability check. The extracted version is asserted
against `X.Y.Z.BUILD` (Maven) or `X.Y.Z+BUILD` (semver build metadata) before export, and a
malformed repo-specific status fails loud rather than silently falling back to the generic mirror.
`test-get-release-version.yml` covers context selection, shape rejection, and null/missing status
handling end-to-end, but the parse remains inline shell rather than an extracted, unit-tested
script — see [risk: fragile version parsing](/risks/fragile-version-parsing.md).

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `github-token` | GitHub token for API calls | No | `${{ github.token }}` |
| `branch` | Branch to read the version from | No | `master` |

| Output | Description |
|---|---|
| `release-version` | The extracted release version |
| `commit-sha` | The commit SHA whose repox status supplied the version |
| `failure-reason` | Machine-readable failure code (`no-version`, `no-commit-sha`, `invalid-shape`) |

Also exported as the `RELEASE_VERSION` environment variable. Requires `statuses: read`.

# Citations

[1] [get-release-version/README.md](/../get-release-version/README.md)
