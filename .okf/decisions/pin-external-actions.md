---
type: Decision
title: External actions pinned to full commit SHA
description: Every non-SonarSource GitHub Action reference must be pinned to a full commit SHA (with a version comment), never a mutable tag.
tags: [decision, security, supply-chain]
timestamp: 2026-07-15T00:00:00Z
---

# Decision

```yaml
# Bad
- uses: actions/checkout@v4

# Good
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

# Why

Prevents tag-mutation supply-chain attacks, where a compromised or malicious maintainer moves a
tag to point at different code without publishing a new version number. The March 2025
`tj-actions/changed-files` tag-hijack (cited in the
[architecture review](/decisions/architecture-review-2026-07.md) §6) is the cautionary tale
motivating enforcement, not just documentation, of this rule.

# How to apply

Applies to every action reference outside the `SonarSource` GitHub organization. The rule
exists and is followed today, but nothing in CI enforces it — the review recommends adopting
`zizmor` or OpenSSF Scorecard so drift fails the build instead of relying on review vigilance.

# Citations

[1] [CLAUDE.md § Pinning External Actions](/../CLAUDE.md)
[2] [docs/ARCHITECTURE_REVIEW.md § 6](/../docs/ARCHITECTURE_REVIEW.md)
