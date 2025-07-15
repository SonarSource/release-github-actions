# Update Jira Release Ticket Status Action

This GitHub Action automates updating the status of an "Ask for release" ticket in Jira. It can also be used to change the assignee of the ticket.

## Prerequisites

The action requires that the repository needs to have the `development/kv/data/jira` token configured in vault.
This can done using the SPEED self-service portal ([more info](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)).

## Inputs

| Input         | Description                                                                     | Required | Default |
|---------------|---------------------------------------------------------------------------------|----------|---------|
| `jira_user`   | The Jira user (email) for authentication.                                       | `true`   |         |
| `jira_token`  | The Jira API token for authentication.                                          | `true`   |         |
| `ticket_key`  | The key of the Jira ticket to update (e.g., `REL-1234`).                        | `true`   |         |
| `status`      | The target status. Possible values: `Start Progress`, `Technical Release Done`. | `true`   |         |
| `assignee`    | The email of the user to assign the ticket to.                                  | `false`  | `''`    |
| `use_sandbox` | Set to `false` to use the Jira production server.                               | `false`  | `true`  |

## Example Usage

Here is an example of how to use this action in a workflow. This step would typically run after a release ticket has been created.

```yaml
name: Update Release Ticket

on:
  workflow_dispatch:
    inputs:
      ticket_key:
        description: 'Jira Ticket Key to update'
        required: true
      new_status:
        description: 'New status for the ticket'
        required: true
        type: choice
        options:
        - Start Progress
        - Technical Release Done
      assignee_email:
        description: 'Email of the new assignee (optional)'
        required: false

jobs:
  update_release_ticket:
    name: Update release ticket
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

      - name: Update Jira Release Ticket
        uses: SonarSource/release-github-actions/update-release-ticket-status@v1
        with:
          jira_user: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_USER }}
          jira_token: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_TOKEN }}
          ticket_key: ${{ github.event.inputs.ticket_key }}
          status: ${{ github.event.inputs.new_status }}
          assignee: ${{ github.event.inputs.assignee_email }}

      - name: Echo Status
        run: echo "Successfully updated ticket ${{ github.event.inputs.ticket_key }} to status ${{ github.event.inputs.new_status }}."