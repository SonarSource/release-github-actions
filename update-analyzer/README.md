# Update Analyzer Action

This GitHub Action automates the process of updating an analyzer's version within SonarQube or SonarCloud. It checks out the respective product repository, modifies the `build.gradle` file with the new version, and creates a pull request with the changes.

## Description

The action updates analyzer versions by:
1. Determining the target repository based on the ticket prefix (`SONAR-` for SonarQube or `SC-` for SonarCloud)
2. Checking out the appropriate product repository (`sonar-enterprise` or `sonarcloud-core`)
3. Updating the analyzer version in the build.gradle file using sed commands
4. Creating a pull request with the changes using the specified GitHub token from Vault

## Prerequisites

The `secret-name` provided to the action must have the following permissions for the target repository (e.g., `SonarSource/sonar-enterprise`):

* `contents: write`
* `pull-requests: write`

An example PR how to request a token with those permissions can be found [here](https://github.com/SonarSource/re-terraform-aws-vault/pull/6693).

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper@v3](https://github.com/SonarSource/vault-action-wrapper) for secure token retrieval
- [actions/checkout@v4](https://github.com/actions/checkout) for repository checkout
- [peter-evans/create-pull-request@v6](https://github.com/peter-evans/create-pull-request) for pull request creation

## Inputs

| Input               | Description                                                                                                                                                                                                                                                           | Required | Default  |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|----------|
| `release-version`   | The new version to set for the analyzer (e.g., `1.12.0.12345`).                                                                                                                                                                                                       | `true`   |          |
| `ticket-key`        | The Jira ticket number. Must start with `SONAR-` (for SonarQube) or `SC-` (for SonarCloud).                                                                                                                                                                           | `true`   |          |
| `plugin-name`       | The language key of the plugin to update. It will always be used as a part of the PR title and commit message. It can be used to match the artifact in the build script (i.e. it should be the `X` in `sonar-X-plugin`), unless `plugin-artifacts` input is provided. | `true`   |          |
| `secret-name`       | Name of the secret for GitHub token to fetch from the vault that has permissions to create pull requests in the target Github repository.                                                                                                                             | `true`   |          |
| `plugin-artifacts`  | Comma-separated list of plugin artifact names (any `X` in `sonar-X-plugin`) that will be used instead of `plugin-name` when provided.                                                                                                                                 | `false`  |          |
| `base-branch`       | The base branch for the pull request.                                                                                                                                                                                                                                 | `false`  | `master` |
| `draft`             | A boolean value (`true`/`false`) to control if the pull request is created as a draft.                                                                                                                                                                                | `false`  | `false`  |
| `reviewers`         | A comma-separated list of GitHub usernames to request a review from (e.g., `user1,user2`).                                                                                                                                                                            | `false`  |          |
| `pull-request-body` | The body of the pull request.                                                                                                                                                                                                                                         | `false`  |          |

## Outputs

| Output             | Description                          |
|--------------------|--------------------------------------|
| `pull-request-url` | The URL of the created pull request. |

## Usage

### Basic usage

```yaml
- name: Update Analyzer
  uses: SonarSource/release-github-actions/update-analyzer@master
  with:
    release-version: '1.12.0.12345'
    ticket-key: 'SONAR-12345'
    plugin-name: 'php'
    secret-name: 'sonar-php-release-automation'
```

### With draft pull request

```yaml
- name: Update Analyzer
  uses: SonarSource/release-github-actions/update-analyzer@master
  with:
    release-version: '1.12.0.12345'
    ticket-key: 'SONAR-12345'
    plugin-name: 'php'
    secret-name: 'sonar-php-release-automation'
    draft: true
```

### With custom base branch and reviewers

```yaml
- name: Update Analyzer
  uses: SonarSource/release-github-actions/update-analyzer@master
  with:
    release-version: '1.12.0.12345'
    ticket-key: 'SC-67890'
    plugin-name: 'java'
    secret-name: 'sonar-java-release-automation'
    base-branch: 'develop'
    reviewers: 'user1,user2'
    pull-request-body: 'This PR updates the Java analyzer to the latest version.'
```

### Using plugin-artifacts for multiple plugins

```yaml
- name: Update Multiple Analyzers
  uses: SonarSource/release-github-actions/update-analyzer@master
  with:
    release-version: '1.12.0.12345'
    ticket-key: 'SONAR-12345'
    plugin-name: 'jvm'
    plugin-artifacts: 'java,kotlin,scala'
    secret-name: 'jvm-release-automation'
```

## Implementation Details

The action uses a composite action that:
- Uses the SonarSource Vault action wrapper to securely retrieve GitHub tokens
- Determines the target repository based on ticket prefix validation
- Uses sparse checkout for efficient repository cloning (only the build.gradle file)
- Updates analyzer versions using sed pattern matching for `sonar-X-plugin` artifacts
- Creates pull requests with standardized naming conventions and commit messages
- Supports both single plugin updates and multiple plugin artifacts in one PR

## Error Handling

The action will fail with a non-zero exit code if:
- The ticket format is invalid (doesn't start with `SONAR-` or `SC-`)
- The Vault token retrieval fails
- The target repository checkout fails
- The build.gradle file modification fails
- The pull request creation fails

## Notes

- This action specifically targets SonarSource product repositories (`sonar-enterprise` and `sonarcloud-core`)
- The action uses sparse checkout to minimize data transfer and processing time
- Branch naming follows the pattern: `{plugin-name}/update-analyzer-{release-version}`
- Commit messages and PR titles follow standardized formats for consistency
- The action supports both individual plugin updates and batch updates for multiple related plugins
- All GitHub tokens are securely retrieved from HashiCorp Vault using the SonarSource wrapper action
