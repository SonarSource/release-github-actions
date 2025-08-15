# Get Jira Release Notes Action

This GitHub Action fetches Jira release notes and generates the release notes URL for a given project and version. It combines functionality from both fetching release notes content and generating the proper Jira URL.

## Description

The action retrieves Jira release information by:
1. Connecting to Jira using authentication credentials from Vault
2. Fetching the version ID for the specified project and version name
3. Retrieving all issues associated with the specified fixVersion
4. Formatting the issues into categorized Markdown release notes
5. Generating the proper Jira release notes URL
6. Returning both the formatted release notes and the URL

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Jira credentials

## Inputs

| Input               | Description                                                                                                           | Required | Default                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------|----------|-------------------------------------------------------------|
| `jira-project-key`  | The key of the Jira project (e.g., SONARIAC). Can also be set via `JIRA_PROJECT_KEY` environment variable             | No       |                                                             |
| `jira-version-name` | The name of the Jira version/fixVersion (e.g., 1.2.3). Can also be set via `JIRA_VERSION` environment variable        | No       |                                                             |
| `use-jira-sandbox`  | Use the sandbox Jira server instead of production. Can also be controlled via `USE_JIRA_SANDBOX` environment variable | No       | `false`                                                     |
| `issue-types`       | Comma-separated list of issue types to include in the release notes, in order                                         | No       | `New Feature,False Positive,False Negative,Bug,Improvement` |

## Outputs

| Output             | Description                             |
|--------------------|-----------------------------------------|
| `release-notes`    | The formatted release notes as Markdown |
| `jira-release-url` | The URL to the Jira release notes page  |

## Environment Variables Set

| Environment Variable | Description                                                                        |
|----------------------|------------------------------------------------------------------------------------|
| `RELEASE_NOTES`      | The formatted release notes as Markdown (same content as `release-notes` output)   |
| `JIRA_RELEASE_URL`   | The URL to the Jira release notes page (same content as `jira-release-url` output) |

## Usage

### Basic usage

```yaml
- name: Get Jira Release Notes
  id: jira-notes
  uses: SonarSource/release-github-actions/get-jira-release-notes@master
  with:
    jira-project-key: 'SONARIAC'
    jira-version-name: '1.2.3'

- name: Use the outputs
  run: |
    echo "Release Notes URL: ${{ steps.jira-notes.outputs.jira-release-url }}"
    echo "Release Notes:"
    echo "${{ steps.jira-notes.outputs.release-notes }}"
```

### Custom issue types ordering

```yaml
- name: Get Jira Release Notes with Custom Types
  id: jira-notes
  uses: SonarSource/release-github-actions/get-jira-release-notes@master
  with:
    jira-project-key: 'SONARIAC'
    jira-version-name: '1.2.3'
    issue-types: 'New Feature,Bug,Improvement,Documentation'
```

### Using environment variables

```yaml
- name: Get Jira Release Notes with Environment Variables
  uses: SonarSource/release-github-actions/get-jira-release-notes@master
  env:
    JIRA_PROJECT_KEY: 'SONARIAC'
    JIRA_VERSION: '1.2.3'
```

### Mixed usage (inputs override environment variables)

```yaml
- name: Get Jira Release Notes with Mixed Parameters
  uses: SonarSource/release-github-actions/get-jira-release-notes@master
  with:
    jira-project-key: 'OVERRIDE_PROJECT'  # This overrides JIRA_PROJECT_KEY
  env:
    JIRA_PROJECT_KEY: 'SONARIAC'
    JIRA_VERSION: '1.2.3'
```

### Using sandbox environment

```yaml
- name: Get Jira Release Notes from Sandbox
  uses: SonarSource/release-github-actions/get-jira-release-notes@master
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
4. Return both the release notes URL (`https://sonarsource.atlassian.net/projects/SONARIAC/versions/12345/tab/release-report-all-issues`) and the formatted release notes in Markdown format

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
- Either both inputs (`jira-project-key` and `jira-version-name`) or both environment variables (`JIRA_PROJECT_KEY` and `JIRA_VERSION`) must be provided
- Inputs take priority over environment variables when both are set
- The action will fail if the specified project or version doesn't exist in Jira
- Issue types that don't match the specified categories will not appear in the release notes
- The action supports both production and sandbox Jira environments
- Release notes are formatted to match Jira's native export format
- Empty sections (issue types with no issues) are omitted from the output
