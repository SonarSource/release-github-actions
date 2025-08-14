# Create Jira Release Ticket Action

This GitHub Action automates the creation of an "Ask for release" ticket in Jira. It is designed to be used in release
workflows to standardize the process of requesting a new software release.

The action is self-contained and uses a Python script to interact with the Jira API.

## Prerequisites

The action requires that the repository has the `development/kv/data/jira` token configured in vault.
This can be done using the SPEED self-service
portal ([more info](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)).

## Inputs

The following inputs can be configured for the action:

| Input                  | Description                                                                                                       | Required | Default |
|------------------------|-------------------------------------------------------------------------------------------------------------------|----------|---------|
| `project_key`          | The project key (e.g., `SONARIAC`).                                                                               | `true`   |         |
| `project_name`         | The display name of the project (e.g., `SonarIaC`). Will be used as the prefix of the resulting release ticket.   | `true`   |         |
| `version`              | The new version string being released (e.g., `1.2.3`).                                                            | `true`   |         |
| `short_description`    | A brief description of the release.                                                                               | `true`   |         |
| `sq_compatibility`     | The SonarQube compatibility version (e.g., `2025.3`).                                                             | `true`   |         |
| `targeted_product`     | The targeted product version (e.g., `11.0`).                                                                      | `false`  |         |
| `use_sandbox`          | Set to `false` to use the Jira production server.                                                                 | `false`  | `true`  |
| `documentation_status` | The status of the release documentation.                                                                          | `false`  | `N/A`   |
| `rule_props_changed`   | Whether rule properties have changed (`Yes` or `No`).                                                             | `false`  | `No`    |
| `jira_release_name`    | The specific Jira release version to use. If omitted and there is only one unreleased version it will release it. | `false`  | `''`    |
| `sonarlint_changelog`  | The SonarLint changelog content.                                                                                  | `false`  | `''`    |
| `skip_release_notes`   | Skip fetching the release notes link completely.                                                                  | `false`  | `false` |

## Outputs

| Output              | Description                                      |
|---------------------|--------------------------------------------------|
| `ticket_key`        | The key of the Jira ticket (e.g., `REL-1234`).   |
| `jira_release_name` | The name of the Jira release used by the action. |
| `ticket_url`        | The URL of the created Jira ticket.              |
| `release_url`       | The URL of the Jira release page.                |

## Example Usage

Here is an example of how to use this action in a workflow. This job will be triggered manually and will create a Jira
release ticket using the provided inputs and secrets from HashiCorp Vault.

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
      targeted_product:
        description: 'Targeted Product'
        required: false
      jira_release_name:
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
      - name: Create Jira Release Ticket
        id: create_ticket
        uses: SonarSource/release-github-actions/.github/actions/create-jira-release-ticket@master
        with:
          project_key: ${{ env.PROJECT_KEY }}
          project_name: ${{ env.PROJECT_NAME }}
          version: ${{ github.event.inputs.version }}
          short_description: ${{ github.event.inputs.short_description }}
          targeted_product: ${{ github.event.inputs.targeted_product }}
          sq_compatibility: ${{ github.event.inputs.sq_compatibility }}
          jira_release_name: ${{ github.event.inputs.jira_release }}
          sonarlint_changelog: ${{ github.event.inputs.sonarlint_changelog }}

      - name: Echo Ticket Details
        run: |
          echo "Ticket Key: ${{ steps.create_ticket.outputs.ticket_key }}"
          echo "Ticket URL: ${{ steps.create_ticket.outputs.ticket_url }}"
          echo "Release Name: ${{ steps.create_ticket.outputs.jira_release_name }}"
          echo "Release URL: ${{ steps.create_ticket.outputs.release_url }}"
```
