---
type: Decision
title: "No user-controlled input interpolated directly into run: blocks"
description: All action.yml inputs must be passed through environment variables rather than interpolated into shell, to prevent script injection.
tags: [decision, security, script-injection]
timestamp: 2026-07-15T00:00:00Z
---

# Decision

`action.yml` files must never interpolate `${{ inputs.x }}` directly inside a `run:` block.
Inputs are passed through environment variables instead:

```yaml
# Bad — script injection risk
run: echo "${{ inputs.branch }}"

# Good
env:
  INPUT_BRANCH: ${{ inputs.branch }}
run: echo "$INPUT_BRANCH"
```

# Why

A crafted input value (e.g. a branch name containing `` `$(...)` ``) interpolated directly into
a `run:` string is executed as shell — classic GitHub Actions script injection. Passing through
`env:` neutralizes it because the value is never re-parsed as shell syntax.

# How to apply

Applies to every new or edited `action.yml`. The related `inputs.x || env.X` +
`if [[ -z ]]` guard pattern (input precedence: explicit input > environment variable > default)
must also stay per-action — see [vault blocks stay per-action](/decisions/vault-blocks-per-action.md).
Removing either pattern during a refactor reintroduces injection risk or breaks precedence.

# Citations

[1] [CLAUDE.md § Security](/../CLAUDE.md)
