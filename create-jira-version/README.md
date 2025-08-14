# Create Jira Version Action

This GitHub Action creates a new version in a Jira project, with the ability to automatically determine the next version number based on existing versions.

## Description

The action creates a new version in the specified Jira project by:
1. Connecting to Jira using authentication credentials from Vault
2. Either using a provided version name or automatically determining the next version number
3. Creating the new version in the specified Jira project
4. Returning the created version's ID and name

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Jira credentials
- [SonarSource/release-github-actions/get-jira-version](https://github.com/SonarSource/release-github-actions) when auto-determining version names

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `jira_project_key` | The key of the Jira project (e.g., SONARIAC) | Yes | - |
| `jira_version_name` | The name of the Jira version to create (e.g., 1.2.3) | No | Auto-determined |
| `use_jira_sandbox` | Use the sandbox Jira server instead of production | No | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `jira_version_id` | The ID of the created Jira version |
| `jira_version_name` | The name of the created Jira version |

## Usage

### Basic usage with explicit version name

```yaml
- name: Create Jira Version
  id: create-version
  uses: SonarSource/release-github-actions/create-jira-version@master
  with:
    jira_project_key: 'SONARIAC'
    jira_version_name: '1.2.3'

- name: Use created version
  run: |
    echo "Created version ID: ${{ steps.create-version.outputs.jira_version_id }}"
    echo "Created version name: ${{ steps.create-version.outputs.jira_version_name }}"
```

### Auto-determine next version number

```yaml
- name: Create Next Jira Version
  id: create-version
  uses: SonarSource/release-github-actions/create-jira-version@master
  with:
    jira_project_key: 'SONARIAC'
    # jira_version_name is omitted - will auto-increment from latest version

- name: Use created version
  run: |
    echo "Created version: ${{ steps.create-version.outputs.jira_version_name }}"
```

### Using sandbox environment

```yaml
- name: Create Jira Version in Sandbox
  uses: SonarSource/release-github-actions/create-jira-version@master
  with:
    jira_project_key: 'TESTPROJECT'
    jira_version_name: '1.0.0-beta'
    use_jira_sandbox: 'true'
```

## Example

If you have existing versions `1.2.1` and `1.2.2` in your Jira project and don't specify a version name:
1. The action will get the latest version (`1.2.2`)
2. Auto-increment to determine the next version (`1.2.3`)
3. Create version `1.2.3` in Jira
4. Return the new version's ID and name

## Implementation Details

The action uses a Python script that:
- Authenticates with Jira using credentials from HashiCorp Vault
- Supports both production and sandbox Jira environments
- Can auto-determine the next version number by incrementing the latest existing version
- Creates the new version using the Jira REST API
- Outputs the created version's metadata for use in subsequent steps


## Notes

- This action requires access to SonarSource's HashiCorp Vault for Jira credentials
- When `jira_version_name` is not provided, the action automatically determines the next version by incrementing the latest existing version
- The action supports both production and sandbox Jira environments
- Version names should follow semantic versioning patterns for best results
- The action will fail if a version with the same name already exists in the project
