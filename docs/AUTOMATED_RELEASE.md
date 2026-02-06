# Automated Release Workflow

This reusable GitHub Actions workflow automates the end-to-end release process across Jira and GitHub, and optionally creates integration tickets and analyzer update PRs. It is designed to be invoked via `workflow_call` from other repositories.

> **Quick Setup**: Use the [automated-release-setup Claude Code skill](../skills/automated-release-setup/) to automatically set up this workflow in your repository. The skill will guide you through prerequisites, create the necessary workflow files, and configure vault permissions.

## Description

The workflow orchestrates these steps:

1. Optionally freeze (lock) the target branch at the start of the release
2. Check releasability status on the branch (enabled by default)
3. Determine the release version and Jira version name
4. Optionally generate Jira release notes if not provided
5. Create a Jira release ticket
6. Publish a GitHub release (draft or final)
7. Release the current Jira version and create the next version in Jira
8. Optionally create integration tickets (SLVS, SLVSCODE, SLE, SLI, SQC, SQS)
9. Optionally open analyzer update PRs in SQS and SQC
10. Optionally post per-job and final workflow summaries when `verbose` is enabled

## Dependencies

This workflow composes several actions from this repository:

- `SonarSource/gh-action_releasability/releasability-status` (external action for releasability checks)
- `SonarSource/release-github-actions/get-release-version`
- `SonarSource/release-github-actions/get-jira-version`
- `SonarSource/release-github-actions/get-jira-release-notes`
- `SonarSource/release-github-actions/create-jira-release-ticket`
- `SonarSource/release-github-actions/publish-github-release`
- `SonarSource/release-github-actions/release-jira-version`
- `SonarSource/release-github-actions/create-integration-ticket`
- `SonarSource/release-github-actions/update-analyzer`
- `SonarSource/release-github-actions/update-release-ticket-status`
- Branch lock/unlock via `sonarsource/gh-action-lt-backlog/ToggleLockBranch`

## Inputs

| Input                         | Description                                                                                                     | Required | Default      |
|------------------------------|-----------------------------------------------------------------------------------------------------------------|----------|--------------|
| `jira-project-key`           | Jira project key                                                                                                | Yes      | -            |
| `project-name`               | Display name of the project                                                                                     | Yes      | -            |
| `plugin-name`                | Plugin name                                                                                                     | Yes      | -            |
| `plugin-artifacts-sqs`       | Artifact identifier(s) for SQS; falls back to `plugin-name`                                                     | No       | -            |
| `plugin-artifacts-sqc`       | Artifact identifier(s) for SQC; falls back to `plugin-name`                                                     | No       | -            |
| `use-jira-sandbox`           | Use Jira sandbox                                                                                                | No       | `true`       |
| `is-draft-release`           | Create the GitHub release as a draft                                                                            | No       | `true`       |
| `pm-email`                   | Product manager email to assign the release ticket after technical release                                      | Yes      | -            |
| `release-automation-secret-name` | Secret name used to create analyzer update PRs. If omitted, defaults to `sonar-{plugin-name}-release-automation`. | No       | -            |
| `short-description`          | Brief summary for release and integration tickets                                                               | Yes      | -            |
| `rule-props-changed`         | Whether rule properties changed (`true`/`false`); mapped to Yes/No in the release ticket                        | Yes      | -            |
| `branch`                     | Branch to release from                                                                                          | Yes      | `master`     |
| `release-notes`              | Explicit release notes; if empty, Jira release notes are generated                                              | No       | -            |
| `sq-ide-short-description`   | Short summary of SQ IDE related changes                                                                         | No       | -            |
| `new-version`                | Next version to create in Jira                                                                                  | Yes      | -            |
| `create-slvs-ticket`         | Create SLVS integration ticket                                                                                  | No       | `false`      |
| `create-slvscode-ticket`     | Create SLVSCODE integration ticket                                                                              | No       | `false`      |
| `create-sle-ticket`          | Create SLE integration ticket                                                                                   | No       | `false`      |
| `create-sli-ticket`          | Create SLI integration ticket                                                                                   | No       | `false`      |
| `sqs-integration`            | Create SQS integration ticket and PR                                                                            | No       | `true`       |
| `sqc-integration`            | Create SQC integration ticket and PR                                                                            | No       | `true`       |
| `runner-environment`         | Runner labels/environment                                                                                        | No       | `sonar-m`    |
| `release-process`            | Release process documentation URL                                                                               | No       | General page |
| `verbose`                    | When `true`, posts per-job summaries and a final run summary                                                    | No       | `false`      |
| `freeze-branch`              | When `true`, locks the target branch during the release and unlocks it after publishing                         | No       | `true`       |
| `check-releasability`        | When `true`, verifies the releasability status on the branch before proceeding                                  | No       | `true`       |
| `slack-channel`              | Slack channel to notify when locking/unlocking the branch                                                       | No       | -            |

## Outputs

| Output        | Description                                                |
|---------------|------------------------------------------------------------|
| `new-version` | The newly created Jira version name (from the Jira release job) |

## Environment Variables

The workflow sets the following environment variables for composed actions:

| Variable           | Description                                 |
|--------------------|---------------------------------------------|
| `JIRA_PROJECT_KEY` | Propagates the Jira project key to actions  |
| `USE_JIRA_SANDBOX` | Propagates sandbox selection to actions     |

## Usage

