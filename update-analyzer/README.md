# Update Analyzer Action

This GitHub Action automates the process of updating an analyzer's version within SonarQube or SonarCloud. It checks out
the respective product repository, modifies the `build.gradle` file with the new version, and opens a pull request with
the changes.

The action determines whether to target SonarQube (`sonar-enterprise`) or SonarCloud (`sonarcloud-core`) based on the
prefix of the provided `ticket` number (`SONAR-` or `SC-`).

## Prerequisites

The `secret_name` provided to the action must have the following permissions for the target repository (e.g.,
`SonarSource/sonar-enterprise`):

* `contents: write`
* `pull-requests: write`

An example PR how to request a token with those permissions can be
found [here](https://github.com/SonarSource/re-terraform-aws-vault/pull/6693).

## Inputs

| Input             | Description                                                                                 | Required | Default  |
|-------------------|---------------------------------------------------------------------------------------------|----------|----------|
| `version`         | The new version to set for the analyzer (e.g., `1.12.0.12345`).                             | `true`   |          |
| `ticket`          | The Jira ticket number. Must start with `SONAR-` (for SonarQube) or `SC-` (for SonarCloud). | `true`   |          |
| `plugin_language` | The language key of the plugin to update (e.g., `architecture`, `java`).                    | `true`   |          |
| `secret_name`     | Name of the secret to fetch from the vault that has access to the target repository.        | `true`   |          |
| `plugin_names`    | Comma-separated list of plugin names to update instead of plugin_language.                  | `false`  |          |
| `base_branch`     | The base branch for the pull request.                                                       | `false`  | `master` |
| `draft`           | A boolean value (`true`/`false`) to control if the pull request is created as a draft.      | `false`  | `false`  |
| `reviewers`       | A comma-separated list of GitHub usernames to request a review from (e.g., `user1,user2`).  | `false`  |          |
| `pr_body`         | The body of the pull request.                                                               | `false`  |          |

## Outputs

| Output   | Description                          |
|----------|--------------------------------------|
| `pr-url` | The URL of the created pull request. |

## Example Usage

Here is an example of how to use this action in a workflow. This workflow can be triggered manually (
`workflow_dispatch`) and uses a secret to provide the required token. The second job demonstrates how to use the
`pr-url` output.

```yaml
# .github/workflows/update-my-analyzer.yml
name: Manually Update Analyzer

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'The new analyzer version (e.g. 1.12.0.12345)'
        required: true
        type: string
      ticket:
        description: 'The Jira ticket number (e.g. SONAR-12345)'
        required: true
        type: string

jobs:
  update-analyzer:
    name: Update PHP Analyzer in SonarQube
    runs-on: ubuntu-latest
    outputs:
      pull_request_url: ${{ steps.update_step.outputs.pr-url }}
    steps:
      - name: Update analyzer and create PR
        id: update_step
        uses: SonarSource/release-github-actions/update-analyzer@master
        with:
          version: ${{ inputs.version }}
          ticket: ${{ inputs.ticket }}
          plugin_language: 'php'
          secret_name: 'sonar-php-release-automation'
          draft: true

  report-pr-url:
    name: Report PR URL
    runs-on: ubuntu-latest
    needs: update-analyzer
    if: needs.update-analyzer.outputs.pull_request_url != ''
    steps:
      - name: Echo the PR URL
        run: |
          echo "Pull request created at: ${{ needs.update-analyzer.outputs.pull_request_url }}"
```

### Using `plugin_names` for Multiple Plugins

You can also update multiple plugins in a single PR by using the `plugin_names` input instead of `plugin_language`:

```yaml
- name: Update multiple analyzers and create PR
  uses: SonarSource/release-github-actions/update-analyzer@master
  with:
    version: ${{ inputs.version }}
    ticket: ${{ inputs.ticket }}
    plugin_names: 'java,kotlin,scala'
    secret_name: 'jvm-release-automation'
```
