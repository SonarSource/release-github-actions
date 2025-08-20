# Create Jira Version Action

This GitHub Action creates a new version in a Jira project, with the ability to automatically determine the next version number based on existing versions.

## Description

The action creates a new version in the specified Jira project by:
1. Connecting to Jira using authentication credentials from Vault
2. Validating required project key from inputs or environment variables
3. Either using a provided version name or automatically determining the next version number
4. Creating the new version in the specified Jira project
5. Returning the created version's ID and name

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Jira credentials
- [SonarSource/release-github-actions/get-jira-version](https://github.com/SonarSource/release-github-actions) when auto-determining version names

## Inputs

| Input               | Description                                                                                                               | Required | Default         |
|---------------------|---------------------------------------------------------------------------------------------------------------------------|----------|-----------------|
| `jira-project-key`  | The key of the Jira project (e.g., SONARIAC). Can also be set via `JIRA_PROJECT_KEY` environment variable                 | No*      | -               |
| `jira-version-name` | The name of the Jira version to create (e.g., 1.2.3). Can also be set via `JIRA_VERSION_NAME` environment variable        | No       | Auto-determined |
| `use-jira-sandbox`  | Use the sandbox server instead of the production Jira. Can also be controlled via `USE_JIRA_SANDBOX` environment variable | No       | -               |

*Either the input or corresponding environment variable must be provided for jira-project-key.

## Outputs

| Output              | Description                          |
|---------------------|--------------------------------------|
| `jira-version-id`   | The ID of the created Jira version   |
| `jira-version-name` | The name of the created Jira version |

## Usage

### Basic usage with explicit version name

```yaml
- name: Create Jira Version
  id: create-version
  uses: SonarSource/release-github-actions/create-jira-version@master
  with:
    jira-project-key: 'SONARIAC'
    jira-version-name: '1.2.3'

- name: Use created version
  run: |
    echo "Created version ID: ${{ steps.create-version.outputs.jira-version-id }}"
    echo "Created version name: ${{ steps.create-version.outputs.jira-version-name }}"
```

### Auto-determine next version number

```yaml
- name: Create Next Jira Version
  id: create-version
  uses: SonarSource/release-github-actions/create-jira-version@master
  with:
    jira-project-key: 'SONARIAC'
    # jira-version-name is omitted - will auto-increment from latest version

- name: Use created version
  run: |
    echo "Created version: ${{ steps.create-version.outputs.jira-version-name }}"
```

### Using environment variables

```yaml
- name: Create Jira Version
  uses: SonarSource/release-github-actions/create-jira-version@master
  env:
    JIRA_PROJECT_KEY: 'SONARIAC'
  with:
    jira-version: '1.2.3'
```

### Using sandbox environment

```yaml
- name: Create Jira Version in Sandbox
  uses: SonarSource/release-github-actions/create-jira-version@master
  with:
    jira-project-key: 'TESTPROJECT'
    jira-version-name: '1.0.0-beta'
    use-jira-sandbox: 'true'
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
- Validates required project key from inputs or environment variables
- Supports both production and sandbox Jira environments via URL selection
- Can auto-determine the next version number by incrementing the latest existing version
- Creates the new version using the Jira REST API
- Outputs the created version's metadata for use in subsequent steps

## Notes

- This action requires access to SonarSource's HashiCorp Vault for Jira credentials
- Either `jira-project-key` input or `JIRA_PROJECT_KEY` environment variable must be provided
- When `jira-version-name` is not provided, the action automatically determines the next version by incrementing the latest existing version
- Input parameters take precedence over environment variables when both are provided
- The action supports both production and sandbox Jira environments
- Version names should follow semantic versioning patterns for best results
- The action will handle existing versions gracefully and return the existing version details