### Basic usage via workflow_call

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      new-version:
        description: "Next version to create in Jira"
        required: true
        type: string
      short-description:
        description: "Brief summary for release and integration tickets"
        required: true
        type: string
      verbose:
        description: "Emit job summaries"
        required: false
        type: boolean
        default: false

jobs:
  automated-release:
    uses: SonarSource/release-github-actions/.github/workflows/automated-release.yml@v1
    with:
      jira-project-key: CSD
      project-name: "Cloud Security"
      plugin-name: "csd"
      pm-email: "pm@example.com"
      short-description: ${{ inputs.short-description }}
      rule-props-changed: "false"
      branch: "master"
      new-version: ${{ inputs.new-version }}
      sqs-integration: true
      sqc-integration: true
      slack-channel: "release-notifications"
      verbose: ${{ inputs.verbose }}
```

## Notes

- When `check-releasability: true` (default), the workflow will:
  - Execute a releasability check on the specified branch immediately after freezing (using `SonarSource/gh-action_releasability@v3`)
  - Update the commit status with the latest releasability results
  - Fail early if the releasability check does not pass, preventing unnecessary work (like creating REL tickets)
- When `freeze-branch: true`, the workflow will:
  - Lock the specified branch at the start of the release
  - Proceed with the release steps
  - Unlock the branch after the GitHub release is published
  - Send lock/unlock notifications to the configured `slack-channel` if provided
- When `release-notes` is empty, Jira release notes are fetched and used.
- Integration tickets and analyzer update PRs are created only if their respective flags are enabled and prerequisites are met.
- Summaries:
  - Each job includes a "Summary" step that writes to `$GITHUB_STEP_SUMMARY` only when `verbose: true`.
- Permissions and environments are scoped per job to minimize required privileges.

## Setup

To set up this workflow in your repository, you need to complete the following prerequisites and create the necessary workflow files.

### Prerequisites

1. **Jira Configuration**:
   - Add `Jira Tech User GitHub` as Administrator on your Jira project (Project settings → People → Administrator role)
   - For dry-run testing, also add the user to the Jira sandbox: https://sonarsource-sandbox-608.atlassian.net/

2. **Vault Permissions**:
   - Create a PR in `re-terraform-aws-vault` to add the `release-automation` secret
   - File: `orders/{squad}.yaml` (e.g., `orders/analysis-jvm-squad.yaml`)
   - Add the `release_automation` anchor if not present:
     ```yaml
     release_automation: &release_automation
       suffix: release-automation
       description: access to sonar-enterprise and sonarcloud-core repositories to create PRs to update analyzers
       organization: SonarSource
       permissions:
         contents: write
         pull_requests: write
     ```
   - Add to your repository's `github.customs` section:
     ```yaml
     - <<: *release_automation
       repositories: [your-repo-name, sonar-enterprise, sonarcloud-core]
     ```
   - Example PR: https://github.com/SonarSource/re-terraform-aws-vault/pull/8406

3. **Release Workflow**:
   - Update `release.yml` to support `workflow_dispatch` with inputs: `version`, `releaseId`, `dryRun`
   - Add fallbacks for release events:
     ```yaml
     with:
       version: ${{ inputs.version || github.event.release.tag_name }}
       releaseId: ${{ inputs.releaseId || github.event.release.id }}
       dryRun: ${{ inputs.dryRun == true }}
     ```

### Required Workflow Files

You need to create two workflow files:

1. **`automated-release.yml`**: Main workflow that calls this reusable workflow
2. **`bump-versions.yaml`**: Bumps version after release (Maven or Gradle)

See the [Usage](#usage) section for examples, or use the [automated-release-setup skill](../skills/automated-release-setup/) for guided setup.

### SonarLint Integration

When your analyzer is used by SonarLint, you can enable integration ticket creation for IDE teams:

| Input | Jira Project | Description |
|-------|--------------|-------------|
| `create-slvs-ticket` | SLVS | SonarLint for Visual Studio |
| `create-slvscode-ticket` | SLVSCODE | SonarLint for VS Code |
| `create-sle-ticket` | SLE | SonarLint for Eclipse |
| `create-sli-ticket` | SLI | SonarLint for IntelliJ |

Use `sq-ide-short-description` to describe changes relevant for IDE integrations.

## Troubleshooting

- Ensure the caller repository has appropriate permissions to use this workflow and to write releases and PRs.
- Verify that `release-automation-secret-name` exists and grants access for creating analyzer update PRs. If omitted, ensure the default secret (`sonar-{plugin-name}-release-automation`) exists and is configured with the required permissions.
- Check job logs if the final summary indicates failure; the per-job logs contain detailed outputs even when `verbose` is disabled.
- Ensure the `Jira Tech User GitHub` is an Administrator on the target Jira project; admin rights are required to release the Jira version and to create a new version.

## Testing

1. **Test with dry-run first**:
   - Go to Actions → Automated Release → Run workflow
   - Set `dry-run: true`
   - Verify Jira tickets in sandbox, draft GitHub release, draft PRs

2. **Production release**:
   - Set `dry-run: false`
   - All tickets, releases, and PRs will be created in production

## Post-Release Checklist

- Review and merge the bump-version PR
- Review and merge the SQS PR in sonar-enterprise
- Review and merge the SQC PR in sonarcloud-core
- Update integration ticket statuses in Jira
- Set fix versions on the SONAR ticket

**If SonarLint integration is enabled:**
- Monitor the SLVS, SLVSCode, SLE, and/or SLI tickets created in Jira
- Coordinate with IDE teams for integration timelines
