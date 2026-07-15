# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of reusable GitHub Actions for automating SonarSource analyzer releases. Actions handle Jira integration (tickets, versions, release notes), GitHub releases, cross-repository updates, and Slack notifications.

## Knowledge Bundle (.okf)

This repository has an [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog) knowledge
bundle at `.okf/` — concept-per-file notes on every action, workflow, shared module, and
architectural decision, plus a `risks/` directory capturing known reliability/testability gaps
from the 2026-07-14 architecture review. Consult `.okf/index.md` before non-trivial work in this
repo, and keep it in sync: when adding/removing/renaming an action or workflow, or making a
decision worth remembering, update or add the corresponding concept file (see the `okf` skill).

## Jira Project

Related Jira tickets for this project are tracked in the **GHA** (GitHub Automation) project. When available, use the Jira MCP to access ticket details (e.g., `GHA-123`).

## Branching

**Critical:** Changes must always be made on a feature branch, never directly on `master`. Before any commit, verify you are not on `master`.
- If on `master`, create a new branch using the format: `<username-prefix>/<feature-name>` (e.g., `ab/add-slack-notifications`)
- Ask for the prefix to use from the team if unsure (e.g., `ab/` for Antoine B., `js/` for Jean S., etc.)
- Adapt `<feature-name>` based on the task/prompt (use lowercase, hyphen-separated)
- If already on a feature branch, do not create a new branch—continue working on the current branch

## Documentation

**Important:** When making any code changes, check if the related README or documentation needs to be updated. Each action has its own `README.md`, and workflow documentation is in `docs/`. Keep documentation in sync with code changes.

When creating a new action:
- Add a `README.md` to the action's directory documenting inputs, outputs, and usage
- Update the main `README.md` at the repository root to link to the new action

## Testing

**Important:** When making any code changes, always check if there are related tests that need to be updated. Always run the tests after making changes to ensure nothing is broken.

### Run all tests (CI)
Tests run automatically via GitHub Actions. To trigger manually:
- Push to `master` runs `.github/workflows/test-all.yml`
- PRs and pushes to `branch-*` run action-specific test workflows

### Run unit tests locally for a Python action
```bash
cd <action-name>
pip install -r requirements.txt
pip install pytest pytest-cov
python -m pytest test_*.py -v --cov=<module_name> --cov-report=term-missing
```

Example for lock-branch:
```bash
cd lock-branch
pip install -r requirements.txt
pip install pytest pytest-cov
python -m pytest test_lock_branch.py test_notify_slack.py test_utils.py -v
```

### Run a single test
```bash
cd <action-name>
python -m pytest test_<module>.py::TestClassName::test_method_name -v
```

## Architecture

### Action Types
- **Python-based** (Jira integration): `create-jira-release-ticket/`, `create-jira-version/`, `release-jira-version/`, `get-jira-release-notes/`, `create-integration-ticket/`, `update-release-ticket-status/`, `lock-branch/`
- **Bash-based** (GitHub/version operations): `get-release-version/`, `get-jira-version/`, `publish-github-release/`, `check-releasability-status/`, `update-analyzer/`, `update-rule-metadata/`, `notify-slack/`

### Action Structure
Each action follows this pattern:
```
action-name/
├── action.yml           # Composite action definition
├── README.md            # Documentation
├── requirements.txt     # Python deps (if applicable)
├── <script>.py          # Implementation
└── test_<script>.py     # pytest unit tests
```

### Key Patterns
- All actions use `using: "composite"` (not JavaScript/Docker)
- Credentials from `SonarSource/vault-action-wrapper@v3`
- Python actions use Python 3.10
- Error output via stderr (`eprint()`), values via stdout to `$GITHUB_OUTPUT`
- Input precedence: explicit input > environment variable > default

### Jira Custom Field IDs

Defined in `shared/jira_common.py` as the `CUSTOM_FIELDS` dict — single source of truth:
```python
customfield_10146  # SHORT_DESCRIPTION
customfield_10145  # LINK_TO_RELEASE_NOTES
customfield_10147  # DOCUMENTATION_STATUS
customfield_11263  # RULE_PROPS_CHANGED
customfield_11264  # SONARLINT_CHANGELOG
```

### Version Formats
- Release version: `X.Y.Z.buildNumber` (e.g., `11.44.2.12345`)
- Jira version: `X.Y` or `X.Y.Z` (trailing `.0` removed)

## Security

