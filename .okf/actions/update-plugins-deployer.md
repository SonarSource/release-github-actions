---
type: GitHub Action
title: Update Plugins Deployer
description: Bumps a plugin version anchor in sonar-plugins-deployer's plugins.yaml and opens a PR.
resource: https://github.com/SonarSource/release-github-actions/tree/master/update-plugins-deployer
tags: [action, sqc, sonar-plugins-deployer, pull-request]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Validates the ticket key starts with `SC-`, checks out `plugins.yaml` from
`sonar-plugins-deployer`, computes the anchor key from `plugin-name` (strips `-enterprise`
suffix; maps `csharp`/`vbnet` → `dotnet`; the `sonar-` prefix in anchor keys is optional per
`8b28303`), updates the version anchor in the `versions:` block (all `plugins:` aliases pick up
the change automatically), and opens a PR via
[create-pull-request](/actions/create-pull-request.md). Corresponds to the `sqc-integration`
fan-out of [automated-release](/workflows/automated-release.md).

# Schema

| Input | Description | Required |
|---|---|---|
| `release-version` | New version (e.g. `1.12.0.12345`) | Yes |
| `ticket-key` | Jira ticket key, must start with `SC-` | Yes |

Requires `contents: write` and `pull-requests: write` on `sonar-plugins-deployer` for the
`secret-name` Vault token.

# Citations

[1] [update-plugins-deployer/README.md](/../update-plugins-deployer/README.md)
