# Check Releasability Status Action

This GitHub Action checks the Releasability Status on the specified branch using the GitHub Statuses API and verifies that the status is successful.

## Description

The action validates the releasability by:
1. Calling the GitHub API to get the commit status for the specified branch
2. Filtering for statuses with context `Releasability`
3. Verifying that the state is `success`
4. Optionally checking that the description does not contain `failed optional checks`

## Prerequisites

This action requires the `statuses: read` permission for the GitHub token to access repository commit statuses via the GitHub API.

## Inputs

| Input                  | Description                                                                          | Required | Default               |
|------------------------|--------------------------------------------------------------------------------------|----------|-----------------------|
| `github-token`         | The GitHub token for API calls                                                       | No       | `${{ github.token }}` |
| `branch`               | The branch from which to check the releasability status                              | No       | `master`              |
| `with-optional-checks` | Whether to also check that the description does not contain "failed optional checks" | No       | `true`                |

## Outputs

| Output                     | Description                                                              |
|----------------------------|--------------------------------------------------------------------------|
| `releasability-state`      | The state of the Releasability status (e.g., `success`, `failure`, `pending`) |
| `releasability-description`| The description of the Releasability status                              |

These outputs are always set (even on failure), allowing subsequent steps to access the releasability information for reporting or debugging purposes.

## Usage

### Basic usage

```yaml
- name: Check Releasability Status
  uses: SonarSource/release-github-actions/check-releasability-status@master
```

### With custom GitHub token

```yaml
- name: Check Releasability Status
  uses: SonarSource/release-github-actions/check-releasability-status@master
  with:
    github-token: ${{ secrets.CUSTOM_GITHUB_TOKEN }}
```

### Check specific branch

```yaml
- name: Check Releasability Status
  uses: SonarSource/release-github-actions/check-releasability-status@master
  with:
    branch: 'develop'
```

### Disable optional checks validation

```yaml
- name: Check Releasability Status
  uses: SonarSource/release-github-actions/check-releasability-status@master
  with:
    with-optional-checks: 'false'
```

## Implementation Details

The action uses a shell script that:
- Executes the gh CLI command: `gh api "/repos/{owner/repo}/commits/{branch}/status"`
- Uses the standard GitHub context `${{ github.repository }}` to get the repository owner and name
- Uses the specified branch (defaults to `master`)
- Filters for the `Releasability` status context using jq
- Validates that the state is `success`
- Optionally validates that the description doesn't contain `failed optional checks`

## Error Handling

The action will fail with a non-zero exit code if:
- The GitHub API call fails
- No `Releasability` status is found on the specified branch
- The `Releasability` status state is not `success`
- The `with-optional-checks` input is `true` and the description contains `failed optional checks`

## Notes

- This action specifically looks for a status with context `Releasability` (case-sensitive)
- The action defaults to the master branch but can check any specified branch
- The action requires read access to the repository's commit statuses
- The `gh` CLI tool must be available in the runner environment (it's pre-installed on GitHub-hosted runners)
- Unlike the previous implementation, this action no longer extracts version information or uses the Checks API
