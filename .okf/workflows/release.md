---
type: Workflow
title: Release (of release-github-actions itself)
description: On a published GitHub release of this repo, fast-forwards the v1 branch and pins internal @master refs to the release SHA.
resource: https://github.com/SonarSource/release-github-actions/blob/master/.github/workflows/release.yml
tags: [workflow, release, self-hosting, v1-pinning]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Triggered on `release: [published]`. Checks out the `v${MAJOR}` version branch (e.g. `v1`),
`git reset --hard`s it to the release tag, then rewrites every internal `@master` reference in
`action.yml` files and `automated-release.yml` to the exact release commit SHA via `sed`, commits,
and `git push --force-with-lease`.

This is what makes the [Golden Architecture](/decisions/golden-architecture.md)'s "`@master` on
master, frozen SHA on `v1`" split work: source on `master` always references siblings as
`@master` so tests exercise the latest code, while `v1` becomes a self-consistent frozen
snapshot with no floating refs — consumers pin `@v1` and get exactly what was tested at release
time.

# Known fragility

Per [risk: release.yml force-push + sed rewrite](/risks/release-yml-fragility.md): the `sed`
only rewrites `@master` (an internal `@v1` reference is silently left unpinned — see
[risk: internal @v1 rule violation](/risks/internal-v1-violation.md)); there's no post-sed
assertion that zero `@master` refs remain; `--force-with-lease` failing leaves `v1` silently
stale; and `git commit ... || true` swallows all commit failures as "nothing changed."

# Citations

[1] [CLAUDE.md § Golden Architecture](/../CLAUDE.md)
[2] [docs/ARCHITECTURE_REVIEW.md § 4.4](/../docs/ARCHITECTURE_REVIEW.md)
