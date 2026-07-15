---
type: GitHub Action
title: Bump Project Version
description: Updates the version in Maven and Gradle files across the repository, opening a pull request with the change.
resource: https://github.com/SonarSource/release-github-actions/tree/master/bump-version
tags: [action, version, maven, gradle, pull-request]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Composite action that rewrites the project version (without `-SNAPSHOT`) in Maven or Gradle
build files, optionally excluding specific modules, and opens a pull request with the change.
Used as the `bump-version` step in [automated-release](/workflows/automated-release.md) to
prepare the next development iteration after a release.

# Schema

| Input | Description | Required | Default |
|---|---|---|---|
| `version` | The new version (without `-SNAPSHOT`) | Yes | |
| `token` | GitHub token for PR creation | No | |
| `excluded-modules` | Comma-separated modules to exclude | No | |
| `base-branch` | Base branch for the pull request | No | `master` |
| `pr-labels` | Comma-separated labels for the pull request | No | |
| `tool` | Version bumping tool (`maven`, or empty for shell-based) | No | |

| Output | Description |
|---|---|
| `pull-request-url` | URL of the created pull request |

# Citations

[1] [bump-version/README.md](/../bump-version/README.md)
