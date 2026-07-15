---
type: GitHub Action
title: Update Rule Metadata
description: Runs the rule-api tooling across all languages to refresh rule metadata and opens a PR with the diff.
resource: https://github.com/SonarSource/release-github-actions/tree/master/update-rule-metadata
tags: [action, rule-api, rspec, pull-request]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Downloads the specified `rule-api` JAR version, discovers directories containing
`sonarpedia.json` (or uses explicitly specified files), runs `rule-api update` in each, and — if
anything changed — opens a PR via [create-pull-request](/actions/create-pull-request.md) plus a
per-language summary. A *skipped* run of this job has previously caused downstream jobs
(including unfreeze) to be silently skipped too — see
[risk: success()/skipped transitive gate](/risks/orchestrator-untested.md).

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `rule-api-version` | Version of the rule-api tooling | see README | |

Requires Java 17, Git, and
[vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for Artifactory
credentials and GitHub token.

# Citations

[1] [update-rule-metadata/README.md](/../update-rule-metadata/README.md)
