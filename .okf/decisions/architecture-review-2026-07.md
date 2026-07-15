---
type: Decision
title: Automated Release Workflow — Architecture Review (2026-07-14)
description: Code review of the analyzer release orchestrator identifying it as an un-idempotent, untested-at-the-orchestrator-level distributed transaction.
resource: https://github.com/SonarSource/release-github-actions/blob/master/docs/ARCHITECTURE_REVIEW.md
tags: [decision, review, reliability, testability]
timestamp: 2026-07-14T00:00:00Z
---

# Overview

Scope: [automated-release](/workflows/automated-release.md) and the ~20 composite actions it
orchestrates. [ide-automated-release](/workflows/ide-automated-release.md) and
[abd-automated-release](/workflows/abd-automated-release.md) are explicitly out of scope.
Method: code read of the orchestrator + actions, cross-checked with internal
incident/ticket/Slack mining and external best-practice research, from both a "release DRI" and
a "workflow maintainer" persona.

# TL;DR

The workflow works and is in daily use, but is a **multi-system distributed transaction with no
idempotency and no recovery model**, tested only by per-action unit tests with **no test of the
orchestrator itself**. Two structural facts explain almost every finding below:

1. No mutating step is idempotent — see [risk: no idempotency](/risks/no-idempotency.md).
2. The orchestrator's control flow (`needs:` + `if:` + output plumbing) is untested — see
   [risk: orchestrator has no test](/risks/orchestrator-untested.md).

# Top 5 highest-leverage fixes

| Priority | Fix | Addresses |
|---|---|---|
| P0 | Idempotency guards + per-failure-point recovery runbook | Half-done releases, duplicate REL tickets, MI1162-class stalls |
| P0 | Orchestrator dry-run mode exercising the full DAG in CI | Untested wiring, GHA-226/227-class `if:`/`success()` footguns |
| P1 | inputs/outputs contract test (golden-file snapshot) per action | Silent `@v1` breaking changes |
| P1 | Fix freeze/unfreeze recovery model — don't `always()` unfreeze after a post-publish failure | MI1162, GHA-227, "branch still frozen" pain |
| P1 | Delete the dead `set-release-lock`/`clear-release-lock` stub jobs and their aspirational comments | Confusion, misrepresented guarantees (GHA-355 scar) |

# Incidents mapped to design gaps

| Incident / ticket | What happened | Root design gap |
|---|---|---|
| MI1162 (RCA, MIM-376) | Release tooling delayed a customer-facing regression fix; recovery needed a manually-built master-unfreeze workflow | No safe recovery path; freeze can be left stuck |
| GHA-226 / GHA-227 | A skipped [update-rule-metadata](/actions/update-rule-metadata.md) silently skipped downstream jobs incl. unfreeze — master left frozen | Untested `if:`/`needs:` control flow; `success()` transitive-skip footgun |
| GHA-355 / June 29 | release-lock rollout broke releases across multiple repos; ripped out | Token model; per-repo fan-out amplifies blast radius; no pre-prod integration test |
| GHA-351 (#170) | A non-existent PyPI version broke every action at install time | No lockfile/verified pin; no `pip install` smoke test |
| check-releasability false-green / over-strict-fail | Reported green on stale Jira-optional failure; later failed on stale optional checks | Historical stale-status read — note: the orchestrator itself now uses the exact commit SHA, so this is ecosystem context, not a defect in `automated-release.yml` |
| gh-action_release v7 / `releaseId` | Automation lagged GitHub's release-immutability migration | Tight coupling to an external action's input contract, no compatibility test |

# All findings

See individual [risk](/risks/index.md) concepts for full detail:
[no idempotency](/risks/no-idempotency.md),
[always() unfreeze on failure](/risks/unfreeze-on-failure.md),
[no concurrency guard](/risks/no-concurrency-guard.md),
[fragile version parsing](/risks/fragile-version-parsing.md),
[orchestrator has no test](/risks/orchestrator-untested.md),
[bash actions with real logic are untested](/risks/untested-inline-shell.md),
[no inputs/outputs contract test](/risks/no-contract-test.md),
[input sprawl with undocumented invalid combinations](/risks/input-sprawl.md),
[SonarSource-specific hardcoding in a "reusable" workflow](/risks/hardcoded-integration-targets.md),
[internal @v1 rule violation](/risks/internal-v1-violation.md),
[release.yml force-push + sed rewrite fragility](/risks/release-yml-fragility.md),
[failure summary lacks actionable detail](/risks/unhelpful-failure-summary.md),
[dry-run/sandbox split-brain not surfaced honestly](/risks/dry-run-split-brain.md),
[dead release-lock stub jobs](/risks/dead-release-lock-stubs.md).

# Prioritized roadmap

- **Phase 0 (days, near-zero risk):** delete dead stub jobs; fix the `@v1` violation + CI
  grep-guard; add `concurrency:` group + per-job `timeout-minutes`; `pip install` smoke matrix +
  `actionlint`.
- **Phase 1 (weeks):** inputs/outputs contract test; orchestrator dry-run mode in CI; fix
  freeze/unfreeze recovery model; failure summary with per-job checklist.
- **Phase 2 (weeks–months):** idempotency on every mutating action; recovery runbook in
  [AUTOMATED_RELEASE.md](/../docs/AUTOMATED_RELEASE.md); unified `dry-run` input; retries with
  backoff on Jira/GitHub 5xx/429.
- **Phase 3 (months):** integration harness against a dummy repo (GHA-247/249); extract
  remaining inline shell to tested `.sh`; structured JSON input for integration targets;
  harden [release.yml](/workflows/release.md).

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md](/../docs/ARCHITECTURE_REVIEW.md)
