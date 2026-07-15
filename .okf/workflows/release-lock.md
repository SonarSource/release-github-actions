---
type: Reusable Workflow
title: Release Lock
description: Sets a release-lock GitHub commit status that blocks other PRs from merging while a version-bump PR is open.
resource: https://github.com/SonarSource/release-github-actions/blob/master/.github/workflows/release-lock.yml
tags: [workflow, release, branch-protection, required-check]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Closes the gap left by [automated-release](/workflows/automated-release.md)'s early unfreeze:
the branch reopens right after the GitHub release publishes, but *before* the version-bump PR
(from [bump-version](/actions/bump-version.md)) is created. That gap lets other PRs merge into
an unbumped branch. Freeze (`lock_branch`) can't cover the gap — it's all-or-nothing, including
for the release DRI, and the bump PR push itself needs an unfrozen branch.

The fix: a required-status-check signal, "a version-bump PR is open," implemented as a thin
per-repo `release-lock.yml` caller that delegates to this reusable workflow.

# Schema

Input: `bump-branch-prefix` (default `bot/prepare-next-development-iteration-`) — identifies the
version-bump PR by its head branch prefix, invariant across Maven/Gradle/custom paths.

| Condition | Status on other PRs | Status on bump PR |
|---|---|---|
| No bump PR open | ✅ success — "No release in progress" | — |
| Bump PR open | ❌ failure — "Release in progress — merge the version-bump PR first" | ✅ success |
| Bump PR merged/abandoned | ✅ success (auto-reset) | — |

When the bump PR closes, the workflow sweeps all open PRs (paginated, drafts included) and
resets each to green automatically.

# Adoption

Two-phase, per repo, via the `automated-release-setup` skill:

1. **Phase 1 (unenforced)** — add the thin `release-lock.yml` caller; observe over one or two
   real releases.
2. **Phase 2 (enforce)** — register `release-lock` as a required status check on the branch.

The gate is opt-in and non-breaking: a repo without it releases exactly as before. Once
[lock-branch](/actions/lock-branch.md)'s freeze/unfreeze preserves
`required_status_checks.contexts` (it does, by design), the `release-lock` check survives every
freeze/unfreeze cycle once registered.

A future release will flip `automated-release`'s `freeze-branch` default from `true` to `false`,
since Phase 2 makes the `lock_branch` freeze redundant — repos must reach Phase 2 before that
default flip lands, or they'd briefly have neither guard.

# Citations

[1] [docs/AUTOMATED_RELEASE.md § Release lock gate](/../docs/AUTOMATED_RELEASE.md)
