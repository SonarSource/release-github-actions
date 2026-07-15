---
type: Reusable Workflow
title: Automated Release (analyzer path)
description: Orchestrates the full end-to-end analyzer release across Jira, GitHub, and downstream integration repos.
resource: https://github.com/SonarSource/release-github-actions/blob/master/.github/workflows/automated-release.yml
tags: [workflow, release, orchestrator, jira, github-release]
timestamp: 2026-07-15T00:00:00Z
---

# Overview

~1,100-line reusable `workflow_call` workflow, ~50 inputs, ~15 jobs wired by hand-written
`needs:` + `if:` guards. Triggered manually via `workflow_dispatch` from an analyzer repo. This
is the generic **analyzer** release path — distinct from
[ide-automated-release](/workflows/ide-automated-release.md) (DevEx/IDE) and
[abd-automated-release](/workflows/abd-automated-release.md), which are separate paths.

# Job DAG

```
disable-auto-merge (if bump-version: true)
        │
        ▼
  freeze-branch (optional, lock_branch via lock-branch action)
        │
        ▼
  check-releasability (SonarSource/gh-action_releasability@v3, exact commit SHA)
        │
        ▼
  prepare-release (get-release-version, get-jira-version, get-jira-release-notes)
        │
   ┌────┴─────────────────────┐
   ▼                          ▼
create-release-ticket   publish-github-release
   │                          │
   └───────────┬──────────────┘
               ▼
          UNFREEZE branch
               │
               ▼
        release-in-jira (release-jira-version, create-jira-version for next)
               │
       ┌───────┴────────────────────┐
       ▼                            ▼
  bump-version                create-integration-tickets (SLVS/SLE/SLI/SQS/SQC/...)
  (opens version-bump PR)            │
                                     ▼
                            update-analyzer PRs (sonar-enterprise, sonar-plugins-deployer)
```

Actions composed: [get-release-version](/actions/get-release-version.md),
[get-jira-version](/actions/get-jira-version.md),
[get-jira-release-notes](/actions/get-jira-release-notes.md),
[create-jira-release-ticket](/actions/create-jira-release-ticket.md),
[publish-github-release](/actions/publish-github-release.md),
[release-jira-version](/actions/release-jira-version.md),
[create-integration-ticket](/actions/create-integration-ticket.md),
[update-analyzer](/actions/update-analyzer.md),
[update-plugins-deployer](/actions/update-plugins-deployer.md),
[update-analysis-as-a-service](/actions/update-analysis-as-a-service.md),
[update-release-ticket-status](/actions/update-release-ticket-status.md),
[bump-version](/actions/bump-version.md), and branch lock/unlock via
[lock-branch](/actions/lock-branch.md) (external:
`SonarSource/gh-action_releasability@v3`, `sonarsource/gh-action-lt-backlog/ToggleLockBranch`).

# Schema

Key inputs (selected — full list in the action README): `jira-project-key`, `project-name`,
`plugin-name`, `pm-email`, `short-description`, `rule-props-changed`, `branch`, `new-version`,
`use-jira-sandbox` (default `true`), `is-draft-release` (default `true`), `freeze-branch`
(default `true`), `check-releasability` (default `true`), `sqs-integration` /
`sqc-integration` (default `true`), `sqaa-integration` (runs only when `sqc-integration` is
also true; silently skipped if not onboarded), `create-slvs-ticket` / `create-slvscode-ticket` /
`create-sle-ticket` / `create-sli-ticket` / `create-cli-ticket` (default `false`), `verbose`
(default `false`).

Outputs: `new-version` (Jira version name), `sqaa-pull-request-url`.

# Notes

- **Auto-merge sweep**: when `bump-version: true`, strips auto-merge from all open PRs at
  release start, to reduce the race window where a PR could merge before the version-bump PR
  opens. Best-effort — see the [release-lock gate](/workflows/release-lock.md) for the guard of
  last resort.
- **Freeze window ends early**: the branch unfreezes right after
  [publish-github-release](/actions/publish-github-release.md), *before* the version-bump PR is
  created — see [release-lock](/workflows/release-lock.md) for how that gap is closed.
- This workflow has been the subject of an [architecture review](/decisions/architecture-review-2026-07.md)
  identifying reliability, testability, and observability gaps — see the
  [risks](/risks/index.md) directory.

# Citations

[1] [README.md](/../README.md)
[2] [docs/AUTOMATED_RELEASE.md](/../docs/AUTOMATED_RELEASE.md)
[3] [docs/ARCHITECTURE_REVIEW.md](/../docs/ARCHITECTURE_REVIEW.md)
