# Update Log

## 2026-07-23
* **Automated release Slack visibility**: After creating a GitHub release, the analyzer release
  workflow now sends a short project/version/release-notes announcement to the private Code
  Quality PM/EM leads channel by default. Callers can opt out with
  `code-quality-leads-slack-notification: false`; the existing configurable full-summary Slack
  destination remains independent.

## 2026-07-15
* **Creation**: Established the OKF bundle for this repository — [actions/](/actions/) (22 composite actions), [workflows/](/workflows/) (5 reusable workflows), [shared/](/shared/) (the Jira helper module), [decisions/](/decisions/) (Golden Architecture and security conventions, plus the 2026-07-14 architecture review), and [risks/](/risks/) (14 individual findings distilled from [docs/ARCHITECTURE_REVIEW.md](/../docs/ARCHITECTURE_REVIEW.md)).
