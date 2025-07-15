# Create Jira Release Ticket Action

This GitHub Action automates the creation of an "Ask for release" ticket in Jira. It is designed to be used in release workflows to standardize the process of requesting a new software release.

The action is self-contained and uses a Python script to interact with the Jira API.
## Prerequisites

The action requires that the repository needs to have the `development/kv/data/jira` token configured in vault.
This can done using the SPEED self-service portal ([more info](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)).

## Inputs

The following inputs can be configured for the action:

| Input                  | Description                                                                                                        | Required | Default |
|------------------------|--------------------------------------------------------------------------------------------------------------------|----------|---------|
| `jira_user`            | The Jira user (email) for authentication.                                                                          | `true`   |         |
| `jira_token`           | The Jira API token for authentication.                                                                             | `true`   |         |
| `project_key`          | The project key (e.g., `SONARIAC`).                                                                                | `true`   |         |
| `project_name`         | The display name of the project (e.g., `SonarIaC`). Will be used as the prefix of the resulting release ticket.    | `true`   |         |
| `version`              | The new version string being released (e.g., `1.2.3`).                                                             | `true`   |         |
| `short_description`    | A brief description of the release.                                                                                | `true`   |         |
| `sq_compatibility`     | The SonarQube compatibility version (e.g., `2025.3`).                                                              | `true`   |         |
| `use_sandbox`          | Set to `false` to use the Jira production server.                                                                  | `false`  | `true`  |
| `documentation_status` | The status of the release documentation.                                                                           | `false`  | `N/A`   |
| `rule_props_changed`   | Whether rule properties have changed (`Yes` or `No`).                                                              | `false`  | `No`    |
| `jira_release_name`    | The specific Jira release version to use. If omitted and there is only one unreleased version it will released it. | `false`  | `''`    |
| `sonarlint_changelog`  | The SonarLint changelog content.                                                                                   | `false`  | `''`    |

## Outputs

| Output       | Description                                    |
|--------------|------------------------------------------------|
| `ticket_key` | The key of the jira ticket (e.g., `REL-1234`). |

## Example Usage

Here is an example of how to use this action in a workflow. This job will be triggered manually and will create a Jira release ticket using the provided inputs and secrets from HashiCorp Vault.

```yaml
name: Create Release Ticket

env:
  PROJECT_KEY: 'SONARIAC'
  PROJECT_NAME: 'SonarIaC'

on:
  workflow_dispatch:
    inputs:
     version:
        description: 'Version'
        required: true
        default: '1.0.0'
      short_description:
        description: 'Short Description'
        required: true
      sq_compatibility:
        description: 'SonarQube Compatibility'
        required: true
      jira_release:
        description: 'Jira release version'
        required: false
      sonarlint_changelog:
        description: 'SonarLint changelog content'
        required: false

jobs:
  create_release_ticket:
    name: Create release ticket
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

      - name: Create Jira Release Ticket
        id: create_ticket
        uses: SonarSource/release-github-actions/.github/actions/create-jira-release-ticket
        with:
          jira_user: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_USER }}
          jira_token: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_TOKEN }}
          project_key: ${{ env.PROJECT_KEY }}
          project_name: ${{ env.PROJECT_NAME }}
          version: ${{ github.event.inputs.version }}
          short_description: ${{ github.event.inputs.short_description }}
          sq_compatibility: ${{ github.event.inputs.sq_compatibility }}
          jira_release_name: ${{ github.event.inputs.jira_release }}
          sonarlint_changelog: ${{ github.event.inputs.sonarlint_changelog }}

      - name: Echo Ticket Key
        run: echo "The created Jira ticket key is ${{ steps.create_ticket.outputs.ticket_key }}"
