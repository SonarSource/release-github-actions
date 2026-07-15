---
type: GitHub Action
title: Create Pull Request
description: In-house replacement for peter-evans/create-pull-request using the gh CLI, with vault-based token resolution.
resource: https://github.com/SonarSource/release-github-actions/tree/master/create-pull-request
tags: [action, pull-request, github-cli, shared-building-block]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Stages and commits file changes on a new branch, then creates a pull request (or updates an
existing one) via the `gh` CLI. Supports labels, reviewers, assignees, milestones, and drafts.
Resolves an authentication token via Vault first, falling back to the provided `token` input.

This is a shared building block reused by several higher-level actions:
[update-analyzer](/actions/update-analyzer.md),
[update-plugins-deployer](/actions/update-plugins-deployer.md),
[update-analysis-as-a-service](/actions/update-analysis-as-a-service.md), and
[update-rule-metadata](/actions/update-rule-metadata.md).

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `token` | GitHub token (vault token preferred, falls back to this) | No | `${{ github.token }}` |
| `add-paths` | Comma/newline-separated paths to stage | No | `''` (all changes) |
| `commit-message` | Commit message | No | `[create-pull-request] automated change` |
| `committer` | Committer `Name <email>` | No | `github-actions[bot] <...>` |
| `author` | Author `Name <email>` | No | `${{ github.actor }} <...>` |
| `signoff` | Add `Signed-off-by` trailer | No | `false` |

Requires the repository to already be checked out, a token with `contents: write` and
`pull-requests: write`, and (for vault resolution) `id-token: write` plus a vault secret at
`development/github/token/{REPO_OWNER_NAME_DASH}-release-automation`.

# Citations

[1] [create-pull-request/README.md](/../create-pull-request/README.md)
