# Risks

Findings from the [2026-07-14 architecture review](../decisions/architecture-review-2026-07.md)
of [automated-release](../workflows/automated-release.md), one concept per finding.

# Reliability (P0/P1)

* [no-idempotency](no-idempotency.md) - no mutating step in the release pipeline is idempotent.
* [unfreeze-on-failure](unfreeze-on-failure.md) - `always()` unfreeze thaws the branch even on a failed release.
* [no-concurrency-guard](no-concurrency-guard.md) - no concurrency guard on the orchestrator.
* [fragile-version-parsing](fragile-version-parsing.md) - untested version parsing feeds every downstream job.

# Testability (P0/P1)

* [orchestrator-untested](orchestrator-untested.md) - the orchestrator's control flow has no test.
* [untested-inline-shell](untested-inline-shell.md) - bash/inline-shell actions with real logic have no unit test.
* [no-contract-test](no-contract-test.md) - no inputs/outputs contract test; silent `@v1` breaking changes ship.

# Maintainability (P1/P2)

* [input-sprawl](input-sprawl.md) - ~50-input sprawl with silent invalid combinations.
* [hardcoded-integration-targets](hardcoded-integration-targets.md) - SonarSource-specific hardcoding makes "reusable" aspirational.
* [internal-v1-violation](internal-v1-violation.md) - a confirmed `@v1` rule violation in `automated-release.yml`.
* [release-yml-fragility](release-yml-fragility.md) - `release.yml`'s force-push + sed rewrite has no post-write assertions.

# Observability (P1/P2)

* [unhelpful-failure-summary](unhelpful-failure-summary.md) - failure summary doesn't say what failed or what to do.
* [dry-run-split-brain](dry-run-split-brain.md) - draft/sandbox split-brain is not surfaced honestly.

# Cleanups / ecosystem context

* [dead-release-lock-stubs](dead-release-lock-stubs.md) - dead stub jobs misrepresent guarantees.
* [stale-releasability-status](stale-releasability-status.md) - the standalone `check-releasability-status` action can read a stale status (not a defect in the orchestrator itself).
