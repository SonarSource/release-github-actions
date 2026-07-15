---
type: Risk
title: SonarSource-specific hardcoding makes "reusable" aspirational
description: Jira project keys and custom field IDs for integration targets are string literals baked into the orchestrator, not configuration.
tags: [risk, maintainability, hardcoding, p2]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

Project keys `SLVS`, `SLVSCODE`, `SLE`, `SLI`, `CLI`, `SC`, `SONAR` are hardcoded as string
literals in the fan-out steps of [automated-release](/workflows/automated-release.md)
(`:763`–`:841`). Adding a new integration target means editing the 1,100-line orchestrator, not
passing config. Custom field IDs (see [shared/jira_common.py](/shared/jira-common.md)) and the
KTLO epic notion are SonarSource-tenant constants baked into ostensibly "reusable" code.

# Recommendation

Push the integration-target list into a structured JSON input (`[{project, description, epic}]`)
parsed inside the step via `fromJSON`. Targets become data, not code — the orchestrator stops
growing a hardcoded step per new target. Won't fully de-Sonar the repo, but caps the growth; see
also [input sprawl](/risks/input-sprawl.md), which this partially addresses.

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 4.2](/../docs/ARCHITECTURE_REVIEW.md)
