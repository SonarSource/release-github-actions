# Get Jira Release Notes Action

This GitHub Action fetches Jira release notes and generates the release notes URL for a given project and version. It combines functionality from both fetching release notes content and generating the proper Jira URL.

## Description

The action retrieves Jira release information by:
1. Connecting to Jira using authentication credentials from Vault
2. Fetching the version ID for the specified project and version name
3. Retrieving all issues associated with the specified fixVersion
4. Formatting the issues into categorized release notes in both Markdown and Jira wiki markup formats
5. Generating the proper Jira release notes URL
6. Returning both the formatted release notes and the URL

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Jira credentials
- [SonarSource/release-github-actions/get-jira-version](https://github.com/SonarSource/release-github-actions) when neither jira-version-name nor JIRA_VERSION_NAME are provided

## Inputs

| Input               | Description                                                                                                                                                                                                                      | Required | Default                                                     |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|-------------------------------------------------------------|
| `jira-project-key`  | The key of the Jira project (e.g., SONARIAC). Can also be set via `JIRA_PROJECT_KEY` environment variable                                                                                                                        | No*      | -                                                           |
| `jira-version-name` | The name of the Jira version/fixVersion (e.g., 1.2.3). Can also be set via `JIRA_VERSION_NAME` environment variable. If neither is provided, the action will attempt to automatically fetch the version using `get-jira-version` | No       | -                                                           |
| `use-jira-sandbox`  | Use the sandbox Jira server instead of production. Can also be controlled via `USE_JIRA_SANDBOX` environment variable                                                                                                            | No       | `false`                                                     |
| `issue-types`       | Comma-separated list of issue types to include in the release notes, in order                                                                                                                                                    | No       | `New Feature,False Positive,False Negative,Bug,Improvement` |

*Either the input or corresponding environment variable must be provided for jira-project-key.

## Outputs

| Output                          | Description                                              |
|---------------------------------|----------------------------------------------------------|
| `release-notes`                 | The formatted release notes as Markdown                  |
| `jira-release-notes`            | The formatted release notes in Jira wiki markup          |
| `jira-release-url`              | The URL to the Jira release notes page                   |
| `jira-release-issue-filter-url` | The URL of the issue filter for the Jira release         |

## Environment Variables Set

| Environment Variable              | Description                                                                                             |
|-----------------------------------|---------------------------------------------------------------------------------------------------------|
| `RELEASE_NOTES`                   | The formatted release notes as Markdown (same content as `release-notes` output)                        |
| `JIRA_RELEASE_NOTES`              | The formatted release notes in Jira wiki markup (same content as `jira-release-notes` output)           |
| `JIRA_RELEASE_URL`                | The URL to the Jira release notes page (same content as `jira-release-url` output)                      |
| `JIRA_RELEASE_ISSUE_FILTER_URL`   | The URL of the issue filter for the Jira release (same content as `jira-release-issue-filter-url` output) |

## Usage

### Basic usage

```yaml
- name: Get Jira Release Notes
  id: jira-notes
  uses: SonarSource/release-github-actions/get-jira-release-notes@v1
  with:
    jira-project-key: 'SONARIAC'
    jira-version-name: '1.2.3'

- name: Use the outputs
  run: |
    echo "Release Notes URL: ${{ steps.jira-notes.outputs.jira-release-url }}"
    echo "Issue Filter URL: ${{ steps.jira-notes.outputs.jira-release-issue-filter-url }}"
    echo "Release Notes (Markdown):"
    echo "${{ steps.jira-notes.outputs.release-notes }}"
    echo "Release Notes (Jira Format):"
    echo "${{ steps.jira-notes.outputs.jira-release-notes }}"
```

### Custom issue types ordering

```yaml
- name: Get Jira Release Notes with Custom Types
  id: jira-notes
  uses: SonarSource/release-github-actions/get-jira-release-notes@v1
  with:
    jira-project-key: 'SONARIAC'
    jira-version-name: '1.2.3'
    issue-types: 'New Feature,Bug,Improvement,Documentation'
```

### Using environment variables

```yaml
- name: Get Jira Release Notes with Environment Variables
  uses: SonarSource/release-github-actions/get-jira-release-notes@v1
  env:
    JIRA_PROJECT_KEY: 'SONARIAC'
    JIRA_VERSION_NAME: '1.2.3'
```

### Mixed usage (inputs override environment variables)

```yaml
- name: Get Jira Release Notes with Mixed Parameters
  uses: SonarSource/release-github-actions/get-jira-release-notes@v1
  with:
    jira-project-key: 'OVERRIDE_PROJECT'  # This overrides JIRA_PROJECT_KEY
  env:
    JIRA_PROJECT_KEY: 'SONARIAC'
    JIRA_VERSION_NAME: '1.2.3'
```

### With automatic version fetching

```yaml
- name: Get Jira Release Notes with Auto-Fetched Version
  uses: SonarSource/release-github-actions/get-jira-release-notes@v1
  with:
    jira-project-key: 'SONARIAC'
```

### Using sandbox environment

```yaml
- name: Get Jira Release Notes from Sandbox
  uses: SonarSource/release-github-actions/get-jira-release-notes@v1
  with:
    jira-project-key: 'TESTPROJECT'
    jira-version-name: '1.0.0-beta'
    use-jira-sandbox: 'true'
```

## Example

If you have a Jira project `SONARIAC` with version `1.2.3` containing:
- 2 New Feature issues
- 3 Bug fixes
- 1 Improvement

The action will:
1. Connect to Jira and find version `1.2.3` in project `SONARIAC`
2. Fetch all 6 issues with fixVersion `1.2.3`
3. Generate a Markdown document with categorized sections
4. Return the release notes URL (`https://sonarsource.atlassian.net/projects/SONARIAC/versions/12345/tab/release-report-all-issues`) and the formatted release notes in both Markdown and Jira wiki markup formats

## Implementation Details

The action uses a Python script that:
- Authenticates with Jira using credentials from HashiCorp Vault
- Supports both production and sandbox Jira environments
- Fetches version metadata to get the proper version ID for URL generation
- Queries Jira for all issues with the specified fixVersion
- Groups issues by type and formats them according to the specified order
- Generates both human-readable release notes and machine-readable URLs
- Outputs results in GitHub Actions format for use in subsequent steps

## Notes

- This action requires access to SonarSource's HashiCorp Vault for Jira credentials
- Either `jira-project-key` input or `JIRA_PROJECT_KEY` environment variable must be provided
- If neither `jira-version-name` input nor `JIRA_VERSION_NAME` environment variable is provided, the action will attempt to automatically fetch the version using the `get-jira-version` action
- Inputs take priority over environment variables when both are set
- The action will fail if the specified project or version doesn't exist in Jira
- Issue types that don't match the specified categories will not appear in the release notes
- The action supports both production and sandbox Jira environments
- Release notes are formatted to match Jira's native export format
- Empty sections (issue types with no issues) are omitted from the output
