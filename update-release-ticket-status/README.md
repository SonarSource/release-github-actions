# Update Release Ticket Status Action

This GitHub Action updates the status of an "Ask for release" ticket in Jira, streamlining the release process by automating ticket transitions and optionally changing assignees.

## Description

The action updates a release ticket in Jira by:
1. Connecting to Jira using authentication credentials from Vault
2. Fetching the specified ticket and validating it exists
3. Optionally assigning the ticket to a new user
4. Transitioning the ticket to the specified status
5. Providing comprehensive error handling and logging

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Jira credentials

## Inputs

| Input                | Description                                                                                                               | Required | Default |
|----------------------|---------------------------------------------------------------------------------------------------------------------------|----------|---------|
| `release-ticket-key` | The key of the Jira ticket to update (e.g., REL-1234)                                                                     | Yes      | -       |
| `status`             | The target status for the ticket. Must be a valid transition (`Start Progress` or `Technical Release Done`)               | Yes      | -       |
| `assignee`           | The email of the user to assign the ticket to                                                                             | No       | -       |
| `use-jira-sandbox`   | Use the sandbox server instead of the production Jira. Can also be controlled via `USE_JIRA_SANDBOX` environment variable | No       | `false` |

## Usage

### Basic usage

```yaml
- name: Update Release Ticket Status
  uses: SonarSource/release-github-actions/update-release-ticket-status@master
  with:
    release-ticket-key: 'REL-1234'
    status: 'Start Progress'
```

### With assignee change

```yaml
- name: Update Release Ticket and Assign
  uses: SonarSource/release-github-actions/update-release-ticket-status@master
  with:
    release-ticket-key: 'REL-5678'
    status: 'Technical Release Done'
    assignee: 'developer@example.com'
```

### Using sandbox environment

```yaml
- name: Update Release Ticket in Sandbox
  uses: SonarSource/release-github-actions/update-release-ticket-status@master
  with:
    release-ticket-key: 'REL-9999'
    status: 'Start Progress'
    use-jira-sandbox: 'true'
```

### Using environment variables

```yaml
- name: Update Release Ticket with Environment Variables
  env:
    USE_JIRA_SANDBOX: 'true'
  uses: SonarSource/release-github-actions/update-release-ticket-status@master
  with:
    release-ticket-key: 'REL-1111'
    status: 'Technical Release Done'
```
## Implementation Details

The action uses a Python script that:
- Authenticates with Jira using credentials from HashiCorp Vault
- Supports both production and sandbox Jira environments via URL selection
- Validates the existence of the specified ticket before attempting updates
- Handles assignee changes with comprehensive error reporting
- Performs status transitions with validation of available transitions
- Provides detailed error messages for troubleshooting

## Valid Status Transitions

| Status                   | Description                                               |
|--------------------------|-----------------------------------------------------------|
| `Start Progress`         | Transitions the ticket to "In Progress" status            |
| `Technical Release Done` | Transitions the ticket to "Technical Release Done" status |

## Error Handling

The action provides detailed error messages for common issues:
- **Ticket not found**: When the specified ticket key doesn't exist
- **Invalid assignee**: When the assignee email is not valid or the user doesn't have permissions
- **Invalid transition**: When the requested status transition is not available from the current status
- **Authentication failure**: When Jira credentials are invalid or expired
- **Connection issues**: When the Jira server is unreachable

## Notes

- This action requires access to SonarSource's HashiCorp Vault for Jira credentials
- The action supports both production and sandbox Jira environments
- Input parameters take precedence over environment variables when both are provided
- The assignee parameter is optional - if not provided, the ticket assignee remains unchanged
- Status transitions are validated against Jira's workflow - invalid transitions will fail with descriptive error messages
