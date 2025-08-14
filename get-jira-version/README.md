# Get Jira Version Action

This GitHub Action extracts a Jira-compatible version number from a build number by formatting it appropriately for Jira version management.

## Description

The action takes a build number (typically in the format `major.minor.patch.build`) and converts it to a Jira version format by:
1. Extracting the first three components (major.minor.patch)
2. Removing any trailing `.0` to match Jira's version naming conventions

## Dependencies

This action depends on the [SonarSource/ci-github-actions/get-build-number](https://github.com/SonarSource/ci-github-actions) action to retrieve the build number.

## Outputs/Environment Variables

| Output | Description |
|--------|-------------|
| `JIRA_VERSION` | The Jira-formatted version derived from the build number |

This means you can reference the version in later steps using something like `${{ steps.jira-version.outputs.JIRA_VERSION }}` or `${{ env.JIRA_VERSION }}`.

## Usage

```yaml
- id: jira-version
  uses: SonarSource/release-github-actions/get-jira-version@master
  
- run: echo "Jira version is ${{ steps.jira-version.outputs.JIRA_VERSION }}"

# alternatively, you can access the version as an environment variable

- uses: SonarSource/release-github-actions/get-jira-version@master
- run: echo "Jira version is ${{ env.JIRA_VERSION }}"

```

## Example

If the build number is `1.2.3.45`, the action will:
1. Extract `1.2.3` (first three components)
2. Output `JIRA_VERSION=1.2.3`

If the build number is `2.1.0.12`, the action will:
1. Extract `2.1.0` (first three components)
2. Remove trailing `.0` to get `2.1`
3. Output `JIRA_VERSION=2.1`

## Implementation Details

The action uses a bash script that:
- Uses `cut` to extract the major.minor.patch components from the build number
- Uses `sed` to remove trailing `.0` if present
- Sets both the GitHub output and environment variable for the Jira version

## Notes

- This action is designed to work with semantic versioning patterns
- The trailing `.0` removal helps maintain cleaner version names in Jira
- The action assumes the build number follows the pattern `major.minor.patch.build`
