---
type: Risk
title: No inputs/outputs contract test — silent @v1 breaking changes ship
description: Nothing enforces that an action's inputs/outputs are treated as the public API CLAUDE.md declares them to be.
tags: [risk, testability, breaking-change, golden-architecture, p1]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

[CLAUDE.md](/../CLAUDE.md) declares an action's `inputs:`/`outputs:` a public API — see
[Golden Architecture](/decisions/golden-architecture.md). **Nothing enforces this.** Rename an
input, change a default, drop an output — CI stays green,
[release.yml](/workflows/release.md) cuts a `v1` snapshot anyway, and the next squad release
fails mid-release, after the branch is frozen and the GitHub release is published.

# Failure scenario

A refactor renames an input on `master` for internal clarity, forgetting a consumer still
passes the old name via `@v1`. The rename ships in the next release cut. Weeks later a squad
triggers their release; the input silently doesn't apply (or the workflow errors) partway
through the DAG, with the branch already frozen.

# Recommendation

A golden-file contract test: dump each `action.yml`'s input/output names + `required` +
`default` to a checked-in snapshot; CI diffs and fails on change, forcing a conscious "yes, this
is breaking" acknowledgment and a major-version bump conversation. Small script, catches the
highest-consequence mistake class in the repo.

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 3.3](/../docs/ARCHITECTURE_REVIEW.md)
[2] [CLAUDE.md § Golden Architecture](/../CLAUDE.md)
