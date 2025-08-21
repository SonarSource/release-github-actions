# Release Jira Version Action

This GitHub Action automates releasing a version in Jira.

## Description

The action performs the following operations:
1. Connecting to Jira using authentication credentials from Vault
2. Validating required project key from inputs or environment variables
3. Finding a Jira version matching the `jira-version-name` input within the specified `jira-project-key`
4. Marking that version as "released" in Jira, setting the release date to the current day

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Jira credentials
- [SonarSource/release-github-actions/get-jira-version](https://github.com/SonarSource/release-github-actions) when auto-determining version names

## Inputs

| Input               | Description                                                                                                                                                                  | Required | Default         |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|-----------------|
| `jira-project-key`  | The key of the Jira project (e.g., SONARIAC). Can also be set via `JIRA_PROJECT_KEY` environment variable                                                                     | No*      | -               |
| `jira-version-name` | The name of the Jira version to release (e.g., 1.2.3). Can also be set via `JIRA_VERSION_NAME` environment variable. If not provided, the script will determine the next version based on the release version. | No       | Auto-determined |
| `use-jira-sandbox`  | Use the sandbox server instead of the production Jira. Can also be controlled via `USE_JIRA_SANDBOX` environment variable                                                     | No       | -               |

*Either the input or corresponding environment variable must be provided for jira-project-key.

## Outputs

No outputs are defined for this action, as it primarily performs operations without returning values.

## Usage

### Basic usage with explicit version name

```yaml
- name: Release Jira Version
  uses: SonarSource/release-github-actions/release-jira-version@master
  with:
    jira-project-key: 'SONARIAC'
    jira-version-name: '1.2.3'
```

### Auto-determine version to release

```yaml
- name: Release Current Jira Version
  uses: SonarSource/release-github-actions/release-jira-version@master
  with:
    jira-project-key: 'SONARIAC'
    # jira-version-name is omitted - will auto-determine from the release version
```

### Using environment variables

```yaml
- name: Release Jira Version
  uses: SonarSource/release-github-actions/release-jira-version@master
  env:
    JIRA_PROJECT_KEY: 'SONARIAC'
    JIRA_VERSION_NAME: '1.2.3'
```

### Using sandbox environment

```yaml
- name: Release Jira Version in Sandbox
  uses: SonarSource/release-github-actions/release-jira-version@master
  with:
    jira-project-key: 'SONARIAC'
    jira-version-name: '1.2.3'
    use-jira-sandbox: 'true'
```

## Implementation Details

The action uses a Python script that:
- Authenticates with Jira using credentials from HashiCorp Vault
- Validates required project key from inputs or environment variables
- Supports both production and sandbox Jira environments via URL selection
- Can auto-determine which version to release by finding the latest unreleased version
- Releases the specified version using the Jira REST API

## Prerequisites

The action requires that the repository has the `development/kv/data/jira` token configured in vault.
This can be done using the SPEED self-service portal ([more info](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)).

The [Jira API user](https://sonarsource.atlassian.net/jira/people/712020:9dcffe4d-55ee-4d69-b5d1-535c6dbd9cc4) must have the project role `Administrators` for the target project to manage releases.

## Notes

- This action requires access to SonarSource's HashiCorp Vault for Jira credentials
- Either `jira-project-key` input or `JIRA_PROJECT_KEY` environment variable must be provided
- Input parameters take precedence over environment variables when both are provided
- The action supports both production and sandbox Jira environments
- Version names should follow semantic versioning patterns for best results
- The released version will be marked with the current date as the release date
