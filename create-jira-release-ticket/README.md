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

| Input                  | Description                                                                                                                                                                                                                                                             | Required | Default |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|---------|
| `project-name`         | The display name of the project (e.g., SonarIaC). Used as the prefix for the release ticket summary                                                                                                                                                                     | Yes      | -       |
| `short-description`    | A short description for the release                                                                                                                                                                                                                                     | Yes      | -       |
| `jira-project-key`     | The key of the Jira project (e.g., SONARIAC). Can also be set via `JIRA_PROJECT_KEY` environment variable                                                                                                                                                               | No*      | -       |
| `version`              | The version being released (e.g., 11.44.2), or leave empty to use the release version                                                                                                                                                                                   | No       | -       |
| `jira-release-id`      | The numeric Jira version ID (e.g., `12345`). Can also be set via `JIRA_RELEASE_ID` environment variable. If not provided, the action will automatically fetch the release ID using `get-jira-release-notes`                                            | No**     | -       |
| `jira-release-url`     | **⚠️ DEPRECATED:** Use `jira-release-id` instead. The full URL to the Jira version page (e.g., `https://sonarsource.atlassian.net/projects/SONARIAC/versions/12345`). The action will extract the version ID from the URL. Can also be set via `JIRA_RELEASE_URL` env var | No       | -       |
| `use-jira-sandbox`     | Use the sandbox server instead of the production Jira. Can also be controlled via `USE_JIRA_SANDBOX` environment variable                                                                                                                                               | No       | `false` |
| `documentation-status` | Status of the documentation                                                                                                                                                                                                                                             | No       | `N/A`   |
| `rule-props-changed`   | Whether rule properties have changed (`Yes` or `No`)                                                                                                                                                                                                                    | No       | `No`    |
| `sonarlint-changelog`  | The SonarLint changelog content                                                                                                                                                                                                                                         | No       | -       |
| `start-progress`       | Whether to start progress on the release ticket after creation                                                                                                                                                                                                          | No       | `false` |

*Either the input or corresponding environment variable must be provided for jira-project-key.
**At least one of `jira-release-id`, `jira-release-url`, `JIRA_RELEASE_ID`, or `JIRA_RELEASE_URL` should be provided, otherwise the action will automatically fetch it.

## Outputs

| Output               | Description                        |
|----------------------|------------------------------------|
| `release-ticket-key` | The key of the created Jira ticket |
| `release-ticket-url` | The URL of the created Jira ticket |

## Environment Variables

### Input Environment Variables

| Variable               | Description                                                                                                                   |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| `JIRA_PROJECT_KEY`     | The Jira project key. Used as fallback when `jira-project-key` input is not provided                                         |
| `JIRA_RELEASE_ID`      | The numeric Jira version ID. Used as fallback when `jira-release-id` input is not provided                  |
| `JIRA_RELEASE_URL`     | **⚠️ DEPRECATED:** Use `JIRA_RELEASE_ID` instead. Full URL to Jira version. Used as fallback when `jira-release-url` not set |
| `USE_JIRA_SANDBOX`     | Whether to use the sandbox Jira instance. Used as fallback when `use-jira-sandbox` input is not provided                     |

### Output Environment Variables

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
    jira-release-id: '12345'  # Numeric version ID from Jira

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
    JIRA_RELEASE_ID: '12345'  # Numeric version ID
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
    jira-release-id: '12345'

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

## Migration Guide: jira-release-url → jira-release-id

### What Changed?

The action now uses a **Jira issue filter URL** instead of linking directly to the Jira release notes page. This provides a more dynamic view of all issues in the release.

**Old Approach:**
- Input: `jira-release-url` with full URL like `https://sonarsource.atlassian.net/projects/SONARIAC/versions/12345`
- Env Var: `JIRA_RELEASE_URL` with full URL
- Result: Linked to static Jira version page

**New Approach:**
- Input: `jira-release-id` with just the numeric ID like `12345`
- Env Var: `JIRA_RELEASE_ID` with just the numeric ID
- Result: Constructs a Jira issue filter URL like `https://sonarsource.atlassian.net/issues/?jql=fixVersion%3D12345`

