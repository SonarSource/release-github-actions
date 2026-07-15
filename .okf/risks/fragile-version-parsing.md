---
type: Risk
title: Fragile, untested release-version parsing feeds every downstream job
description: get-release-version parses the version out of a human-readable repox status description with no unit test guarding the format.
tags: [risk, reliability, testability, get-release-version, p2]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

[get-release-version](/actions/get-release-version.md) parses the release version out of a
human-readable repox commit-status **description** via
`... | .description | split("'")[1]` — inline `jq` in `action.yml`, no unit test. Every
downstream job in [automated-release](/workflows/automated-release.md) keys off this output.

# Failure scenario

The repox status text format changes upstream (a wording tweak, a punctuation change). Every
release breaks with a cryptic "Could not extract release version," and nothing caught it before
a real release run.

# Recommendation

Extract the parse into a tested `get_release_version.sh` (or `.py`) with `test_*` cases for the
known status-text formats and a clear failure message; assert the shape (`X.Y.Z.build`).

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 2.6](/../docs/ARCHITECTURE_REVIEW.md)
