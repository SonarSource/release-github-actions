---
type: Risk
title: automated-release.yml:907 references @v1 instead of @master
description: A confirmed violation of the Golden Architecture rule, silently left unpinned by the release-time sed rewrite.
tags: [risk, maintainability, golden-architecture, p1]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

`automated-release.yml:907` references `update-plugins-deployer@v1`, while every other internal
ref in the file uses `@master` — a confirmed violation of
[the Golden Architecture rule](/decisions/golden-architecture.md) that internal `uses:` must
never be written as `@v1`. Because [release.yml](/workflows/release.md)'s `sed` only rewrites
`@master` refs, this one is silently left floating: on the `v1` snapshot,
[update-plugins-deployer](/actions/update-plugins-deployer.md) resolves to a different (later,
moving) snapshot than every one of its sibling actions.

# Recommendation

1. Fix `:907` to `@master`.
2. Add a CI grep-guard that fails on any `SonarSource/release-github-actions/...@v1` string
   appearing anywhere in the repo — making the rule enforced, not prose-only.
3. Consider a `v1-rc` staging branch so `master` isn't simultaneously "dev" and "what tests run
   against."

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 4.3](/../docs/ARCHITECTURE_REVIEW.md)
