# Get Release Version Action

This GitHub Action extracts the release version from the `repox` status on a specified branch and makes it available as both an output and environment variable.

## Description

The action retrieves the release version by:
1. Calling the GitHub API to get the commit status for the specified branch (defaults to master)
2. Preferring the repo's own promoted-build status, `repox-<repo-name>-<branch>` (e.g.
   `repox-sonar-analyzer-commons-master`) — falling back to any status starting with
   `repox-<branch>` if that repo-specific one isn't present
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
- Fetches the commit status JSON once: `gh api "/repos/{owner/repo}/commits/{branch}/status"`
- Looks for the exact context `repox-<repo-name>-<branch>` first (the repo's own promoted-build
  status), then falls back to any context starting with `repox-<branch>` if that isn't found
- Uses the standard GitHub context `${{ github.repository }}` for the API call, and the
  `GITHUB_REPOSITORY` runner env var to derive `<repo-name>` for the exact-match lookup
- Validates that a version was successfully extracted
- Sets both `GITHUB_OUTPUT` and `GITHUB_ENV` for maximum compatibility

### Why prefer the repo-specific context?

Repox also posts a generic `repox-<branch>` status that mirrors whichever build-name was
promoted most recently. For a repo that only ever promotes one artifact this is identical to its
own `repox-<repo-name>-<branch>` status. But a repo that promotes more than one artifact under
different build names (e.g. a Maven build plus a secondary npm/NuGet package) can have that
generic status flip between the two, each with a different version format — the npm side, for
example, needs valid semver and typically rewrites a `X.Y.Z.buildNumber` Maven version into a
`X.Y.Z-buildNumber` prerelease tag. Preferring the repo-specific context avoids inheriting
whichever artifact happened to promote last.

## Error Handling

The action will fail with a non-zero exit code if:
- The GitHub API call fails
- No matching `repox` status is found (neither the repo-specific context nor the generic fallback)
- The version cannot be extracted from the status description
- The extracted version is empty

## Notes

- This action assumes that the matched `repox` status contains the version in a specific format
  within single quotes
- The action requires read access to the repository's commit statuses
- The `gh` CLI tool must be available in the runner environment (it's pre-installed on GitHub-hosted runners)
