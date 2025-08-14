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
| `short_description`    | A brief description of the release.                                                                               | `true`   |         |
| `sq_compatibility`     | The SonarQube compatibility version (e.g., `2025.3`).                                                             | `true`   |         |
| `version`              | The version being released (e.g., `1.2.3`), or leave empty to use the build number.                              | `false`  |         |
| `targeted_product`     | The targeted product version (e.g., `11.0`).                                                                      | `false`  |         |
| `use_sandbox`          | Set to `false` to use the Jira production server.                                                                 | `false`  | `true`  |
| `documentation_status` | Status of the documentation.                                                                                      | `false`  | `N/A`   |
| `rule_props_changed`   | Whether rule properties have changed (`Yes` or `No`).                                                             | `false`  | `No`    |
| `jira_release_name`    | The specific Jira release version to use. If not provided, will auto-detect the single unreleased version.       | `false`  |         |
| `sonarlint_changelog`  | The SonarLint changelog content.                                                                                  | `false`  |         |
| `start_progress`       | Whether to start progress on the release ticket after creation.                                                   | `false`  | `false` |

## Outputs

| Output              | Description                                      |
|---------------------|--------------------------------------------------|
| `ticket_key`        | The key of the Jira ticket (e.g., `REL-1234`).   |
| `jira_release_name` | The name of the Jira release used by the action. |
| `ticket_url`        | The URL of the created Jira ticket.              |
| `release_url`       | The URL of the Jira release page.                |

## Environment Variables

The action also sets the following environment variables that can be used in subsequent workflow steps:

| Variable              | Description                                      |
|-----------------------|--------------------------------------------------|
| `RELEASE_TICKET_KEY`  | The key of the created Jira ticket (e.g., `REL-1234`). |
| `JIRA_RELEASE_NAME`   | The name of the Jira release used by the action. |
| `RELEASE_TICKET_URL`  | The URL of the created Jira ticket.              |
| `JIRA_RELEASE_URL`    | The URL of the Jira release page.                |

## Example Usage

Here is an example of how to use this action in a workflow. This job will be triggered manually and will create a Jira
release ticket using the provided inputs and secrets from HashiCorp Vault.

```yaml
on:
  workflow_dispatch:
    inputs:
      version:
        required: true
      short_description:
        required: true
      sq_compatibility:
        required: true

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
          project_key: 'SONARIAC'
          project_name: 'SonarIaC'
          version: ${{ github.event.inputs.version }}
          short_description: ${{ github.event.inputs.short_description }}
          sq_compatibility: ${{ github.event.inputs.sq_compatibility }}

      - name: Echo Ticket Details
        run: |
          echo "Ticket Key: ${{ steps.create_ticket.outputs.ticket_key }}"
          echo "Ticket URL: ${{ steps.create_ticket.outputs.ticket_url }}"
          echo "Release Name: ${{ steps.create_ticket.outputs.jira_release_name }}"
          echo "Release URL: ${{ steps.create_ticket.outputs.release_url }}"
```