### Why the Change?

The issue filter URL provides several benefits:
- **More comprehensive**: Displays complete issue details with filters
- **Better integration**: Works seamlessly with Jira's search and filtering capabilities
- **Simpler input**: Only requires the numeric version ID, not the full URL

### How to Migrate

**Before:**
```yaml
- name: Create Release Ticket
  uses: SonarSource/release-github-actions/create-jira-release-ticket@v1
  with:
    jira-release-url: 'https://sonarsource.atlassian.net/projects/SONARIAC/versions/12345'
    # ... other inputs
```

**After:**
```yaml
- name: Create Release Ticket
  uses: SonarSource/release-github-actions/create-jira-release-ticket@v1
  with:
    jira-release-id: '12345'  # Just the numeric ID!
    # ... other inputs
```

### Backward Compatibility

The old `jira-release-url` input and `JIRA_RELEASE_URL` environment variable still work but will generate deprecation warnings. The action automatically extracts the version ID from the URL, so your workflows won't break.

**Example with deprecated input (still works):**
```yaml
- name: Create Release Ticket (deprecated but functional)
  uses: SonarSource/release-github-actions/create-jira-release-ticket@v1
  with:
    jira-release-url: 'https://sonarsource.atlassian.net/projects/SONARIAC/versions/12345'
    # ⚠️ Warning: jira-release-url is deprecated. Please use jira-release-id instead.
```

The action extracts the ID `12345` from the URL automatically, ensuring your existing workflows continue to function.

## Implementation Details

The action uses a Python script that:
- Authenticates with Jira using credentials from HashiCorp Vault
- Supports both production and sandbox Jira environments via URL selection
- Validates required project key from inputs or environment variables
- Accepts either `jira-release-id` (recommended) or extracts the ID from `jira-release-url` (deprecated)
- Constructs a Jira issue filter URL in the format: `https://<jira-url>/issues/?jql=fixVersion%3D<version-id>`
- Creates "Ask for release" tickets with comprehensive custom field mapping
- Optionally starts progress on the created ticket
- Sets environment variables for downstream workflow steps
- Automatically fetches the release ID using `get-jira-release-notes` action if not provided

## Field Mapping

The action populates the following Jira custom fields:

| Field                   | Custom Field ID   | Source Input           | Description                                                                    |
|-------------------------|-------------------|------------------------|--------------------------------------------------------------------------------|
| Short Description       | customfield_10146 | `short-description`    | Brief description of the release                                               |
| Link to Issue Filter    | customfield_10145 | `jira-release-id`      | Jira issue filter URL showing all issues in the release (dynamically generated) |
| Documentation Status    | customfield_10147 | `documentation-status` | Status of documentation for the release                                        |
| Rule Properties Changed | customfield_11263 | `rule-props-changed`   | Whether rule properties were changed (Yes/No)                                  |
| SonarLint Changelog     | customfield_11264 | `sonarlint-changelog`  | Changelog content for SonarLint                                                |

**Note:** The "Link to Issue Filter" field (formerly "Link to Release Notes") now contains a Jira issue filter URL constructed from the version ID, providing a dynamic view of all issues in the release.

## Notes

- This action requires access to SonarSource's HashiCorp Vault for Jira credentials
- Either `jira-project-key` input or `JIRA_PROJECT_KEY` environment variable must be provided
- Use `jira-release-id` input or `JIRA_RELEASE_ID` environment variable with the numeric version ID
- **Deprecated:** `jira-release-url` and `JIRA_RELEASE_URL` are still supported for backward compatibility but will generate deprecation warnings
- If no release ID or URL is provided, the action will automatically fetch the release ID using the `get-jira-release-notes` action
- The action constructs a Jira issue filter URL from the version ID, providing a dynamic view of all issues in the release
- Input parameters take precedence over environment variables when both are provided
- The action supports both production and sandbox Jira environments
- When `version` is not provided, the action automatically uses the release version from the CI environment
- The `start-progress` option automatically transitions the ticket to "Start Progress" status after creation
