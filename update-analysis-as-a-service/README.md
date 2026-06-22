# Update Analysis as a Service Action

This GitHub Action updates analyzer versions in `SonarSource/sonar-analysis-as-a-service` and creates a pull request.

## Description

The action updates `gradle/libs.versions.toml` in Analysis as a Service by:
1. Checking out `SonarSource/sonar-analysis-as-a-service`
2. Resolving version keys from `plugin-name` or `plugin-artifacts`
3. Updating matching `[versions]` entries
4. Creating a pull request with the changes using the specified GitHub token from Vault

## Prerequisites

The `secret-name` provided to the action must have the following permissions on `SonarSource/sonar-analysis-as-a-service`:

* `contents: write`
* `pull-requests: write`

## Inputs

| Input               | Description                                                                                                    | Required | Default  |
|---------------------|----------------------------------------------------------------------------------------------------------------|----------|----------|
| `release-version`   | The new version to set for the analyzer, e.g. `1.12.0.12345`.                                                   | `true`   |          |
| `plugin-name`       | The language key of the plugin to update. Used in the PR title and as the default version-key source.           | `true`   |          |
| `secret-name`       | Name of the Vault secret for a GitHub token with access to `sonar-analysis-as-a-service`.                       | `true`   |          |
| `plugin-artifacts`  | Comma-separated analyzer artifact names to update instead of `plugin-name`.                                     | `false`  |          |
| `base-branch`       | The base branch for the pull request.                                                                          | `false`  | `master` |
| `draft`             | Whether to create the pull request as a draft.                                                                  | `false`  | `false`  |
| `reviewers`         | A comma-separated list of GitHub usernames to request a review from.                                            | `false`  |          |
| `pull-request-body` | The body of the pull request.                                                                                  | `false`  |          |

## Outputs

| Output             | Description                          |
|--------------------|--------------------------------------|
| `pull-request-url` | The URL of the created pull request. |

## Version Key Resolution

For each artifact, the action strips a `-enterprise` suffix and then resolves version keys in this order:

1. For artifacts already starting with `sonar-` and not ending with `-plugin`, `{artifact}-plugin`
2. For artifacts already starting with `sonar-`, the exact artifact key
3. For other artifacts not ending with `-plugin`, `sonar-{artifact}-plugin`
4. For other artifacts, `sonar-{artifact}`

For example:

* `dre` updates `sonar-dre`
* `java` updates `sonar-java-plugin`
* `java-symbolic-execution` updates `sonar-java-symbolic-execution-plugin`
* `go-enterprise` updates `sonar-go`

## Usage

```yaml
- name: Update Analysis as a Service
  uses: SonarSource/release-github-actions/update-analysis-as-a-service@v1
  with:
    release-version: '1.12.0.12345'
    plugin-name: 'dre'
    secret-name: 'sonar-dre-release-automation'
```

### Updating multiple version keys

```yaml
- name: Update Analysis as a Service
  uses: SonarSource/release-github-actions/update-analysis-as-a-service@v1
  with:
    release-version: '8.25.0.42802'
    plugin-name: 'java'
    plugin-artifacts: 'java,java-symbolic-execution'
    secret-name: 'sonar-java-release-automation'
```
