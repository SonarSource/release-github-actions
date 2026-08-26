---
type: GitHub Action
title: Update Rule Metadata
description: Runs the rule-api tooling across all languages to refresh rule metadata and opens a PR with the diff.
resource: https://github.com/SonarSource/release-github-actions/tree/master/update-rule-metadata
tags: [action, rule-api, rspec, pull-request]
timestamp: 2026-08-26T00:00:00Z
---

# Overview

Downloads the specified `rule-api` JAR version, discovers directories containing
`sonarpedia.json` (or uses explicitly specified files), runs `rule-api update` in each, and — if
anything changed — opens a PR via [create-pull-request](/actions/create-pull-request.md) plus a
per-language summary. A *skipped* run of this job has previously caused downstream jobs
(including unfreeze) to be silently skipped too — see
[risk: success()/skipped transitive gate](/risks/orchestrator-untested.md).

The generated PR carries **no label by default** — the `labels` input is the only source of
labels (GHA-418). Consumers use it to steer CI on the bot PR: Cloud Security analyzers run the
whole PVF on every pull request unless it carries `skip-pvf`. The orchestrator
[automated-release](/workflows/automated-release.md) exposes this as `rule-metadata-pr-labels`.
Before GHA-418 the README wrongly claimed a `skip-qa` label was applied automatically.

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `rule-api-version` | Version of the rule-api tooling | see README | |
| `labels` | Comma/newline-separated labels for the generated PR | No | (none) |

Requires Java 17, Git, and
[vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for Artifactory
credentials and GitHub token.

# Citations

[1] [update-rule-metadata/README.md](/../update-rule-metadata/README.md)
