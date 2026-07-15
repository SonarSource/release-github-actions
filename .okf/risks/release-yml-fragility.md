---
type: Risk
title: release.yml's force-push + sed rewrite has no post-write assertions
description: The pinning of @master refs to a release SHA can silently fail partially, or the force-push can silently no-op, with no alarm either way.
tags: [risk, maintainability, release-yml, p2]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

[release.yml](/workflows/release.md) does `git reset --hard $TAG` → `sed` rewrite
`@master`→SHA → `git push --force-with-lease`, with several fragilities:

- `sed` only rewrites `@master`; an internal `@v1` ref (see
  [internal @v1 violation](/risks/internal-v1-violation.md)) or an oddly-spaced ref is silently
  not pinned — and there is **no post-sed assertion** that zero `@master` refs remain.
- `--force-with-lease` on a shared consumer-facing branch: if the lease fails, `v1` **silently**
  doesn't update and consumers keep resolving the old snapshot, with no alarm.
- `git commit ... || true` (`:53`) swallows *all* commit failures as "nothing changed," not just
  the intended "no diff" case.
- No verification that the rewritten `v1` is internally consistent (e.g. no remaining
  cross-references to `master`).

# Recommendation

After the `sed`, assert `! grep -rn '@master'` on the rewritten files (and no internal `@v1`)
and fail loudly if either check fails. Replace `commit || true` with an explicit "is the diff
empty?" check. Keep immutable `v1.2.3` tags alongside the moving `v1` branch so a bad
force-push is recoverable.

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 4.4](/../docs/ARCHITECTURE_REVIEW.md)
