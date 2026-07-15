---
type: Decision
title: Golden Architecture — actions as a public API, @master vs @v1
description: Every action's inputs/outputs are a public API surface; internal refs use @master on master and get frozen to a SHA only on v1.
tags: [decision, architecture, versioning, public-api]
timestamp: 2026-07-15T00:00:00Z
---

# Decision

Every action is a self-contained composite invoked as
`SonarSource/release-github-actions/<action>@v1`. Consumers pin `@v1`. Internal refactors within
an action are transparent to consumers; **changing an action's `inputs:`/`outputs:` is a
breaking change** and must be treated as a public API change.

Source on `master` references sibling actions as `@master` (e.g.
`SonarSource/release-github-actions/get-release-version@master`), so any test run from `master`
exercises the latest code across all sub-actions. The [release workflow](/workflows/release.md)
fast-forwards the `v1` branch to a release tag and then rewrites every `@master` ref to the
exact release commit SHA — so `v1` is a self-consistent frozen snapshot with no floating refs.

**New internal `uses:` must never be written as `@v1`** — not in `action.yml` files, not in
`automated-release.yml`, not in test workflows (including string-match assertions like
`grep -q "...@master"`). Always `@master`; the release workflow handles pinning.

# Why

- Lets `master` stay a coherent, always-current integration branch that CI actually exercises.
- Lets `v1` (and future major versions) be an immutable, auditable snapshot that a squad's
  release didn't silently drift out from under.
- A rename/removal on `master` without a version bump would break every `@v1` consumer
  mid-release, often after the branch is already frozen — see
  [risk: input sprawl with undocumented invalid combinations](/risks/input-sprawl.md) and
  [risk: no inputs/outputs contract test](/risks/no-contract-test.md) for how this is currently
  under-enforced.

# Violations found

`automated-release.yml:907` references `update-plugins-deployer@v1` while every other internal
ref uses `@master` — a confirmed rule violation caught by the
[architecture review](/decisions/architecture-review-2026-07.md). The release-time `sed` only
rewrites `@master`, so this ref was silently left floating, pinned to a different snapshot than
its siblings. Recommended fix: correct the ref to `@master` and add a CI grep-guard so the rule
is enforced, not just prose.

# Citations

[1] [CLAUDE.md § Golden Architecture](/../CLAUDE.md)
[2] [docs/ARCHITECTURE_REVIEW.md § 4.3](/../docs/ARCHITECTURE_REVIEW.md)
