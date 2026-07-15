---
type: GitHub Action
title: Release Jira Version
description: Marks a Jira version as released with today's release date.
resource: https://github.com/SonarSource/release-github-actions/tree/master/release-jira-version
tags: [action, jira, version, release]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Finds the Jira version matching `jira-version-name` in the given project and marks it released,
setting the release date to today. Falls back to
[get-jira-version](/actions/get-jira-version.md) for auto-determining the version name. Used in
[automated-release](/workflows/automated-release.md) right after
[publish-github-release](/actions/publish-github-release.md) and before
[create-jira-version](/actions/create-jira-version.md) creates the next version. Has no
"already released?" check — see [risk: no idempotency on mutating steps](/risks/no-idempotency.md).

# Citations

[1] [release-jira-version/README.md](/../release-jira-version/README.md)
