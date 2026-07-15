---
type: Risk
title: Dead set-release-lock/clear-release-lock stub jobs misrepresent guarantees
description: No-op jobs are surrounded by comments describing locking behavior that does not actually happen — a scar from the GHA-355 revert.
tags: [risk, dead-code, documentation, p2]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

`set-release-lock` and `clear-release-lock` (`automated-release.yml:292`–`299`, `723`–`731`) are
no-op `echo "Skipped…"` jobs, but their surrounding comments describe elaborate PR-locking
behavior that **does not happen**. A future reader believes other PRs are locked during a
release when they aren't. This is a scar from GHA-355, where the actual sweep was reverted after
breaking releases across multiple repos — the real mechanism today is
[release-lock](/workflows/release-lock.md), a separate opt-in required-status-check workflow.

# Recommendation

Either wire the token and make the stub jobs actually work, or delete the jobs *and* the
aspirational comments. Don't ship scaffolding that lies about the guarantees it provides.
Near-zero risk, do first.

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 7](/../docs/ARCHITECTURE_REVIEW.md)
