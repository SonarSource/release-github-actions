# Update integrations tickets Action

This GitHub Action automates the process of finding and updating Jira integration tickets.

The action finds both a SonarQube (SQS) integration ticket and a SonarCloud (SC) integration ticket by searching for tickets linked to a specified release ticket. It can then optionally update the `fixVersions` field of the found SQS ticket. If updating the `fixVersions` fails (e.g., due to a non-existent version), it will issue a warning without failing the action.

## Prerequisites

The action requires that the repository has the `development/kv/data/jira` token configured in vault.
This can be done using the SPEED self-service portal ([more info](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)).

## Inputs

| Input                | Description                                                                                         | Required | Default |
|----------------------|-----------------------------------------------------------------------------------------------------|----------|---------|
| `jira_user`          | The Jira user (email) for authentication.                                                           | `true`   |         |
| `jira_token`         | The Jira API token for authentication.                                                              | `true`   |         |
| `release_ticket_key` | The key of the release ticket (e.g., `REL-1234`) to find the linked integration tickets from.       | `true`   |         |
| `sqs_project_key`    | The Jira project key to search for the linked SQS integration ticket.                               | `false`  | `SONAR` |
| `sc_project_key`     | The Jira project key to search for the linked SC integration ticket.                                | `false`  | `SC`    |
| `sqs_fix_versions`   | A comma-separated list of fix versions to set on the SQS integration ticket (e.g., `"10.1, 10.2"`). | `false`  |         |
| `use_sandbox`        | Set to `false` to use the Jira production server.                                                   | `false`  | `true`  |

## Outputs

| Output           | Description                                                        |
|------------------|--------------------------------------------------------------------|
| `sqs_ticket_key` | The key of the SQS integration ticket that was found.              |
| `sc_ticket_key`  | The key of the SC integration ticket that was found.               |

## Example Usage

Here is an example of how to use this action in a workflow. This job will be triggered manually, find the linked SQS and SC tickets, and update the SQS ticket's fix versions.

```yaml
name: Update Integration Tickets

on:
  workflow_dispatch:
    inputs:
      release_ticket:
        description: 'Release Ticket Key (e.g., REL-1234)'
        required: true
      fix_versions:
        description: 'Optional comma-separated fix versions for the SONAR ticket'
        required: false

jobs:
  update-integration-tickets:
    name: Find and Update Integration Tickets
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

      - name: Find and Update Tickets
        id: integration_update
        uses: SonarSource/release-github-actions/update-integration-tickets@master
        with:
          jira_user: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_USER }}
          jira_token: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_TOKEN }}
          release_ticket_key: ${{ github.event.inputs.release_ticket }}
          sqs_fix_versions: ${{ github.event.inputs.fix_versions }}

      - name: Echo Found Ticket Keys
        run: |
          echo "Found SQS integration ticket: ${{ steps.integration_update.outputs.sqs_ticket_key }}"
          echo "Found SC integration ticket: ${{ steps.integration_update.outputs.sc_ticket_key }}"
