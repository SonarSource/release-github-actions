---
type: Risk
title: No concurrency guard on the release orchestrator
description: Two overlapping releases on the same branch can race Jira version release, GitHub release publication, and freeze/unfreeze.
tags: [risk, reliability, concurrency, p1]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

`grep concurrency automated-release.yml` finds nothing. Two DRIs, or one double-click on
`workflow_dispatch`, can start two overlapping runs of
[automated-release](/workflows/automated-release.md) on the same branch.

# Failure scenario

Two runs both pass [check-releasability](/actions/check-releasability-status.md), both reach
[release-jira-version](/actions/release-jira-version.md) — one releases the Jira version, the
other's "already released" call (which doesn't exist — see
[no idempotency](/risks/no-idempotency.md)) errors ambiguously, or worse, both publish competing
GitHub releases.

# Recommendation

A one-line native fix:

```yaml
concurrency:
  group: release-${{ inputs.branch }}
  cancel-in-progress: false   # queue, don't cancel a release mid-flight
```

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 2.3](/../docs/ARCHITECTURE_REVIEW.md)
