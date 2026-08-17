# Update Log

## 2026-08-14
* **Releasability failure detail in summary**: The `check-releasability` job's `Summary` step now
  runs on any failure, not only when `verbose: true` — so its per-check ✅/❌ breakdown (e.g.
  `QA`, `Jira`, `QualityGate`) is always visible in that job's own step-summary section on the
  run's summary page, right alongside the top-level `summarize-release` message. Just an `if:`
  condition change; no new job outputs or cross-job plumbing. Partially resolves
  [unhelpful-failure-summary](/risks/unhelpful-failure-summary.md) — scoped to the releasability
  case only; the other eight jobs in the DAG are unchanged.

## 2026-07-23
* **Automated release Slack visibility**: After creating a GitHub release, the analyzer release
  workflow now sends a short project/version/release-notes announcement to the private Code
  Quality PM/EM leads channel by default. Callers can opt out with
  `code-quality-leads-slack-notification: false`; the existing configurable full-summary Slack
  destination remains independent.

## 2026-07-15
* **Creation**: Established the OKF bundle for this repository — [actions/](/actions/) (22 composite actions), [workflows/](/workflows/) (5 reusable workflows), [shared/](/shared/) (the Jira helper module), [decisions/](/decisions/) (Golden Architecture and security conventions, plus the 2026-07-14 architecture review), and [risks/](/risks/) (14 individual findings distilled from [docs/ARCHITECTURE_REVIEW.md](/../docs/ARCHITECTURE_REVIEW.md)).
