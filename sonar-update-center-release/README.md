# Sonar Update Center Release Action

This GitHub Action opens a pull request in [sonar-update-center-properties](https://github.com/SonarSource/sonar-update-center-properties) adding a new release section to the specified `.properties` file.

## Prerequisites

Make sure your `release-automation` token in [re-terraform-aws-vault](https://github.com/SonarSource/re-terraform-aws-vault/) allows writing to `sonar-update-center-properties`. It must include:
- `contents: write`
- `pull-requests: write`

## Implementation Details

The action uses a Python script (`update.py`) that performs an in-place update of the `.properties` file.

## Inputs

| Input           | Description                                                              | Required |
|-----------------|--------------------------------------------------------------------------|----------|
| `file`          | The `.properties` file to update (e.g., `scannermaven.properties`).      | `true`   |
| `version`       | The new version string (e.g., `5.5.0.6356`).                             | `true`   |
| `description`   | The release description.                                                 | `true`   |
| `date`          | The release date in `YYYY-MM-DD` format.                                 | `true`   |
| `changelog-url` | The URL to the changelog for this release.                               | `true`   |
| `download-url`  | The URL to download this release.                                        | `true`   |

## Outputs

| Output             | Description                          |
|--------------------|--------------------------------------|
| `pull-request-url` | The URL of the created pull request. |
