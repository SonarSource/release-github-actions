---
type: GitHub Action
title: Update Analyzer
description: Bumps an analyzer version in sonar-enterprise's build.gradle and opens a PR.
resource: https://github.com/SonarSource/release-github-actions/tree/master/update-analyzer
tags: [action, sqs, sonar-enterprise, gradle, pull-request]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Checks out `sonar-enterprise`, updates the analyzer version in `build.gradle` via `sed`, and
opens a PR through [create-pull-request](/actions/create-pull-request.md). Corresponds to the
`sqs-integration` fan-out of [automated-release](/workflows/automated-release.md). Logic that
previously called into `sonarcloud-core` was removed (see `d09b37a`).

Inline shell (~121 lines) with no unit test — see
[risk: bash actions with real logic are untested](/risks/untested-inline-shell.md).

# Schema

Requires `contents: write` and `pull-requests: write` on `sonar-enterprise` for the
`secret-name` Vault token. Depends on
[vault-action-wrapper@v3](https://github.com/SonarSource/vault-action-wrapper),
`actions/checkout@v4`, and [create-pull-request](/actions/create-pull-request.md).

# Citations

[1] [update-analyzer/README.md](/../update-analyzer/README.md)
