# Release Jira Version Action

This GitHub Action automates releasing a version in Jira and then creating a new, subsequent version. It is useful for end-of-release-cycle workflows.

## Description

The action performs the following operations:
1. Connecting to Jira using authentication credentials from Vault
2. Finding a Jira version matching the `jira_version_name` input within the specified `jira_project_key`
3. Marking that version as "released" in Jira, setting the release date to the current day
4. Creating the next version by automatically incrementing the version number (e.g., `1.5.2` becomes `1.5.3`)

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Jira credentials
- [SonarSource/release-github-actions/get-jira-version](https://github.com/SonarSource/release-github-actions) when auto-determining version names

## Inputs

| Input | Description                                                                                                                                   | Required | Default |
|-------|-----------------------------------------------------------------------------------------------------------------------------------------------|----------|---------|
| `jira_project_key` | The key of the Jira project (e.g., SONARIAC)                                                                                                  | Yes | - |
| `jira_version_name` | The name of the Jira version to release (e.g., 1.2.3). If not provided, the script will determine the next version based on the build number. | No | Auto-determined |
| `use_jira_sandbox` | Use the sandbox Jira server instead of production. Can also be controlled via `USE_JIRA_SANDBOX` environment variable.                        | No | `false` |

## Outputs

No outputs are defined for this action, as it primarily performs operations without returning values.

## Usage

### Basic usage with explicit version name

```yaml
- name: Release Jira Version
  uses: SonarSource/release-github-actions/release-jira-version@master
  with:
    jira_project_key: 'SONARIAC'
    jira_version_name: '1.2.3'
```

### Auto-determine version to release

```yaml
- name: Release Current Jira Version
  uses: SonarSource/release-github-actions/release-jira-version@master
  with:
    jira_project_key: 'SONARIAC'
    # jira_version_name is omitted - will auto-determine from the build number
```

### Using sandbox environment (with input)

```yaml
- name: Release Jira Version in Sandbox
  uses: SonarSource/release-github-actions/release-jira-version@master
  with:
    jira_project_key: 'SONARIAC'
    jira_version_name: '1.2.3'
    use_jira_sandbox: 'true'
```

### Using sandbox environment (with environment variable)

```yaml
- name: Release Jira Version in Sandbox
  uses: SonarSource/release-github-actions/release-jira-version@master
  env:
    USE_JIRA_SANDBOX: 'true'
  with:
    jira_project_key: 'SONARIAC'
    jira_version_name: '1.2.3'
```

## Example

If you have an unreleased version `1.2.2` in your Jira project:
1. The action will find and release version `1.2.2`, marking it as released with today's date
2. Auto-increment to determine the next version (`1.2.3`)
3. Create the new unreleased version `1.2.3` in Jira
4. The development cycle can continue with the new version

## Implementation Details

The action uses a Python script that:
- Authenticates with Jira using credentials from HashiCorp Vault
- Supports both production and sandbox Jira environments (via input or environment variable)
- Can auto-determine which version to release by finding the latest unreleased version
- Releases the specified version using the Jira REST API
- Automatically creates the next version by incrementing the version number

## Prerequisites

The action requires that the repository has the `development/kv/data/jira` token configured in vault.
This can be done using the SPEED self-service portal ([more info](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)).

The [Jira API user](https://sonarsource.atlassian.net/jira/people/712020:9dcffe4d-55ee-4d69-b5d1-535c6dbd9cc4) must have the project role `Administrators` for the target project to manage releases.

## Notes

- This action requires access to SonarSource's HashiCorp Vault for Jira credentials
- The action supports both production and sandbox Jira environments
- Environment variables take precedence when both input and environment variable are provided
- Version names should follow semantic versioning patterns for best results
- The action will automatically create the next version after releasing the current one
- The released version will be marked with the current date as the release date
