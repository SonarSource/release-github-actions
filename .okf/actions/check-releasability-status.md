---
type: GitHub Action
title: Check Releasability Status
description: Verifies the GitHub commit-status "Releasability" check is successful on a branch before a release proceeds.
resource: https://github.com/SonarSource/release-github-actions/tree/master/check-releasability-status
tags: [action, releasability, ci-gate]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Reads the GitHub Statuses API for the target branch, filters for the `Releasability` context,
and confirms the state is `success` (optionally also checking that the description does not
contain "failed optional checks").

Standalone, this action historically could read a **stale** commit status. The
[automated-release workflow](/workflows/automated-release.md) itself does **not** rely on this
action for its releasability gate — it instead calls `SonarSource/gh-action_releasability@v3`
directly with the exact commit SHA. See
[risk: stale releasability status read](/risks/stale-releasability-status.md) for the
distinction between this standalone action and the orchestrator's own gate.

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `github-token` | GitHub token for API calls | No | `${{ github.token }}` |
| `branch` | Branch to check | No | `master` |
| `with-optional-checks` | Also check for "failed optional checks" in the description | No | `true` |

Requires `statuses: read` permission on the GitHub token.

# Citations

[1] [check-releasability-status/README.md](/../check-releasability-status/README.md)
