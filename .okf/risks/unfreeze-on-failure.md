---
type: Risk
title: unfreeze-branch uses always() — thaws the branch even on a failed release
description: The branch unlocks unconditionally after the publish step, opening it to other merges exactly when the release is in its most fragile, half-done state.
tags: [risk, reliability, freeze-branch, p1]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

`automated-release.yml:603` — `if: ${{ always() && inputs.freeze-branch }}`. If
[publish-github-release](/actions/publish-github-release.md) fails, the branch still unfreezes
via [lock-branch](/actions/lock-branch.md). Combined with
[no idempotency](/risks/no-idempotency.md), this produces a half-published release **and** an
open branch that other developers' PRs immediately merge into — the one guardrail (freeze)
releases exactly when the branch most needs to stay held for cleanup.

This is also the mechanism behind GHA-227: the transitive-skip bug meant unfreeze was *skipped*
(master left frozen) — the opposite failure, same root cause: freeze lifecycle is driven by
fragile job-graph semantics (`needs:`/`if:`), not an explicit state machine.

# Failure scenario

`publish-github-release` fails after freeze. `always()` fires the unfreeze anyway. A developer's
unrelated PR merges into the now-open, half-released branch before anyone notices the release is
broken.

# Recommendation

Split the unfreeze decision: unfreeze on success or early abort (nothing published yet); keep
frozen on failure *after* publish, with a loud Slack line — "⚠️ branch left frozen — release
reached an inconsistent state, manual cleanup required." Make freeze/unfreeze itself idempotent
and retried (a bare API blip on unfreeze currently just reds the job with no retry — the MI1162
"stuck frozen" shape).

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 2.2](/../docs/ARCHITECTURE_REVIEW.md)
