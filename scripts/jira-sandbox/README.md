# Jira Sandbox Test Helper Scripts

End-to-end test helpers for the Jira-related GitHub Actions. These scripts create real Jira objects in the sandbox, run verifications against them, then clean up.

**Sandbox URL:** `https://sonarsource-sandbox-608.atlassian.net/`
**Projects used:** `SONARIAC` (analyzer versions & issues), `REL` (release tickets)

## Prerequisites

Set your sandbox credentials:

```bash
export JIRA_USER=<your-email>
export JIRA_TOKEN=<your-api-token>
```

Install dependencies (same `jira` library used by the actions):

```bash
pip install jira
```

## Running the tests

### Full cycle (recommended)

```bash
cd scripts/jira-sandbox
python run_all.py
```

This runs `setup.py` → `verify.py` → `cleanup.py` in sequence. Cleanup always runs, even if verify fails.

### Individual scripts

```bash
cd scripts/jira-sandbox

# 1. Create test fixtures
python setup.py

# 2. Run verifications
python verify.py

# 3. Remove test fixtures
python cleanup.py
```

## What each script does

### `setup.py`
Creates the test fixtures needed for a full release cycle:
1. Creates a Jira version in `SONARIAC` using the scheme `99.<MMDD>.<HHMM>` (e.g. `99.310.1430` for March 10 at 14:30)
2. Creates one Feature, one Bug, and one Maintenance issue with `fixVersion` set
3. Creates a release ticket in the `REL` project
4. Writes all keys/IDs to `test_state.json`

**Version scheme:** Major `99` is well above real production versions and clearly identifies test data. Patch encodes HHMM so it is always non-zero for any run after midnight. Versions ending in `.0` are avoided because `normalize_version_name()` in `create-jira-version` would strip that suffix.

### `verify.py`
Reads `test_state.json` and runs the following checks:
1. Version exists and is unreleased
2. Issues are assigned to the test version (`fixVersion`)
3. Marks the version released (simulates `release-jira-version` action)
4. Creates the next version with patch+1 (simulates `create-jira-version` action)
5. Fetches release notes and verifies expected issue types (simulates `get-jira-release-notes`)
6. Creates an integration ticket linked to the release ticket (simulates `create-integration-ticket`)
7. Transitions the release ticket to "Start Progress" (simulates `update-release-ticket-status`)

### `cleanup.py`
Reads `test_state.json` and removes:
- All issues created by `setup.py` and `verify.py`
- The test Jira version (and next version if created)
- `test_state.json` itself

### `run_all.py`
Orchestrator that runs setup → verify → cleanup. Exit code is 0 only if all three scripts pass.

## Notes

- These scripts only target the **sandbox** instance, never production
- `test_state.json` is gitignored and lives only locally during a test run
- If cleanup fails or is interrupted, run `python cleanup.py` manually to remove leftover fixtures
