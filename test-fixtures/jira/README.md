# Jira Test Fixtures

Reusable Python scripts for setting up and tearing down Jira sandbox state for integration tests.

## Scripts

### `setup.py`

Creates a test version and sample issues in a Jira sandbox project.

```bash
python setup.py \
  --project-key SONARIAC \
  --run-id "$GITHUB_RUN_ID" \
  --jira-url "https://sonarsource-sandbox-608.atlassian.net/"
```

**Output** (JSON to stdout):
```json
{
  "version_id": "12345",
  "version_name": "99.12345678",
  "issue_keys": ["SONARIAC-100", "SONARIAC-101", "SONARIAC-102"]
}
```

Creates:
- 1 version named `99.<run_id>`
- 3 issues (Bug, Feature, Maintenance) linked to the version via `fixVersion`

### `cleanup.py`

Deletes test fixtures. Idempotent — succeeds even if resources are already deleted.

```bash
# From inline arguments:
python cleanup.py \
  --jira-url "https://sonarsource-sandbox-608.atlassian.net/" \
  --version-id 12345 \
  --issue-keys "SONARIAC-100,SONARIAC-101,SONARIAC-102"

# From a state file (output of setup.py):
python cleanup.py \
  --jira-url "https://sonarsource-sandbox-608.atlassian.net/" \
  --state-file /tmp/setup-state.json
```

## Usage in GitHub Actions Workflows

```yaml
- name: Get Jira Credentials from Vault
  uses: SonarSource/vault-action-wrapper@v3
  id: secrets
  with:
    secrets: |
      development/kv/data/jira user | JIRA_USER;
      development/kv/data/jira token | JIRA_TOKEN;

- name: Set up Python
  uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
  with:
    python-version: '3.10'

- name: Install fixture dependencies
  run: pip install -r test-fixtures/jira/requirements.txt

- name: Create Jira test fixtures
  id: fixtures
  env:
    JIRA_USER: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_USER }}
    JIRA_TOKEN: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_TOKEN }}
  run: |
    STATE=$(python test-fixtures/jira/setup.py \
      --project-key SONARIAC \
      --run-id "${{ github.run_id }}" \
      --jira-url "https://sonarsource-sandbox-608.atlassian.net/")
    echo "$STATE" > /tmp/jira-fixtures.json
    echo "version_name=$(echo "$STATE" | jq -r .version_name)" >> "$GITHUB_OUTPUT"

# ... run your integration tests here ...

- name: Clean up Jira test fixtures
  if: always()
  env:
    JIRA_USER: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_USER }}
    JIRA_TOKEN: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_TOKEN }}
  run: |
    python test-fixtures/jira/cleanup.py \
      --jira-url "https://sonarsource-sandbox-608.atlassian.net/" \
      --state-file /tmp/jira-fixtures.json
```

## Running Tests Locally

```bash
cd test-fixtures/jira
pip install -r requirements.txt
pip install pytest pytest-cov
python -m pytest test_*.py -v --cov --cov-report=term-missing
```

## Authentication

Scripts use `JIRA_USER` and `JIRA_TOKEN` environment variables. In CI, these are fetched from Vault at `development/kv/data/jira`.
