---
type: Risk
title: No mutating step in the release pipeline is idempotent
description: A failure partway through the release DAG leaves published GitHub releases, unreleased Jira versions, and duplicate tickets with no safe re-run.
tags: [risk, reliability, idempotency, p0]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

The [automated-release](/workflows/automated-release.md) job DAG performs irreversible actions
in an order hostile to partial failure:

```
freeze → check → prepare → create-release-ticket → publish-github-release
   → UNFREEZE → release-in-jira → bump-version → integration-tickets → analyzer PRs
```

If [publish-github-release](/actions/publish-github-release.md) succeeds and
[release-jira-version](/actions/release-jira-version.md) then fails, the result is a published
GitHub release/tag, a Jira version not released with no next version created, and a REL ticket
stuck "In Progress."

Idempotency is **inconsistent**, not uniformly absent, which is arguably worse — you can't
reason about what a re-run will do:

- [publish-github-release](/actions/publish-github-release.md) is *partially* idempotent — it
  reuses an existing draft release by title — but only for the draft case; a re-run after a
  *published* release is unguarded.
- [create-jira-release-ticket](/actions/create-jira-release-ticket.md) is not idempotent —
  nothing checks whether a REL ticket for this version already exists.
- [release-jira-version](/actions/release-jira-version.md) /
  [create-jira-version](/actions/create-jira-version.md) have no "already released?" check.

The workflow admits it can't resume: the rule-metadata gate literally says "start a new run
instead of re-running failed jobs."

# Failure scenario

Jira has a transient timeout right after the GitHub release is published. The DRI sees a failed
job, has no runbook, and either re-runs (risking a duplicate REL ticket / double release attempt)
or manually patches Jira state while the branch sits in an ambiguous state.

# Recommendation

1. Make each mutating action check-then-act idempotent (query "does X already exist / is it
   already in state Y?" before creating/mutating).
2. Until then, ship a per-failure-point recovery runbook in
   [AUTOMATED_RELEASE.md](/../docs/AUTOMATED_RELEASE.md) keyed by "last successful job."
3. Stage reversible work first, commit irreversible work last (the saga/two-phase pattern).

**Re-run gotcha:** GitHub "re-run failed jobs" replays the cached workflow *definition* — a YAML
bugfix requires a fresh run, not a re-run.

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 2.1](/../docs/ARCHITECTURE_REVIEW.md)
