# Get Release Version Action

This GitHub Action extracts the release version from the `repox` status on a specified branch and makes it available as both an output and environment variable.

## Description

The action retrieves the release version by:
1. Calling the GitHub API to get the commit status for the specified branch (defaults to master)
2. Filtering for statuses with context starting with `repox`
3. Extracting the version from the status description using jq
4. Setting the version as both an action output and environment variable

## Prerequisites

This action requires the `statuses: read` permission for the GitHub token to access repository commit statuses via the GitHub API.

## Dependencies

This action depends on:
- `gh` CLI tool (GitHub CLI) for API access
- `jq` for JSON parsing (used within the gh command)

## Inputs

| Input          | Description                              | Required | Default               |
|----------------|------------------------------------------|----------|-----------------------|
| `github-token` | The GitHub token for API calls           | No       | `${{ github.token }}` |
| `branch`       | The branch from which to get the version | No       | `master`              |

## Outputs

| Output            | Description                                     |
|-------------------|-------------------------------------------------|
| `release-version` | The extracted release version from repox status |

## Environment Variables

After successful execution, the following environment variable is set:

| Variable          | Description                                     |
|-------------------|-------------------------------------------------|
| `RELEASE_VERSION` | The extracted release version from repox status |

## Usage

### Basic usage

```yaml
- name: Get Release Version
  id: get-version
  uses: SonarSource/release-github-actions/get-release-version@v1

- name: Use the release version
  run: |
    echo "Release version: ${{ steps.get-version.outputs.release-version }}"
    echo "From environment: $RELEASE_VERSION"
```

### With custom GitHub token

```yaml
- name: Get Release Version
  id: get-version
  uses: SonarSource/release-github-actions/get-release-version@v1
  with:
    github-token: ${{ secrets.CUSTOM_GITHUB_TOKEN }}
```

### With custom branch

```yaml
- name: Get Release Version from specific branch
  id: get-version
  uses: SonarSource/release-github-actions/get-release-version@v1
  with:
    branch: someone/some_new_feature
```

## Implementation Details

The action uses a shell script that:
- Executes the gh CLI command: `gh api "/repos/{owner/repo}/commits/{branch}/status" --jq ".statuses[] | select(.context | startswith(\"repox\")) | .description | split(\"'\")[1]"`
- Uses the standard GitHub context `${{ github.repository }}` to get the repository owner and name
- Uses the specified branch input (defaults to master if not provided)
- Validates that a version was successfully extracted
- Sets both `GITHUB_OUTPUT` and `GITHUB_ENV` for maximum compatibility

## Error Handling

The action will fail with a non-zero exit code if:
- The GitHub API call fails
- No `repox` status is found
- The version cannot be extracted from the status description
- The extracted version is empty

## Notes

- This action assumes that the `repox` status contains the version in a specific format within single quotes
- The action works with any context that starts with `repox` (e.g., `repox-master`, `someone/some_new_feature`)
- The action requires read access to the repository's commit statuses
- The `gh` CLI tool must be available in the runner environment (it's pre-installed on GitHub-hosted runners)
