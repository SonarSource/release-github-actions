# Create Jira Release Ticket Action

This GitHub Action automates the creation of an "Ask for release" ticket in Jira. It is designed to be used in release workflows to standardize the process of requesting a new software release.

The action is self-contained and uses a Python script to interact with the Jira API.

## Inputs

The following inputs can be configured for the action:

| Input                  | Description                                            | Required | Default |
|------------------------|--------------------------------------------------------|----------|---------|
| `jira_user`            | The Jira user (email) for authentication.              | `true`   | `N/A`   |
| `jira_token`           | The Jira API token for authentication.                 | `true`   | `N/A`   |
| `project_key`          | The the project key (e.g., `SONARIAC`).                | `true`   | `N/A`   |
| `project_name`         | The display name of the project (e.g., `SonarIaC`).    | `true`   | `N/A`   |
| `version`              | The new version string being released (e.g., `1.2.3`). | `true`   | `N/A`   |
| `short_description`    | A brief description of the release.                    | `true`   | `N/A`   |
| `targeted_product`     | The targeted product version (e.g., `11.0`).           | `true`   | `N/A`   |
| `sq_compatibility`     | The SonarQube compatibility version (e.g., `2025.3`).  | `true`   | `N/A`   |
| `use_sandbox`          | Set to `True` to use the Jira sandbox server.          | `false`  | `True`  |
| `documentation_status` | The status of the release documentation.               | `false`  | `N/A`   |
| `rule_props_changed`   | Whether rule properties have changed (`Yes` or `No`).  | `false`  | `No`    |

## Outputs

| Output       | Description                                    |
|--------------|------------------------------------------------|
| `ticket_key` | The key of the jira ticket (e.g., `REL-1234`). |

## Example Usage

Here is an example of how to use this action in a workflow. This job will be triggered manually and will create a Jira release ticket using the provided inputs and secrets from HashiCorp Vault.

```yaml
name: Create Release Ticket

# Define environment variables for project-specific settings
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
        default: 'My new release'
      targeted_product:
        description: 'Targeted Product'
        required: true
        default: '11.0'
      sq_compatibility:
        description: 'SonarQube Compatibility'
        required: true
        default: '2025.3'

jobs:
  create_release_ticket:
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
          targeted_product: ${{ github.event.inputs.targeted_product }}
          sq_compatibility: ${{ github.event.inputs.sq_compatibility }}

      - name: Echo Ticket Key
        run: echo "The created Jira ticket key is ${{ steps.create_ticket.outputs.ticket_key }}"