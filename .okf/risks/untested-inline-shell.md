---
type: Risk
title: Bash/inline-shell actions with real logic have no unit test
description: The Python-vs-Bash test split is arbitrary — logic extracted to a .sh got tested, logic left inline in action.yml did not.
tags: [risk, testability, bash, p1]
timestamp: 2026-07-14T00:00:00Z
---

# Observation

Where logic was extracted to a `.sh` file, it has a test:
[bump-version](/actions/bump-version.md),
[update-plugins-deployer](/actions/update-plugins-deployer.md),
[update-rule-metadata](/actions/update-rule-metadata.md),
[update-analyzer](/actions/update-analyzer.md) (`update_build_gradle.sh` +
`test_update_build_gradle.sh`, extracted 2026-09-09). Where it stayed inline in `action.yml`,
it has none:

- [get-release-version](/actions/get-release-version.md) — feeds every downstream job, no test
  (see [fragile version parsing](/risks/fragile-version-parsing.md)).
- [get-jira-version](/actions/get-jira-version.md),
  [publish-github-release](/actions/publish-github-release.md),
  [check-releasability-status](/actions/check-releasability-status.md) — inline shell, no unit
  test.

The action-level jobs of `test-update-analyzer.yml` (and its peers) still *expect the action to
fail* on missing vault access — a linter with extra steps, not a behavior test.
`test-update-analyzer.yml` now has a `unit-tests` job alongside them.

# Recommendation

Enforce the rule the repo already half-follows: inline shell longer than ~10 lines must be
extracted to a `.sh` with a `test_*.sh` (bats or plain assert).
[update-analyzer](/actions/update-analyzer.md) is done;
[get-release-version](/actions/get-release-version.md) is now the top remaining priority.

# Citations

[1] [docs/ARCHITECTURE_REVIEW.md § 3.2](/../docs/ARCHITECTURE_REVIEW.md)
