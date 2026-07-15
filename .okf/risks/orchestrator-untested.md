---
type: Risk
title: The orchestrator's control flow has no test
description: "needs:/if: wiring and output plumbing across ~15 jobs and ~50 inputs is exercised only in production, not in CI."
tags: [risk, testability, orchestrator, p0]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

[automated-release](/workflows/automated-release.md) is ~1,100 lines, ~50 inputs, 15 jobs wired
by hand-written `needs:` + multi-clause `if:` guards. `test-all.yml` fans out to **per-action**
tests only — nothing instantiates the orchestrator itself, so the logic deciding whether a
release proceeds or corrupts is unexercised:

- The `!cancelled() && (result == 'success' || == 'skipped')` pattern is a footgun: add a new
  gate job upstream and forget its `skipped` clause, and the gate is silently bypassed. GHA-226
  and GHA-227 are this exact bug class, in production — a skipped
  [update-rule-metadata](/actions/update-rule-metadata.md) silently skipped unfreeze too.
- `summarize-release` computes `ALL_SUCCESS` from a hand-maintained `RESULT_*` list
  (`:993`, with a comment begging editors to keep two lists in sync). Miss one and a failed
  release reports "🎉 Successful."
- A typo in `needs.<job>.outputs.<x>` resolves to an empty string, not an error — so
  `release-version: ""` flows downstream and detonates three jobs later, far from the cause.

# Recommendation

1. Add a dry-run mode to the orchestrator (`if: !inputs.dry-run` on every side-effecting step).
   Run it in CI to assert the DAG resolves, `if:` gates behave, and output plumbing connects —
   no Jira/GitHub mutation. Highest-value test; directly closes the GHA-226/227 class.
2. Adopt `actionlint` (syntax + `needs` reference validation) plus a lint that flags any
   `needs.X` where `X` isn't declared in the job's `needs:` list.
3. Build the integration harness that already has a ticket — GHA-247 (epic) / GHA-249 (dummy
   analyzer repo + mocked repox status), currently "To Do."

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 3.1](/../docs/ARCHITECTURE_REVIEW.md)
