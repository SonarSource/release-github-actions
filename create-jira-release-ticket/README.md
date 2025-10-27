# Create Jira Release Ticket Action

This GitHub Action creates an "Ask for release" ticket in Jira, streamlining the release process by automatically creating standardized release tickets with all required information.

## Description

The action creates a release ticket in Jira by:
1. Connecting to Jira using authentication credentials from Vault
2. Validating required project key and automatically fetching release URL if not provided
3. Creating an "Ask for release" ticket with custom fields populated
4. Optionally starting progress on the created ticket
5. Setting environment variables for use in subsequent workflow steps

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Jira credentials
- [SonarSource/release-github-actions/get-release-version](https://github.com/SonarSource/release-github-actions) when version is not provided
- [SonarSource/release-github-actions/update-release-ticket-status](https://github.com/SonarSource/release-github-actions) when start-progress is enabled
- [SonarSource/release-github-actions/get-jira-release-notes](https://github.com/SonarSource/release-github-actions) when neither jira-release-url nor JIRA_RELEASE_URL are provided

## Inputs

| Input                  | Description                                                                                                                                                                                                     | Required | Default |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|---------|
| `project-name`         | The display name of the project (e.g., SonarIaC). Used as the prefix for the release ticket summary                                                                                                             | Yes      | -       |
| `short-description`    | A short description for the release                                                                                                                                                                             | Yes      | -       |
| `jira-project-key`     | The key of the Jira project (e.g., SONARIAC). Can also be set via `JIRA_PROJECT_KEY` environment variable                                                                                                       | No*      | -       |
| `version`              | The version being released (e.g., 11.44.2), or leave empty to use the release version                                                                                                                           | No       | -       |
| `due-date`             | Due date of the release                                                                                                                                                                                         | No       | -       |
| `use-jira-sandbox`     | Use the sandbox server instead of the production Jira. Can also be controlled via `USE_JIRA_SANDBOX` environment variable                                                                                       | No       | `false` |
| `documentation-status` | Status of the documentation                                                                                                                                                                                     | No       | `N/A`   |
| `rule-props-changed`   | Whether rule properties have changed (`Yes` or `No`)                                                                                                                                                            | No       | `No`    |
| `jira-release-url`     | The URL to the Jira release notes page. Can also be set via `JIRA_RELEASE_URL` environment variable. If neither is provided, the action will automatically fetch the release URL using `get-jira-release-notes` | No       | -       |
| `sonarlint-changelog`  | The SonarLint changelog content                                                                                                                                                                                 | No       | -       |
| `start-progress`       | Whether to start progress on the release ticket after creation                                                                                                                                                  | No       | `false` |

*Either the input or corresponding environment variable must be provided for jira-project-key.

## Outputs

| Output               | Description                        |
|----------------------|------------------------------------|
| `release-ticket-key` | The key of the created Jira ticket |
| `release-ticket-url` | The URL of the created Jira ticket |

## Environment Variables

| Variable             | Description                        |
|----------------------|------------------------------------|
| `RELEASE_TICKET_KEY` | The key of the created Jira ticket |
| `RELEASE_TICKET_URL` | The URL of the created Jira ticket |

## Usage

### Basic usage with explicit values

```yaml
- name: Create Jira Release Ticket
  id: create-ticket
  uses: SonarSource/release-github-actions/create-jira-release-ticket@v1
  with:
    jira-project-key: 'SONARIAC'
    project-name: 'SonarIaC'
    version: '11.44.2'
    short-description: 'Bug fixes and performance improvements'
    jira-release-url: 'https://sonarsource.atlassian.net/projects/SONARIAC/versions/12345'

- name: Use created ticket
  run: |
    echo "Created ticket: ${{ steps.create-ticket.outputs.release-ticket-key }}"
    echo "Ticket URL: ${{ steps.create-ticket.outputs.release-ticket-url }}"
```

### Using environment variables

```yaml
- name: Create Jira Release Ticket
  uses: SonarSource/release-github-actions/create-jira-release-ticket@v1
  env:
    JIRA_PROJECT_KEY: 'SONARIAC'
    JIRA_RELEASE_URL: 'https://sonarsource.atlassian.net/projects/SONARIAC/versions/12345'
  with:
    project-name: 'SonarIaC'
    short-description: 'Major release with new features'
    rule-props-changed: 'Yes'
```

### Using sandbox environment

```yaml
- name: Create Jira Release Ticket in Sandbox
  uses: SonarSource/release-github-actions/create-jira-release-ticket@v1
  with:
    project-name: 'Test Project'
    short-description: 'Beta release for testing'
    use-jira-sandbox: 'true'
```

### With automatic progress start

```yaml
- name: Create and Start Release Ticket
  uses: SonarSource/release-github-actions/create-jira-release-ticket@v1
  with:
    project-name: 'SonarIaC'
    short-description: 'Quarterly release'
    start-progress: 'true'
```

### Using environment variables in subsequent steps

```yaml
- name: Create Jira Release Ticket
  uses: SonarSource/release-github-actions/create-jira-release-ticket@v1
  with:
    jira-project-key: 'SONARIAC'
    project-name: 'SonarIaC'
    short-description: 'Release with environment variable usage'
    jira-release-url: 'https://sonarsource.atlassian.net/projects/SONARIAC/versions/12345'

- name: Post to Slack
  run: |
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"Release ticket created: '"$RELEASE_TICKET_KEY"' - '"$RELEASE_TICKET_URL"'"}' \
      ${{ secrets.SLACK_WEBHOOK_URL }}

- name: Update GitHub Release
  run: |
    gh release create v${{ inputs.version }} \
      --title "Release ${{ inputs.version }}" \
      --notes "Jira ticket: $RELEASE_TICKET_URL"
```

## Implementation Details

The action uses a Python script that:
- Authenticates with Jira using credentials from HashiCorp Vault
- Supports both production and sandbox Jira environments via URL selection
- Validates required project key from inputs or environment variables, and automatically fetches release URL if not provided
- Creates "Ask for release" tickets with comprehensive custom field mapping
- Optionally starts progress on the created ticket
- Sets environment variables for downstream workflow steps

## Field Mapping

The action populates the following Jira custom fields:

| Field                   | Custom Field ID   | Source Input           |
|-------------------------|-------------------|------------------------|
| Short Description       | customfield_10146 | `short-description`    |
| Link to Release Notes   | customfield_10145 | `jira-release-url`     |
| Documentation Status    | customfield_10147 | `documentation-status` |
| Rule Properties Changed | customfield_11263 | `rule-props-changed`   |
| SonarLint Changelog     | customfield_11264 | `sonarlint-changelog`  |

## Notes

- This action requires access to SonarSource's HashiCorp Vault for Jira credentials
- Either `jira-project-key` input or `JIRA_PROJECT_KEY` environment variable must be provided
- If neither `jira-release-url` input nor `JIRA_RELEASE_URL` environment variable is provided, the action will automatically fetch the release URL using the `get-jira-release-notes` action
- Input parameters take precedence over environment variables when both are provided
- The action supports both production and sandbox Jira environments
- When `version` is not provided, the action automatically uses the release version from the CI environment
- The `start-progress` option automatically transitions the ticket to "Start Progress" status after creation
