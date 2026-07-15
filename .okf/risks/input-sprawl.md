---
type: Risk
title: ~50-input sprawl with silent invalid combinations
description: Mutually coupled inputs on automated-release have undocumented valid combinations, some of which disagree with the schema.
tags: [risk, maintainability, inputs, p1]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

[automated-release](/workflows/automated-release.md) has ~50 inputs, many coupled through `if:`
expressions, with valid combinations undocumented and unenforced:

- `sqaa-integration: true` with `sqc-integration: false` → the job is silently skipped (`:946`).
- `sqc-plugins-deployer-integration` is a **deprecated no-op** still in the schema with
  `default: true` — appears in every dispatch form and setup doc.
- `rule-props-changed` is a required *string* `"true"`/`"false"` compared with `== 'true'`
  (`:537`): pass a real boolean or `"True"` and it silently maps to "No."
- `new-version` is documented **required** in [AUTOMATED_RELEASE.md](/../docs/AUTOMATED_RELEASE.md)
  but is `required: false` in the YAML (`:91`) — omitting it changes what Jira creates next, and
  **docs and schema disagree**.

# Recommendation

1. Prune deprecated inputs (`sqc-plugins-deployer-integration`); make booleans real booleans.
2. Reconcile docs vs. schema on `new-version`.
3. Collapse the integration-target scalars into one structured input — see
   [hardcoded integration targets](/risks/hardcoded-integration-targets.md).
4. Validate mutually-exclusive/invalid combinations early with a clear error instead of silently
   skipping jobs.

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 4.1](/../docs/ARCHITECTURE_REVIEW.md)
