---
type: Risk
title: Internal @v1 refs instead of @master, and the release-time pin that missed them
description: A confirmed violation of the Golden Architecture rule, silently left unpinned by the release-time sed rewrite. Fixed in GHA-417.
tags: [risk, maintainability, golden-architecture, p1]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

`automated-release.yml:930` (formerly `:907`) referenced `update-plugins-deployer@v1`, while
every other internal ref in the file uses `@master` — a confirmed violation of
[the Golden Architecture rule](/decisions/golden-architecture.md) that internal `uses:` must
never be written as `@v1`. Because [release.yml](/workflows/release.md)'s `sed` only rewrites
`@master` refs, this one was silently left floating: on the `v1` snapshot,
[update-plugins-deployer](/actions/update-plugins-deployer.md) resolved to a different (later,
moving) snapshot than every one of its sibling actions.

**Fixed (GHA-417)**, along with a wider instance of the same defect found while fixing it:
`abd-automated-release.yml` (14 refs) and `ide-automated-release.yml` (10 refs) referenced
sibling actions as `@v1` throughout, and `release.yml`'s `find -name "automated-release.yml"`
filter did not match those filenames — so those two workflows were neither exercised from
`master` nor pinned on the `v1` snapshot. All 24 refs are now `@master`, and the filter is
`-name "*automated-release.yml"`.

# Recommendation

1. ~~Fix the `@v1` refs to `@master`.~~ Done (GHA-417).
2. **Still open:** add a CI grep-guard that fails on any
   `SonarSource/release-github-actions/...@v1` string appearing in `action.yml` /
   `*automated-release.yml` — making the rule enforced, not prose-only. Consumer-facing usage
   examples in `README.md` files legitimately use `@v1`, so the guard must be scoped, not global.
3. Consider a `v1-rc` staging branch so `master` isn't simultaneously "dev" and "what tests run
   against."

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 4.3](/../docs/ARCHITECTURE_REVIEW.md)
