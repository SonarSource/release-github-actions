# Publish GitHub Release Action

This GitHub Action automates the creation of a GitHub Release. It can generate release notes by fetching the details directly from a Jira release version, or it can use release notes provided directly as an input.

This action uses the GitHub CLI to create the release and a Python script to interact with the Jira API.

## Prerequisites

To fetch release notes from Jira, the action requires that the repository has the `development/kv/data/jira` token configured in vault.
This can be done using the SPEED self-service portal ([more info](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)).

The action also requires a `github_token` with `contents: write` permissions to create the release. The default `${{ github.token }}` is usually sufficient.

## Inputs

The following inputs can be configured for the action:

| Input                    | Description                                                                                                      | Required | Default               |
|--------------------------|------------------------------------------------------------------------------------------------------------------|----------|-----------------------|
| `github_token`           | The GitHub token for API calls.                                                                                  | `true`   | `${{ github.token }}` |
| `version`                | The version number for the new release (e.g., `v1.0.0`). This will also be the tag name.                         | `true`   |                       |
| `branch`                 | The branch, commit, or tag to create the release from.                                                           | `false`  | `master`              |
| `draft`                  | A boolean value to indicate if the release should be a draft.                                                    | `false`  | `true`                |
| `release_notes`          | The full markdown content for the release notes. If provided, this is used directly, ignoring Jira inputs.       | `false`  | `''`                  |
| `jira_release_name`      | The name of the Jira release version. If provided and `release_notes` is empty, notes will be fetched from Jira. | `false`  | `''`                  |
| `jira_project_key`       | The Jira project key (e.g., "SONARPHP") to fetch notes from. Required if using `jira_release_name`.              | `false`  |                       |
| `jira_user`              | Jira user (email) for authentication. Required if using `jira_release_name`.                                     | `false`  |                       |
| `jira_token`             | Jira API token for authentication. Required if using `jira_release_name`.                                        | `false`  |                       |
| `issue_types`            | Optional comma-separated list of Jira issue types to include in the release notes, in order of appearance.       | `false`  | `''`                  |
| `use_sandbox`            | Set to `false` to use the Jira production server instead of the sandbox.                                         | `false`  | `true`                |
| `wait_for_workflow_name` | The name or file name of the workflow to wait for upon a non-draft release. If empty, this step is skipped.      | `false`  | `sonar-release`       |

## Outputs

| Output        | Description                           |
|---------------|---------------------------------------|
| `release_url` | The URL of the newly created release. |

## Example Usage

Here is an example of how to use this action in a workflow. This job can be triggered manually to publish a new release, with release notes generated from a specified Jira version.

```yaml
name: Publish New Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'The version to release (e.g., v1.2.3)'
        required: true
      jira_release_name:
        description: 'The corresponding release name in Jira'
        required: true

jobs:
  publish_release:
    name: Publish GitHub Release
    runs-on: ubuntu-latest
    permissions:
      contents: write # Required to create a release
      id-token: write # For Vault integration

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Get Jira Credentials from Vault
        id: secrets
        uses: SonarSource/vault-action-wrapper@v3
        with:
          secrets: |
            development/kv/data/jira user | JIRA_USER;
            development/kv/data/jira token | JIRA_TOKEN;

      - name: Publish GitHub Release
        id: publish
        uses: SonarSource/release-github-actions/update-release-ticket-status@master
        with:
          version: ${{ github.event.inputs.version }}
          jira_project_key: 'YOUR_PROJ_KEY'
          jira_release_name: ${{ github.event.inputs.jira_release_name }}
          jira_user: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_USER }}
          jira_token: ${{ fromJSON(steps.secrets.outputs.vault).JIRA_TOKEN }}
          draft: false
          use_sandbox: false

      - name: Print Release URL
        run: echo "Successfully published release at ${{ steps.publish.outputs.release_url }}"
