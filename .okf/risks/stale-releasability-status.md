---
type: Risk
title: check-releasability-status (standalone action) can read a stale commit status
description: The standalone action reads whatever status is currently posted; the orchestrator itself avoids this by using the exact commit SHA via an external action.
tags: [risk, releasability, ecosystem-context, p2]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

Historically, `check-releasability` reads reported green when a Jira-optional check was actually
stale/failed, and separately later *failed* releases on stale optional checks (XP squad, Feb
2026). This applies to the standalone
[check-releasability-status](/actions/check-releasability-status.md) action, which reads
whatever `Releasability` commit status is currently posted for a branch — there's an inherent
staleness window between "status posted" and "status read."

**Important scoping note:** [automated-release](/workflows/automated-release.md) itself does
**not** depend on this standalone action for its own releasability gate — the orchestrator calls
`SonarSource/gh-action_releasability@v3` directly with the exact `commit-sha` (`:351`), which
sidesteps the staleness window. This risk is ecosystem context (repos that use the standalone
action directly), not a defect in the release orchestrator's own path.

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 1](/../docs/ARCHITECTURE_REVIEW.md)