When modifying `action.yml` files, never interpolate user-controlled inputs directly in `run:` blocks. Pass them through environment variables:

```yaml
# Bad - script injection risk
run: echo "${{ inputs.branch }}"

# Good - use env vars
env:
  INPUT_BRANCH: ${{ inputs.branch }}
run: echo "$INPUT_BRANCH"
```

### Pinning External Actions

**Important:** All GitHub Actions from outside the SonarSource organization must be pinned to a full commit SHA (not a tag). Add a comment with the version number for readability.

```yaml
# Bad - using tag
- uses: actions/checkout@v4

# Good - pinned to commit SHA with version comment
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

This prevents tag mutation attacks where a malicious actor could change what code a tag points to.

## Golden Architecture

Every action is a self-contained composite invoked as `SonarSource/release-github-actions/<action>@v1`. Consumers pin `@v1`; `release.yml` fast-forwards it on release. **Internal refactors are transparent; changing an action's `inputs:`/`outputs:` is a breaking change — treat the input/output surface as a public API.**

### Internal refs: `@master` on master, frozen SHA on `v1`

Source on `master` references sibling actions as `@master` (e.g. `uses: SonarSource/release-github-actions/get-release-version@master`). This means any test run from `master` always exercises the latest code across all sub-actions.

When `release.yml` fast-forwards the `v1` branch to a release tag, it then rewrites every `@master` ref in `action.yml` files and `automated-release.yml` to the exact release commit SHA, then commits. So `v1` is a self-consistent frozen snapshot — no floating refs.

**Do not write new internal `uses:` as `@v1` anywhere in this repo** — this applies to `action.yml` files, `automated-release.yml`, and test workflows (`.github/workflows/test-*.yml`). Always use `@master`; the release workflow handles pinning automatically. This includes string-match assertions in test scripts (e.g. `grep -q "...@master"`).

### Shared Python code

Common helpers live in `shared/` (`eprint`, `get_jira_instance`, `CUSTOM_FIELDS`). Import via:
```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))
from jira_common import eprint, get_jira_instance, CUSTOM_FIELDS
```

**Do NOT package `shared/` with `pyproject.toml` / `pip install -e .`** — that forces an install step into every consumer workflow. `@v1` checks out the whole repo, so `../shared` is already on disk at runtime. (See reverted commit `ad8a663`.)

Rule: if a helper exists in ≥2 actions and you need a third copy, put it in `shared/` with a test in `shared/test_*.py` instead.

### Jira URL resolution

Jira URL selection lives entirely in `shared/jira_common.py` (`JIRA_URL_PROD`, `JIRA_URL_SANDBOX`, `get_jira_url()`). **No `action.yml` constructs a URL.**

All `action.yml` files pass the sandbox flag through as an env var and forward it to the script:
```yaml
env:
  USE_SANDBOX: ${{ inputs.use-jira-sandbox || env.USE_JIRA_SANDBOX }}
run: |
  python script.py --use-sandbox="$USE_SANDBOX"
```

Scripts call `get_jira_instance(args.use_sandbox)` — URL resolution happens inside. Only scripts that need the URL string directly (e.g. for constructing issue links) also import `get_jira_url`. A future domain change is one edit in `shared/jira_common.py`.

### Things that LOOK like duplication but MUST stay per-action

- **Vault credential blocks.** A nested composite can only export secrets via `$GITHUB_ENV`, exposing them to every later step in the job. Keep the vault block inline per action.
- **`inputs.x || env.X` + `if [[ -z ]]` guard.** Mandated by the Security section above (no user input interpolated into `run:`) and the input-precedence rule. Removing it reintroduces injection risk.
- **Orchestrator fan-outs** (integration-ticket steps, analyzer steps in `automated-release.yml`). They surface *named* job outputs consumed by downstream jobs, and reference same-job step outputs; a `matrix` job cannot expose per-cell named outputs. Keep explicit steps.
- **setup-python + `pip install` preamble.** Byte-identical across actions and kept pinned by `update-action-versions.yml`. Don't wrap it in a composite for line count.

### Conventions for every new action

- `using: "composite"`; Python 3.10; use the canonical JIRA URL expression above.
- Outputs via stdout `key=value` → `action.yml` redirects `>> $GITHUB_OUTPUT`; diagnostics via `eprint()` to stderr.
- External (non-SonarSource) actions pinned to a full commit SHA with a version comment.
- New action → `README.md` in its directory + link from root `README.md`.
