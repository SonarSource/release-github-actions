---
type: Risk
title: Failure summary doesn't say what failed or what to do
description: On failure the Slack summary collapses to generic "re-run as needed" advice that is actively dangerous given the idempotency gap.
tags: [risk, observability, failure-summary, p1]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

The happy-path summary (`automated-release.yml:1036`–`1083`) puts all relevant URLs in one
Slack message — genuinely good. On failure it collapses to *"One or more jobs failed… re-run as
needed"*, which — given [no idempotency](/risks/no-idempotency.md) — is **actively dangerous**
advice. It doesn't name the failing job in Slack (you must open the Actions run), even though
per-job `RESULT_*` values are already collected and then thrown away into a single boolean.
`verbose` defaults to `false`, so out of the box you get the *least* diagnostic detail.

# Recommendation

- Always print the per-job ✅/❌ checklist in the failure summary (the data already exists).
- Name the first failing job plus a one-line "what this usually means / what to do," pointing at
  the recovery runbook from [no idempotency](/risks/no-idempotency.md).
- Replace "re-run as needed" with idempotency-aware guidance.

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 5.1](/../docs/ARCHITECTURE_REVIEW.md)
