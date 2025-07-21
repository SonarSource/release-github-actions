# Release Jira Version Action

This GitHub Action automates releasing a version in Jira and then creating a new, subsequent version. It is useful for end-of-release-cycle workflows.

## How It Works

1.  **Finds a Version**: It searches for a Jira version matching the `jira_release_name` input within the specified `project_key`.
2.  **Releases It**: It marks that version as "released" in Jira, setting the release date to the current day.
3.  **Creates the Next Version**:
    - If you provide a `new_version_name`, it creates a new version with that exact name.
    - If you don't, it attempts to increment the last number of the `jira_release_name` (e.g., `1.5.2` becomes `1.5.3`) and creates a new version with the incremented name.

## Prerequisites

The action requires that the repository has the `development/kv/data/jira` token configured in vault.
This can be done using the SPEED self-service portal ([more info](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)).

The [Jira API user](https://sonarsource.atlassian.net/jira/people/712020:9dcffe4d-55ee-4d69-b5d1-535c6dbd9cc4)  must have the project role `Administrators` for the target project to manage releases.

## Inputs

| Input               | Description                                                                                         | Required | Default |
|---------------------|-----------------------------------------------------------------------------------------------------|----------|---------|
| `jira_user`         | The Jira user (email) for authentication.                                                           | `true`   |         |
| `jira_token`        | The Jira API token for authentication. **Store as a secret!**                                       | `true`   |         |
| `project_key`       | The project key in Jira (e.g., `SONARIAC`).                                                         | `true`   |         |
| `jira_release_name` | The exact name of the Jira version you want to release (e.g., `1.2.3`).                             | `true`   |         |
| `new_version_name`  | The name for the next version. If omitted, the action will auto-increment from `jira_release_name`. | `false`  | `''`    |
| `use_sandbox`       | Set to `false` to use the production Jira server. Recommended to test with `true` first.            | `false`  | `true`  |

## Outputs

| Output             | Description                                   |
|--------------------|-----------------------------------------------|
| `new_version_name` | The name of the new version that was created. |

## Example Usage

This example demonstrates a manually triggered workflow that releases the provided version and creates a new one in the `SONARIAC` project.

```yaml
name: Release Jira Version

on:
  workflow_dispatch:
    inputs:
      version_to_release:
        description: "Jira version to release"
        required: true
      next_version:
        description: "Next Jira version to create"
        required: false

jobs:
  release_in_jira:
    name: Release Jira Version
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - name: Get Jira Credentials from Vault
        id: secrets
        uses: SonarSource/vault-action-wrapper@v3
        with:
          secrets: |
            development/kv/data/jira user | JIRA_USER;
            development/kv/data/jira token | JIRA_TOKEN;

      - name: Release and Create Next Version
        id: jira_release
        uses: SonarSource/release-github-actions/release-jira-version@master
        with:
          jira_user: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_USER }}
          jira_token: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_TOKEN }}
          project_key: 'SONARIAC'
          jira_release_name: ${{ github.event.inputs.version_to_release }}
          new_version_name: ${{ github.event.inputs.next_version }}
          use_sandbox: true

      - name: Echo Output
        run: |
          echo "Created new version: ${{ steps.jira_release.outputs.new_version_name }}"
```
