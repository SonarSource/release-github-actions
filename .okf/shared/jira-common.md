---
type: Shared Module
title: shared/jira_common.py
description: Single source of truth for Jira URL resolution, custom field IDs, and Jira client auth used by every Jira-integration action.
resource: https://github.com/SonarSource/release-github-actions/blob/master/shared/jira_common.py
tags: [shared, jira, python]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

Imported by each Python action via a `sys.path` insert (works because `@v1` checks out the
whole repo, so `../shared` is on disk at runtime). Deliberately **not** packaged with
`pyproject.toml` / `pip install -e .` — that would force an install step into every consumer
workflow (a prior attempt was reverted, commit `ad8a663`).

Rule of thumb from [CLAUDE.md](/../CLAUDE.md): if a helper exists in ≥2 actions and a third copy
is needed, it belongs here with a `test_*.py`.

# Schema

| Symbol | Purpose |
|---|---|
| `JIRA_URL_PROD` / `JIRA_URL_SANDBOX` | The two Jira base URLs |
| `get_jira_url(use_sandbox)` | Resolves the URL; accepts bool, `'true'`/`'false'` string, or `None` |
| `get_jira_instance(use_sandbox)` | Authenticates via `JIRA_USER`/`JIRA_TOKEN` env vars, `sys.exit(1)` on failure |
| `eprint(*args, **kwargs)` | Prints to stderr — keeps diagnostics separate from stdout, which carries the result piped to `$GITHUB_OUTPUT` |
| `CUSTOM_FIELDS` | Dict of Jira custom field IDs (also documented in CLAUDE.md) |

`CUSTOM_FIELDS` values: `SHORT_DESCRIPTION` → `customfield_10146`,
`LINK_TO_RELEASE_NOTES` → `customfield_10145`, `DOCUMENTATION_STATUS` → `customfield_10147`,
`RULE_PROPS_CHANGED` → `customfield_11263`, `SONARLINT_CHANGELOG` → `customfield_11264`.

Used by [create-jira-release-ticket](/actions/create-jira-release-ticket.md),
[create-jira-version](/actions/create-jira-version.md),
[create-integration-ticket](/actions/create-integration-ticket.md),
[get-jira-release-notes](/actions/get-jira-release-notes.md),
[release-jira-version](/actions/release-jira-version.md),
[resolve-ktlo-epic](/actions/resolve-ktlo-epic.md), and
[update-release-ticket-status](/actions/update-release-ticket-status.md). URL resolution lives
**only** here — no `action.yml` constructs a Jira URL directly; a future domain change is one
edit in this file.

# Citations

[1] [shared/jira_common.py](/../shared/jira_common.py)
[2] [CLAUDE.md § Jira URL resolution](/../CLAUDE.md)
