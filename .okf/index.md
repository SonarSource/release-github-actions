---
okf_version: "0.1"
---

# release-github-actions — Knowledge Bundle

Reusable GitHub Actions and workflows automating the SonarSource analyzer release process:
Jira integration, GitHub releases, cross-repository updates, and Slack notifications.

# Directories

* [actions/](actions/) - the 22 composite GitHub Actions in this repo, one concept per action.
* [workflows/](workflows/) - the reusable `workflow_call` orchestrators (automated-release, ide-automated-release, abd-automated-release, release-lock) and the repo's own release workflow.
* [shared/](shared/) - Python helpers shared across Jira-integration actions.
* [decisions/](decisions/) - architectural rules and reviews governing this repo (Golden Architecture, security conventions, the 2026-07 architecture review).
* [risks/](risks/) - individual reliability/testability/maintainability findings from the architecture review, one concept per finding.

# Start here

* [automated-release](workflows/automated-release.md) - the main orchestrator; read this first to understand how the actions fit together.
* [Golden Architecture](decisions/golden-architecture.md) - the versioning/API-surface rule that governs every action.
* [Architecture Review (2026-07-14)](decisions/architecture-review-2026-07.md) - TL;DR of known reliability and testability gaps.
