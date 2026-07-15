---
type: GitHub Action
title: Sonar Update Center Release
description: Opens a PR in sonar-update-center-properties adding a new release entry to a .properties file.
resource: https://github.com/SonarSource/release-github-actions/tree/master/sonar-update-center-release
tags: [action, update-center, pull-request]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Runs an in-place Python update (`update.py`) of a target `.properties` file in
`sonar-update-center-properties`, adding a new version/date/description/changelog-URL entry,
then opens a pull request. Requires the `release-automation` Vault token to include
`contents: write` and `pull-requests: write` for that repository.

# Schema

| Input | Description | Required |
|---|---|---|
| `file` | The `.properties` file to update | Yes |
| `version` | New version string (e.g. `5.5.0.6356`) | Yes |
| `description` | Description field of the new entry | Yes |
| `date` | Date field; defaults to today | No |
| `changelog-url` | Changelog URL field | Yes |

# Citations

[1] [sonar-update-center-release/README.md](/../sonar-update-center-release/README.md)
