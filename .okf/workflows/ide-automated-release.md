---
type: Reusable Workflow
title: IDE Automated Release (DevEx path)
description: Reusable release orchestration for SonarQube for IDE / Development Experience projects, separate from the analyzer path.
resource: https://github.com/SonarSource/release-github-actions/blob/master/.github/workflows/ide-automated-release.yml
tags: [workflow, release, orchestrator, devex, sonarqube-for-ide]
timestamp: 2026-08-05T00:00:00Z
---

# Overview

Reusable `workflow_call` workflow for Development Experience projects (SonarLint Core,
SonarQube for IntelliJ, SonarQube for Eclipse, SonarQube for VS Code, etc.),
set up via the
`devex-release-setup` Claude Code skill. Explicitly out of scope for the
[architecture review](/decisions/architecture-review-2026-07.md), which covers only the
analyzer path ([automated-release](/workflows/automated-release.md)). Roughly a fifth the size
of the analyzer orchestrator (~240 lines vs. ~1,100).

# Citations

[1] [README.md](/../README.md)
