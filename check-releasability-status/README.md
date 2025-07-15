# Check Releasability Status Action

This GitHub Action checks the releasability status of the master branch. If the check was successful, it extracts the version number from its annotation. It's important to note that this action doesn't run the releasability status check itself but rather finds previous runs. The action is designed to be a prerequisite step in a release workflow, ensuring that a version is ready to be released before proceeding.

The action is self-contained and uses the `actions/github-script` toolkit to interact with the GitHub Checks API.

## Prerequisites

The action requires that the workflow has `checks: read` permissions for the `GITHUB_TOKEN` to be able to access the Checks API.

## Inputs

The following inputs can be configured for the action:

| Input          | Description                        | Required | Default                  |
|----------------|------------------------------------|----------|--------------------------|
| `check-name`   | The name of the check run to find. | `false`  | `'Releasability status'` |
| `github-token` | The GitHub token for API calls.    | `true`   | `${{ github.token }}`    |

## Outputs

| Output    | Description                                                                                                     |
|-----------|-----------------------------------------------------------------------------------------------------------------|
| `version` | The extracted version string from the check annotation if the check was successful and an annotation was found. |

## Example Usage

Here is an example of how to use this action in a workflow. This workflow can be triggered manually. The first job checks the releasability status and exposes the found version as an output. A second job then consumes this version to perform a subsequent step, such as creating a release.

```yaml
name: Check Releasability and Use Version

on:
  workflow_dispatch:

jobs:
  check_releasability:
    name: Check Releasability Status
    runs-on: ubuntu-latest
    outputs:
      release_version: ${{ steps.check_status.outputs.version }}

    steps:
      - name: Check Releasability Status
        id: check_status
        uses: SonarSource/release-github-actions/check-releasability-status@master

  use_the_version:
    name: Use the Extracted Version
    runs-on: ubuntu-latest
    needs: check_releasability

    steps:
      - name: Echo the version
        if: needs.check_releasability.outputs.release_version
        run: |
          echo "The releasable version is ${{ needs.check_releasability.outputs.release_version }}"
