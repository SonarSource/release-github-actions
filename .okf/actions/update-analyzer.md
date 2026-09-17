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

The `sonar-`/`-plugin` affixes are optional: `set-sonar-prefix: false` matches
`plugin-name`/`plugin-artifacts` verbatim, for artifacts such as `java-a3s-context-collector`.
The flag is validated — any value other than `true`/`false` exits 1, because falling through to
verbatim matching is silent (the pattern matches nothing, and `create-pull-request` reports an
unchanged build file as a successful no-op, so the release goes green with no version bump).

The build-file rewrite lives in `update_build_gradle.sh` with `test_update_build_gradle.sh`,
following the [update-plugins-deployer](/actions/update-plugins-deployer.md) precedent; the
`unit-tests` job of `test-update-analyzer.yml` runs it. The remaining inline shell is the ticket
prefix check in `Set up environment`.

# Schema

Requires `contents: write` and `pull-requests: write` on `sonar-enterprise` for the
`secret-name` Vault token. Depends on
[vault-action-wrapper@v3](https://github.com/SonarSource/vault-action-wrapper),
`actions/checkout@v4`, and [create-pull-request](/actions/create-pull-request.md).

# Citations

[1] [update-analyzer/README.md](/../update-analyzer/README.md)
