---
type: GitHub Action
title: Update Analysis as a Service
description: Updates analyzer versions in sonar-analysis-as-a-service's Gradle version catalog and opens a PR.
resource: https://github.com/SonarSource/release-github-actions/tree/master/update-analysis-as-a-service
tags: [action, sqaa, gradle, pull-request]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Checks out `SonarSource/sonar-analysis-as-a-service`, resolves version keys from `plugin-name`
or `plugin-artifacts`, updates matching entries in `gradle/sonar-plugins.versions.toml` (the
`sonarAnalyzers` catalog, distinct from the default `libs` catalog), and opens a PR via
[create-pull-request](/actions/create-pull-request.md). That catalog file is deliberately left
ownerless in CODEOWNERS so analyzer squads can self-merge their own bumps. Corresponds to the
`sqaa-integration` input of [automated-release](/workflows/automated-release.md), which only
runs when `sqc-integration` is also true, and is skipped silently if the analyzer isn't yet
onboarded to SQAA.

# Schema

| Input | Description | Required |
|---|---|---|
| `release-version` | New analyzer version (e.g. `1.12.0.12345`) | Yes |
| `plugin-name` | Language key used to resolve version entries | see README |

Requires `contents: write` and `pull-requests: write` on `sonar-analysis-as-a-service` for the
`secret-name` Vault token.

# Citations

[1] [update-analysis-as-a-service/README.md](/../update-analysis-as-a-service/README.md)
