# Get Jira Version Action

This GitHub Action extracts a Jira-compatible version number from a release version by formatting it appropriately for Jira version management.

## Description

The action takes a release version (typically in the format `major.minor.patch.build`) and converts it to a Jira version format by:
1. Extracting the first three components (major.minor.patch)
2. Removing any trailing `.0` to match Jira's version naming conventions

## Dependencies

This action depends on the [SonarSource/release-github-actions/get-release-version](https://github.com/SonarSource/release-github-actions) action to retrieve the release version.

## Outputs

| Output              | Description                                                 |
|---------------------|-------------------------------------------------------------|
| `jira-version-name` | The Jira-formatted version derived from the release version |

## Environment Variables

| Variable             | Description                                                 |
|----------------------|-------------------------------------------------------------|
| `JIRA_VERSION_NAME`  | The Jira-formatted version derived from the release version |

## Usage

```yaml
- id: jira-version
  uses: SonarSource/release-github-actions/get-jira-version@master
  
- run: echo "Jira version is ${{ steps.jira-version.outputs.jira-version-name }}"

# alternatively, you can access the version as an environment variable

- uses: SonarSource/release-github-actions/get-jira-version@master
- run: echo "Jira version is ${{ env.JIRA_VERSION_NAME }}"

```

## Example

If the release version is `1.2.3.45`, the action will:
1. Extract `1.2.3` (first three components)
2. Output `jira-version-name=1.2.3` and set `JIRA_VERSION_NAME=1.2.3`

If the release version is `2.1.0.12`, the action will:
1. Extract `2.1.0` (first three components)
2. Remove trailing `.0` to get `2.1`
3. Output `jira-version-name=2.1` and set `JIRA_VERSION_NAME=2.1`

## Implementation Details

The action uses a bash script that:
- Uses `cut` to extract the major.minor.patch components from the release version
- Uses `sed` to remove trailing `.0` if present
- Sets both the GitHub output (`jira-version-name`) and environment variable (`JIRA_VERSION_NAME`) for the Jira version

## Notes

- This action is designed to work with semantic versioning patterns
- The trailing `.0` removal helps maintain cleaner version names in Jira
- The action assumes the release version follows the pattern `major.minor.patch.build`
