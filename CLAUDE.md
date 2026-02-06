# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of reusable GitHub Actions for automating SonarSource analyzer releases. Actions handle Jira integration (tickets, versions, release notes), GitHub releases, cross-repository updates, and Slack notifications.

## Branching

**Critical:** Changes must always be made on a feature branch, never directly on `master`. Before any commit, verify you are not on `master`.
- If on `master`, create a new branch using the format: `ab/<feature-name>` (e.g., `ab/add-slack-notifications`)
- The prefix `ab` represents the developer's initials (first letter of first name + first letter of last name)
- Adapt `<feature-name>` based on the task/prompt (use lowercase, hyphen-separated)
- If already on a feature branch, do not create a new branch—continue working on the current branch

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
