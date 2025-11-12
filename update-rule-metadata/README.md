# Update Rule Metadata Action

This GitHub Action automates updating rule metadata across all supported languages using the rule-api tooling.

## Description

The action performs the following operations:
1. Downloads the specified version of the rule-api JAR file from the SonarSource artifact repository
2. Discovers all directories containing sonarpedia.json files (or processes specified files)
3. Runs the rule-api update command in each directory to update rule metadata
4. Checks for changes and creates a pull request if any updates are made
5. Generates a summary of the updated rules across all languages

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Artifactory credentials
- Java 17 runtime for executing the rule-api JAR
- Git for detecting changes and creating pull requests
- [peter-evans/create-pull-request](https://github.com/peter-evans/create-pull-request) for automated PR creation

## Inputs

| Input              | Description                                                                                                                | Required | Default         |
|--------------------|----------------------------------------------------------------------------------------------------------------------------|----------|-----------------|
| `rule-api-version` | Version of the rule-api tooling to be used for the workflow.                                                               | No       | `2.15.0.4476`   |
| `sonarpedia-files` | Comma-separated list of sonarpedia files to be updated. By default, it will update all Sonarpedia files in the repository. | No       | Auto-discovered |
| `branch`           | Branch to run the check against and create the PR for. By default, it will use master.                                     | No       | `master`        |

## Outputs

| Output             | Description                                                                                               |
|--------------------|-----------------------------------------------------------------------------------------------------------|
| `has-changes`      | Boolean indicating whether any rule metadata changes were detected (from check-changes step)              |
| `summary`          | Summary of the rule metadata updates including rule counts for each language (from generate-summary step) |
| `pull-request-url` | URL of the created pull request (only available if changes were detected, from create-pr step)            |

## Usage

### Required Permissions

```yaml
permissions:
  id-token: write    # Required for SonarSource vault authentication
  contents: write    # Required for checkout and pull request creation
  pull-requests: write # Required for creating pull requests
```

### Basic usage (auto-discover all sonarpedia files)

```yaml
- name: Update Rule Metadata
  uses: SonarSource/release-github-actions/update-rule-metadata@v1
```

### Update specific sonarpedia files

```yaml
- name: Update Rule Metadata
  uses: SonarSource/release-github-actions/update-rule-metadata@v1
  with:
    sonarpedia-files: 'frontend/java/sonarpedia.json,frontend/python/sonarpedia.json'
```

### Use specific rule-api version

```yaml
- name: Update Rule Metadata
  uses: SonarSource/release-github-actions/update-rule-metadata@v1
  with:
    rule-api-version: '2.16.0.5000'
```

### Run against a specific branch

```yaml
- name: Update Rule Metadata
  uses: SonarSource/release-github-actions/update-rule-metadata@v1
  with:
    branch: 'develop'
```

### Complete example with all inputs

```yaml
jobs:
  update-rule-metadata:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: write
      pull-requests: write
    steps:
      - name: Update Rule Metadata
        uses: SonarSource/release-github-actions/update-rule-metadata@v1
        with:
          rule-api-version: '2.16.0.5000'
          sonarpedia-files: 'frontend/java/sonarpedia.json,frontend/csharp/sonarpedia.json'
          branch: 'develop'
```

## Implementation Details

The action uses a bash script that:
- Authenticates with Artifactory using credentials from HashiCorp Vault
- Downloads and caches the specified rule-api JAR version
- Automatically discovers all directories containing sonarpedia.json files (unless specific files are provided)
- Changes into each directory and runs the rule-api update command
- Aggregates logs from all language processing
- Creates a pull request with a summary of changes if any rule metadata updates are detected

## Prerequisites

The action requires that the repository has the `development/artifactory/token/{REPO_OWNER_NAME_DASH}-private-reader` token configured in vault.
This can be done using the SPEED self-service portal ([more info](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)).

The repository must have:
- Proper sonarpedia.json files in language-specific directories
- Write access for creating pull requests
- Java 17 compatible environment (automatically set up by the action)

## Notes

- This action requires access to SonarSource's HashiCorp Vault for Artifactory credentials
- The action automatically discovers all sonarpedia.json files unless specific files are provided
- Pull requests are created with the label `skip-qa` and target the specified branch (defaults to `master`)
- The rule-api JAR is cached to improve performance on subsequent runs
- Changes to sonarpedia.json files themselves are excluded when detecting metadata changes
- The action will fail if no sonarpedia.json files are found to process
