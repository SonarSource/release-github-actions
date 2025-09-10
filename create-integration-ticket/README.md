# Create Integration Ticket Action

This GitHub Action creates a Jira integration ticket with a custom summary and links it to another existing ticket.

## Description

The action creates an integration ticket in Jira by:
1. Connecting to Jira using authentication credentials
2. Validating that the release ticket exists and is accessible
3. Creating a new integration ticket with the provided summary
4. Setting the description on the ticket (if provided)
5. Linking the new ticket to the existing ticket with the specified link type
6. Returning the ticket key and URL for use in subsequent workflow steps

## Dependencies

This action requires:
- Python 3.x runtime environment
- Jira Python library (jira==3.8.0)

## Inputs

| Input                 | Description                                                                                                                               | Required | Default      |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------|----------|--------------|
| `release-ticket-key`  | The key of the ticket to link to (e.g., REL-123)                                                                                          | Yes      | -            |
| `target-jira-project` | The key of the project where the ticket will be created (e.g., SQS)                                                                       | Yes      | -            |
| `ticket-summary`      | The summary/title for the integration ticket                                                                                              | No       | -            |
| `ticket-description`  | Description for the integration ticket                                                                                                    | No       | -            |
| `plugin-name`         | The name of the plugin (used to generate ticket summary if ticket-summary is not provided)                                                | No       | -            |
| `release-version`     | The release version (used to generate ticket summary if ticket-summary is not provided). If not set version will be retreived from build. | No       | -            |
| `use-jira-sandbox`    | Use the sandbox Jira server instead of production. Can also be controlled via `USE_JIRA_SANDBOX` environment variable                     | No       | -            |
| `link-type`           | The type of link to create (e.g., "relates to", "depends on")                                                                             | No       | `relates to` |
| `jira-release-url`    | Jira release URL to append to ticket description                                                                                          | No       | -            |

**Note:** Either `ticket-summary` must be provided, or both `plugin-name` and `release-version` must be provided. If `ticket-summary` is not provided, it will be automatically generated as "Update {plugin-name} to {release-version}".

## Outputs

| Output       | Description                        |
|--------------|------------------------------------|
| `ticket-key` | The key of the created Jira ticket |
| `ticket-url` | The URL of the created Jira ticket |

## Usage

### Example 1: Using explicit ticket summary with description
```yaml
- name: Create Integration Ticket
  id: create-ticket
  uses: SonarSource/release-github-actions/create-integration-ticket@v1
  with:
    ticket-summary: "Update SonarPython analyzer to 5.8.0.24785"
    ticket-description: "This ticket tracks the integration of SonarPython analyzer version 5.8.0.24785 into our platform. Please ensure all tests pass before closing."
    release-ticket-key: "REL-456"
    target-jira-project: "SQS"
    link-type: "depends on"
```

### Example 2: Using plugin-name and release-version (generates summary automatically)
```yaml
- name: Create Integration Ticket
  id: create-ticket
  uses: SonarSource/release-github-actions/create-integration-ticket@v1
  with:
    plugin-name: "SonarPython"
    release-version: "5.8.0.24785"
    release-ticket-key: "REL-456"
    target-jira-project: "SQS"
    link-type: "depends on"
```

### Example 3: Simple integration ticket (without description)
```yaml
- name: Create Integration Ticket
  id: create-ticket
  uses: SonarSource/release-github-actions/create-integration-ticket@v1
  with:
    ticket-summary: "Simple integration ticket"
    release-ticket-key: "REL-456"
    target-jira-project: "SQS"
```

### Example 4: Using with Jira release URL
```yaml
- name: Create Integration Ticket
  id: create-ticket
  uses: SonarSource/release-github-actions/create-integration-ticket@v1
  with:
    plugin-name: "SonarPython"
    release-version: "5.8.0.24785"
    ticket-description: "This release includes bug fixes and performance improvements."
    jira-release-url: "https://sonarsource.atlassian.net/projects/SONARPY/versions/22345/tab/release-report-all-issues"
    release-ticket-key: "REL-456"
    target-jira-project: "SQS"
```

### Using outputs
```yaml
- name: Use ticket outputs
  run: |
    echo "Created ticket: ${{ steps.create-ticket.outputs.ticket-key }}"
    echo "Ticket URL: ${{ steps.create-ticket.outputs.ticket-url }}"
```

## Features

- Creates a Jira ticket in the specified project with optional description
- Automatically detects appropriate issue type (Task, Improvement, or first available)
- Links the created ticket to an existing ticket using the specified link type
- Validates that the release ticket exists before creating the new ticket
- Gracefully handles description field limitations (warns if description cannot be set but continues)
- Supports both production and sandbox Jira instances
- Provides detailed error messages and logging
- Returns ticket key and URL as outputs for use in subsequent workflow steps

## Error Handling

The action will fail if:
- Authentication to Jira fails
- The specified project doesn't exist or isn't accessible
- The release ticket doesn't exist or isn't accessible
- Ticket creation fails

The action will continue but warn if:
- The description field cannot be set (due to project configuration or permissions)
- Ticket linking fails (the ticket is still created successfully)
