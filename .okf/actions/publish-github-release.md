---
type: GitHub Action
title: Publish GitHub Release
description: Creates a GitHub Release from Jira release notes and triggers/monitors the caller's downstream release workflow.
resource: https://github.com/SonarSource/release-github-actions/tree/master/publish-github-release
tags: [action, github-release, gh-action_release]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Validates a release version is available, creates a GitHub release (optionally attaching Repox
artifacts), then triggers the caller repository's `gh-action_release` workflow and waits for it
to complete. Auto-detects whether the caller uses `gh-action_release` v6 or v7 by inspecting the
workflow file (tag ref, SHA+comment, or a `releaseId` input signals v6; otherwise v7 is assumed).

- **v6**: creates a draft, attaches artifacts, publishes when `draft=false`; passes `releaseId`
  downstream.
- **v7 (default)**: draft-first flow — always drafts, passes only `version`/`dryRun`; v7 itself
  handles draft-to-published promotion.

This action **is** partially idempotent — it queries existing releases by title and reuses an
existing draft rather than colliding — but only for the draft case; a re-run after a *published*
release is unguarded. See [risk: no idempotency on mutating steps](/risks/no-idempotency.md).

# Citations

[1] [publish-github-release/README.md](/../publish-github-release/README.md)
