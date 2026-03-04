# Sonar Update Center Release Action

This GitHub Action opens a pull request in [sonar-update-center-properties](https://github.com/SonarSource/sonar-update-center-properties) adding a new release section to the specified `.properties` file.

## Prerequisites

Make sure your `release-automation` token in [re-terraform-aws-vault](https://github.com/SonarSource/re-terraform-aws-vault/) allows writing to `sonar-update-center-properties`. It must include:
- `contents: write`
- `pull-requests: write`

## Implementation Details

The action uses a Python script (`update.py`) that performs an in-place update of the `.properties` file.

## Inputs

| Input           | Description                                                                           | Required |
|-----------------|---------------------------------------------------------------------------------------|----------|
| `file`          | The `.properties` file to update (e.g., `scannermaven.properties`).                  | `true`   |
| `version`       | The new version string (e.g., `5.5.0.6356`).                                         | `true`   |
| `description`   | Value for the `description` field of the new version entry.                           | `true`   |
| `date`          | Value for the `date` field of the new version entry (e.g., `2026-03-04`).             | `true`   |
| `changelog-url` | Value for the `changelogUrl` field of the new version entry.                          | `true`   |
| `download-url`  | Value for the `downloadUrl` field of the new version entry.                           | `true`   |

## Outputs

| Output             | Description                          |
|--------------------|--------------------------------------|
| `pull-request-url` | The URL of the created pull request. |
