# Workflows

* [automated-release](automated-release.md) - the analyzer release orchestrator; the main entry point for this repo.
* [ide-automated-release](ide-automated-release.md) - the DevEx/IDE (SonarLint) release orchestrator.
* [abd-automated-release](abd-automated-release.md) - a distinct release-orchestration variant.
* [release-lock](release-lock.md) - required-status-check gate that blocks other PRs while a version-bump PR is open.
* [release](release.md) - this repo's own release workflow; fast-forwards `v1` and pins internal refs.
