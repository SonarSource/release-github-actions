# Create Integration Ticket Action

This GitHub Action creates a Jira integration ticket with a custom summary and links it to another existing ticket.

## Description

The action creates an integration ticket in Jira by:
1. Connecting to Jira using authentication credentials
2. Validating that the linked ticket exists and is accessible
3. Creating a new integration ticket with the provided summary and description
4. Linking the new ticket to the existing ticket with the specified link type
5. Returning the ticket key and URL for use in subsequent workflow steps

## Dependencies

This action requires:
- Python 3.x runtime environment
- Jira Python library (jira==3.8.0)

## Inputs

| Input                | Description                                                    | Required | Default      |
|----------------------|----------------------------------------------------------------|----------|--------------|
| `ticket-summary`     | The summary/title for the integration ticket                  | No       | -            |
| `analyzer-name`      | The name of the analyzer (used to generate ticket summary if ticket-summary is not provided) | No       | -            |
| `release-version`    | The release version (used to generate ticket summary if ticket-summary is not provided) | No       | -            |
| `linked-ticket-key`  | The key of the ticket to link to (e.g., REL-123)             | Yes      | -            |
| `jira-project-key`   | The key of the project where the ticket will be created (e.g., SQS) | Yes      | -            |
| `ticket-description` | The description for the integration ticket                     | No       | -            |
| `use-jira-sandbox`   | Use the sandbox Jira server instead of production. Can also be controlled via `USE_JIRA_SANDBOX` environment variable         | No       | `false`      |
| `link-type`          | The type of link to create (e.g., "relates to", "depends on") | No       | `relates to` |

**Note:** Either `ticket-summary` must be provided, or both `analyzer-name` and `release-version` must be provided. If `ticket-summary` is not provided, it will be automatically generated as "Update {analyzer-name} to {release-version}".

## Outputs

| Output       | Description                               |
|--------------|-------------------------------------------|
| `ticket_key` | The key of the created Jira ticket       |
| `ticket_url` | The URL of the created Jira ticket       |

## Environment Variables

| Variable     | Description           | Required |
|--------------|-----------------------|----------|
| `JIRA_USER`  | Your Jira username    | Yes      |
| `JIRA_TOKEN` | Your Jira API token   | Yes      |

## Usage

### Example 1: Using explicit ticket summary
```yaml
- name: Create Integration Ticket
  id: create-ticket
  uses: ./create-integration-ticket
  with:
    ticket-summary: "Update SonarPython analyzer to 5.8.0.24785"
    linked-ticket-key: "REL-456"
    jira-project-key: "SQS"
    ticket-description: "This ticket tracks the integration of SonarPython analyzer version 5.8.0.24785 into the SQS project."
    link-type: "depends on"
  env:
    JIRA_USER: ${{ secrets.JIRA_USER }}
    JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}
```

### Example 2: Using analyzer-name and release-version (generates summary automatically)
```yaml
- name: Create Integration Ticket
  id: create-ticket
  uses: ./create-integration-ticket
  with:
    analyzer-name: "SonarPython"
    release-version: "5.8.0.24785"
    linked-ticket-key: "REL-456"
    jira-project-key: "SQS"
    ticket-description: "This ticket tracks the integration of SonarPython analyzer version 5.8.0.24785 into the SQS project."
    link-type: "depends on"
  env:
    JIRA_USER: ${{ secrets.JIRA_USER }}
    JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}
```

### Using outputs
```yaml
- name: Use ticket outputs
  run: |
    echo "Created ticket: ${{ steps.create-ticket.outputs.ticket-key }}"
    echo "Ticket URL: ${{ steps.create-ticket.outputs.ticket-url }}"
```

## Features

- Creates a Jira ticket in the specified project with a custom summary
- Automatically detects appropriate issue type (Task, Story, or first available)
- Links the created ticket to an existing ticket using the specified link type
- Validates that the linked ticket exists before creating the new ticket
- Supports both production and sandbox Jira instances
- Provides detailed error messages and logging
- Returns ticket key and URL as outputs for use in subsequent workflow steps

## Error Handling

The action will fail if:
- JIRA_USER or JIRA_TOKEN environment variables are not set
- Authentication to Jira fails
- The specified project doesn't exist or isn't accessible
- The linked ticket doesn't exist or isn't accessible
- Ticket creation fails
