# Contributing

## Branching

Never commit or push directly to `master`. Always work on a feature branch named
`<username-prefix>/<feature-name>` (lowercase, hyphen-separated), e.g. `nw/add-slack-notifications`.
Ask the team for your prefix if you don't have one yet.

PRs are normally tied to a Jira ticket (project **GHA**) referenced in the PR title. If there's
no ticket, the `.github/PULL_REQUEST_TEMPLATE.md` explains how to let Jira automation create one.

## Repository structure

Each action is a self-contained composite action:

```
action-name/
├── action.yml           # composite action definition
├── README.md            # inputs, outputs, usage
├── requirements.txt     # Python deps (if applicable)
├── <script>.py          # implementation
└── test_<script>.py     # pytest unit tests
```

See `lock-branch/` for a working example. Python helpers shared by ≥2 actions belong in
`shared/`, not duplicated per-action — see `shared/jira_common.py`.

When adding a new action:
1. Follow the structure above.
2. Add a `README.md` documenting inputs/outputs/usage.
3. Link it from the table in the root `README.md`.
4. Add a `test-<action-name>.yml` CI workflow (see "Testing in CI" below) and wire it into
   `test-all.yml`.

Before writing or editing `action.yml`, read the Security and Golden Architecture sections of
[CLAUDE.md](CLAUDE.md) — in particular: never interpolate `${{ inputs.x }}` directly into a
`run:` block (pass it through `env:` instead), and pin non-SonarSource actions to a full commit
SHA with a version comment.

## Testing locally

Each action is tested independently — there's no root test runner or Makefile.

```bash
cd <action-name>
pip install -r requirements.txt
pip install pytest pytest-cov
python -m pytest test_*.py -v --cov=<module_name> --cov-report=term-missing
```

Run a single test:

```bash
python -m pytest test_<module>.py::TestClassName::test_method_name -v
```

`shared/` and `test-fixtures/jira/` follow the same pattern.

## Testing in CI

Every action has its own `test-<action-name>.yml` workflow. The standard trigger shape:

```yaml
on:
  workflow_call:
  pull_request:
    paths:
      - '<action-name>/**'
      - '.github/workflows/test-<action-name>.yml'
  push:
    branches:
      - branch-*
    paths:
      - '<action-name>/**'
      - '.github/workflows/test-<action-name>.yml'
  workflow_dispatch:
```

This means a PR touching an action's directory (or its own test workflow) automatically runs
that action's tests. `push` to a `branch-*`-named branch does the same. `test-all.yml` fans out
to a subset of these workflows via `workflow_call` on every push to `master`, and can also be
triggered manually.

A few older test workflows deviate slightly from this shape (e.g. broader `push` branch filters)
— match the pattern of a recently-added action's test workflow when in doubt.

## Releasing this repository

External consumers pin actions to `SonarSource/release-github-actions/<action>@v1`. On `master`,
every internal reference between sibling actions/workflows uses `@master` instead — never write
a new internal reference as `@v1`, including in test-script string assertions.

An action's `inputs:`/`outputs:` are its public API — changing them is a breaking change.

Publishing a GitHub Release on this repository triggers `.github/workflows/release.yml`
(`on: release: types: [published]`), which fast-forwards the `v<major>` branch (e.g. `v1`) to
the release tag and rewrites every internal `@master` reference to the release commit SHA. No
separate manual step is needed to update `v1` after a release is published.

This is unrelated to `automated-release.yml`, the reusable workflow this repo *provides* for
releasing an analyzer — see [docs/AUTOMATED_RELEASE.md](docs/AUTOMATED_RELEASE.md) for that.

## Further reading

- [docs/AUTOMATED_RELEASE.md](docs/AUTOMATED_RELEASE.md) — reference for the analyzer release
  workflow this repo provides.
- [docs/ARCHITECTURE_REVIEW.md](docs/ARCHITECTURE_REVIEW.md) — known architecture and testing
  gaps, for anyone doing deeper work on the orchestrator.
- [.okf/index.md](.okf/index.md) — concept-per-file knowledge bundle covering every action,
  workflow, and architectural decision in this repo.
