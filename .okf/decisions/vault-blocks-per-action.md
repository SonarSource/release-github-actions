---
type: Decision
title: Vault credential blocks stay inline per action
description: Vault secret retrieval is duplicated in every action.yml rather than factored into a shared composite, to avoid leaking secrets via $GITHUB_ENV.
tags: [decision, security, secrets, vault]
timestamp: 2026-07-15T00:00:00Z
---

# Decision

Every action that needs Vault-sourced credentials (Jira tokens, Slack tokens, GitHub PAT for
cross-repo PRs) repeats the `SonarSource/vault-action-wrapper@v3` block inline, rather than
factoring it into a shared/nested composite action.

# Why

A nested composite action can only export secrets to the calling job via `$GITHUB_ENV` — which
exposes the secret to **every later step in that job**, not just the step that needed it. This
is a strictly wider blast radius than keeping the vault call inline where the secret is consumed.
This is confirmed independently by the external best-practice research in the
[architecture review](/decisions/architecture-review-2026-07.md) §6 as one of the things this
repo already gets right.

# How to apply

This looks like duplication (per [CLAUDE.md](/../CLAUDE.md) it's called out explicitly as
something that *looks like* duplication but must stay per-action) — do not "clean it up" into a
shared composite during a refactor. The same non-negotiable applies to the
`inputs.x || env.X` + `if [[ -z ]]` input-precedence guard pattern, mandated by
[no user-controlled input in run: blocks](/decisions/env-var-injection-guard.md).

# Citations

[1] [CLAUDE.md § Things that LOOK like duplication but MUST stay per-action](/../CLAUDE.md)
[2] [docs/ARCHITECTURE_REVIEW.md § 6](/../docs/ARCHITECTURE_REVIEW.md)
