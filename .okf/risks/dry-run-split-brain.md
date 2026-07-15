---
type: Risk
title: Draft/sandbox split-brain is not surfaced honestly
description: use-jira-sandbox and is-draft-release both default true, but GitHub has no sandbox — a "dry run" still publishes a real release/tag.
tags: [risk, observability, dry-run, p1]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

`use-jira-sandbox` defaults **true**; `is-draft-release` defaults **true**. GitHub has no
sandbox concept — a "dry-run" publishes a **real** GitHub release/tag while filing Jira in
sandbox, and the banner still stamps "DRY RUN." GitHub=prod, Jira=sandbox, banner=dry-run: a
split-brain. Conversely, a *successful production* run leaves the GitHub release and analyzer
PRs as **drafts** with nothing screaming "still a draft — go publish it."

# Failure scenario

A DRI runs what they believe is a safe dry-run test and is surprised to find a real (draft)
GitHub release and real analyzer-update PRs exist afterward — because "dry-run" only ever meant
"Jira sandbox," not "no side effects anywhere."

# Recommendation

- Collapse to one `dry-run` input that fans out to Jira sandbox + GitHub draft + PR draft.
- Make the summary banner reflect the *actual* combination in effect, not just the Jira flag; if
  GitHub can't be sandboxed, say so loudly.
- When `is-draft-release=true && !dry-run`, add "⚠️ Draft — not yet public, publish manually."

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 5.2](/../docs/ARCHITECTURE_REVIEW.md)
