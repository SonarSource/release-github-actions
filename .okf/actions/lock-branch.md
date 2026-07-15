---
type: GitHub Action
title: Lock Branch
description: Locks or unlocks a branch by toggling lock_branch in its branch protection rules.
resource: https://github.com/SonarSource/release-github-actions/tree/master/lock-branch
tags: [action, branch-protection, freeze]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Freezes (locks) or unfreezes (unlocks) a branch by modifying `lock_branch` in its branch
protection rules, with an optional Slack notification. This is the mechanism behind the
`freeze-branch` input of [automated-release](/workflows/automated-release.md). Requires branch
protection to be enabled (or creates it with minimal settings) and a token with
`administration:write`.

Its underlying `lock_branch.py` preserves `required_status_checks.contexts` on every
freeze/unfreeze PUT, which is why the [release-lock](/workflows/release-lock.md) required check
survives freeze/unfreeze cycles once registered. See
[risk: always() unfreeze on failure](/risks/unfreeze-on-failure.md) for how the orchestrator
uses this action in a way that can leave a broken release with an open branch.

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `branch` | Branch to lock/unlock | Yes | - |
| `freeze` | `true` to lock, `false` to unlock | Yes | - |
| `slack-channel` | Slack channel to notify | No | - |
| `github-token` | Token with admin permissions | No | From Vault |
| `slack-token` | Slack token | No | From Vault |

| Output | Description |
|---|---|
| `previous-state` | Previous lock state |
| `current-state` | Current lock state |
| `branch` | Branch that was modified |

# Citations

[1] [lock-branch/README.md](/../lock-branch/README.md)
