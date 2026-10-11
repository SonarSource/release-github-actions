# Update Analyzer Action

This GitHub Action automates the process of updating an analyzer's version within SonarQube. It checks out the `sonar-enterprise` repository, modifies the `build.gradle` file with the new version, and creates a pull request with the changes.

## Description

The action updates analyzer versions by:
1. Checking out the `sonar-enterprise` repository
2. Updating the analyzer version in the build.gradle file using sed commands
3. Creating a pull request with the changes using the specified GitHub token from Vault

## Prerequisites

The `secret-name` provided to the action must have the following permissions for the target repository (e.g., `SonarSource/sonar-enterprise`):

* `contents: write`
* `pull-requests: write`

An example PR how to request a token with those permissions can be found [here](https://github.com/SonarSource/re-terraform-aws-vault/pull/6693).

## Dependencies

This action depends on:
- [SonarSource/vault-action-wrapper@v3](https://github.com/SonarSource/vault-action-wrapper) for secure token retrieval
- [actions/checkout@v4](https://github.com/actions/checkout) for repository checkout
- [SonarSource/release-github-actions/create-pull-request](../create-pull-request) for pull request creation

## Inputs

| Input               | Description                                                                                                                                                                                                                                                           | Required | Default  |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|----------|
| `release-version`   | The new version to set for the analyzer (e.g., `1.12.0.12345`).                                                                                                                                                                                                       | `true`   |          |
| `ticket-key`        | The Jira ticket number. Must start with `SONAR-`.                                                                                                                                                                                                                     | `true`   |          |
| `plugin-name`       | The language key of the plugin to update. It will always be used as a part of the PR title and commit message. It can be used to match the artifact in the build script (i.e. it should be the `X` in `sonar-X-plugin`, or the full artifact name when `set-sonar-prefix` is `false`), unless `plugin-artifacts` input is provided. | `true`   |          |
| `secret-name`       | Name of the secret for GitHub token to fetch from the vault that has permissions to create pull requests in the target Github repository.                                                                                                                             | `true`   |          |
| `plugin-artifacts`  | Comma-separated list of plugin artifact names (any `X` in `sonar-X-plugin`, or full artifact names when `set-sonar-prefix` is `false`) that will be used instead of `plugin-name` when provided.                                                                       | `false`  |          |
| `set-sonar-prefix`  | Whether the artifact follows the `sonar-X-plugin` naming convention (`true`/`false`). When `false`, `plugin-name` / `plugin-artifacts` are matched verbatim in the build file (e.g. `java-a3s-context-collector`). Must be `true` or `false`; any other value fails the action. | `false`  | `true`   |
| `base-branch`       | The base branch for the pull request.                                                                                                                                                                                                                                 | `false`  | `master` |
| `draft`             | A boolean value (`true`/`false`) to control if the pull request is created as a draft. When `true`, the commit message is prefixed with `[DO NOT MERGE]` instead of the ticket key.                                                                                   | `false`  | `false`  |
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
  uses: SonarSource/release-github-actions/update-analyzer@v1
  with:
    release-version: '1.12.0.12345'
    ticket-key: 'SONAR-12345'
    plugin-name: 'php'
    secret-name: 'sonar-php-release-automation'
```

### With draft pull request

```yaml
- name: Update Analyzer
  uses: SonarSource/release-github-actions/update-analyzer@v1
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
  uses: SonarSource/release-github-actions/update-analyzer@v1
  with:
    release-version: '1.12.0.12345'
    ticket-key: 'SONAR-67890'
    plugin-name: 'java'
    secret-name: 'sonar-java-release-automation'
    base-branch: 'develop'
    reviewers: 'user1,user2'
    pull-request-body: 'This PR updates the Java analyzer to the latest version.'
```

### Artifact matching

| Inputs                                                        | Pattern matched in `build.gradle`   |
|---------------------------------------------------------------|-------------------------------------|
| `plugin-name: java`                                           | `:sonar-java.*-plugin:`             |
| `plugin-artifacts: java,kotlin`                               | `:sonar-java-plugin:`, `:sonar-kotlin-plugin:` |
| `plugin-name: java-a3s-context-collector`, `set-sonar-prefix: false` | `:java-a3s-context-collector:` |

General rule: the plugin name (or each entry of `plugin-artifacts`) is wrapped as
`sonar-X-plugin` when `set-sonar-prefix` is `true` (the default). When only `plugin-name` is
given, a `.*` wildcard is inserted so a whole plugin family is matched (e.g. `java` also covers
`sonar-java-symbolic-execution-plugin`).

Artifacts that do **not** follow the `sonar-X-plugin` convention (e.g.
`java-a3s-context-collector`) must be updated by passing `set-sonar-prefix: false`, in which case
the name is matched exactly, with no prefix, suffix or wildcard added.

### Plugin not following the sonar-X-plugin convention

```yaml
- name: Update Analyzer
  uses: SonarSource/release-github-actions/update-analyzer@v1
  with:
    release-version: '1.0.0.100'
    ticket-key: 'SONAR-12345'
    plugin-name: 'java-a3s-context-collector'
    set-sonar-prefix: false
    secret-name: 'sonar-java-release-automation'
```

### Using plugin-artifacts for multiple plugins

```yaml
- name: Update Multiple Analyzers
  uses: SonarSource/release-github-actions/update-analyzer@v1
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
- Validates the ticket prefix
- Uses sparse checkout for efficient repository cloning (only the build.gradle file)
- Updates analyzer versions using sed pattern matching for `sonar-X-plugin` artifacts, or for the
  verbatim artifact name when `set-sonar-prefix` is `false`
- Creates pull requests with standardized naming conventions and commit messages
- Supports both single plugin updates and multiple plugin artifacts in one PR

The build-file rewrite lives in [`update_build_gradle.sh`](update_build_gradle.sh), driven by the
`PLUGIN_NAME`, `PLUGIN_ARTIFACTS`, `SET_SONAR_PREFIX`, `RELEASE_VERSION` and `BUILD_GRADLE_FILE`
environment variables. Run its unit tests with:

```bash
bash update-analyzer/test_update_build_gradle.sh
```

## Error Handling

The action will fail with a non-zero exit code if:
- The ticket format is invalid (doesn't start with `SONAR-`)
- `set-sonar-prefix` is set to anything other than `true` or `false`
- The Vault token retrieval fails
- The target repository checkout fails
- The build.gradle file modification fails
- The pull request creation fails

## Notes

- This action specifically targets the `sonar-enterprise` repository
- The action uses sparse checkout to minimize data transfer and processing time
- Branch naming follows the pattern: `{plugin-name}/update-analyzer-{release-version}`
- Commit messages and PR titles follow standardized formats for consistency
- The action supports both individual plugin updates and batch updates for multiple related plugins
- All GitHub tokens are securely retrieved from HashiCorp Vault using the SonarSource wrapper action
