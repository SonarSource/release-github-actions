# How to Add Release Automations to Your Repository

This guide shows how to implement automated releases using the reusable GitHub Actions workflows from this repository.

## Table of Contents

* [About Reusable Workflows](#about-reusable-workflows)
* [Prerequisite: Vault Secrets](#prerequisite-vault-secrets)
* [Implementation Steps](#implementation-steps)
  * [Phase 1: Create Supporting Workflows](#phase-1-create-supporting-workflows)
  * [Phase 2: Create Placeholder Workflow](#phase-2-create-placeholder-workflow)
  * [Phase 3: Integrate with Reusable Workflow](#phase-3-integrate-with-reusable-workflow)
  * [Phase 4: Test and Refine](#phase-4-test-and-refine)
  * [Real Examples](#real-examples)
* [Resources](#resources)

## About Reusable Workflows

This guide presents a **reusable workflow pattern**:

* We will build a shared workflow (like [`abd-automated-release.yml`](../.github/workflows/abd-automated-release.yml)) that multiple
  repositories can call with repository-specific configuration
* Ideal when multiple projects share similar release processes (e.g., ABD squad repos)
* For unique requirements, you can instead fully define workflows within your repository using the individual actions from this repository

## Prerequisite: Vault Secrets

All repositories for which release automations shall be added need the capability to create pull requests on the SQS and SQC repositories.
This will allow the automation to create PRs for the SQS and SQC integration tickets.

This can be achieved via changes to [re-terraform-aws-vault](https://github.com/SonarSource/re-terraform-aws-vault).
Here are two examples:

* [PR for ABD repositories](https://github.com/SonarSource/re-terraform-aws-vault/pull/7729)
* [PR for Cloud Security repositories](https://github.com/SonarSource/re-terraform-aws-vault/pull/6693)

## Implementation Steps

### Phase 1: Create Supporting Workflows

In this phase we will add workflows to check releasability, to update metadata, and to bump analyzer versions.
If your repository already contains some of these workflows, feel free to skip steps.

#### 1.1 Releasability Status

[//]: # (@formatter:off)

* Copy
  [ABD's releaseability-status.yml](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/releaseability-status.yml)
  to your repositories.
* Check if anything needs to be adapted to your repository. Though, it should work for most analyzers as-is.

[//]: # (@formatter:on)

#### 1.2 Rule Metadata Update

[//]: # (@formatter:off)

* Copy
  [ABD's rule-metadata-update.yml](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/rule-metadata-update.yml)
  to your repositories.
* Check if anything needs to be adapted to your repository. Though, it should work for most analyzers as-is.

[//]: # (@formatter:on)

#### 1.3 Bump Versions

* Create a `bump-versions.yaml` workflow in your repositories.
    * If you use **Maven**,
      copy [ABD's bump-versions.yaml](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/bump-versions.yaml).
    * If you use **Gradle**,
      copy [Cloud Security's bump-versions.yaml](https://github.com/SonarSource/sonar-iac-enterprise/blob/master/.github/workflows/bump-versions.yaml).
* Check if anything needs to be adapted to the needs of your repository.

#### 1.4 Toggle Lock Branch

* Copy
  [ABD's ToggleLockBranch.yml](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/ToggleLockBranch.yml)
  to your repositories.
* Adapt the Slack channel reference to point to your squad's channel:
  ```yaml
  slack-channel: <your channel>
  ```
* Check if anything else needs to be adapted to your repository.

[//]: # (@formatter:on)

### Phase 2: Create Placeholder Workflow

Create `.github/workflows/AutomateRelease.yml` with your workflow inputs:

```yaml
name: Automate release

on:
  workflow_dispatch:
    inputs:
      short-description:
        description: |
          A brief summary of what the release contains.
          This will be added directly to the release ticket.
        required: true
      rule-props-changed:
        type: choice
        description: Did any rule properties change in this release?
        required: true
        default: "No"
        options:
          - "Yes"
          - "No"
      branch:
        description: Branch from which to do the release.
        required: true
        default: "master"
      release-notes:
        description: |
          Release notes.
          If blank, release notes will be generated from the Jira Release.
      new-version:
        description: |
          Specify the version for the next release (e.g., 2.5).
          If left blank, the minor version will be automatically incremented.

jobs:
  dummy_job:
    runs-on: github-ubuntu-latest-s
    name: dummy job
    steps:
      - name: Dummy Step
        run: echo "Testing workflow inputs"
```

Test this manually from GitHub UI to ensure inputs appear correctly.

### Phase 3: Integrate with Reusable Workflow

Replace the `jobs` section in `.github/workflows/AutomateRelease.yml` with:

```yaml
jobs:
  lock-branch:
    name: Lock ${{ inputs.branch }} branch
    uses: ./.github/workflows/ToggleLockBranch.yml
    permissions:
      id-token: write
    with:
      branch: ${{ inputs.branch }}

  release:
    name: Release
    uses: SonarSource/release-github-actions/.github/workflows/abd-automated-release.yml@v1
    needs: lock-branch
    permissions:
      statuses: read
      id-token: write
      contents: write
      actions: write
      pull-requests: write
    with:
      # TODO: Customize these values for your project
      jira-project-key: "DBD"              # Your Jira project key
      project-name: "SonarDBD"             # Your project display name
      plugin-artifacts: "dbd,dbd-java-frontend,dbd-python-frontend"  # Comma-separated artifacts
      use-jira-sandbox: true               # Set false for production
      is-draft-release: true               # Set false for production
      pm-email: "pm@sonarsource.com"       # Product manager email
      release-automation-secret-name: "your-project-release-automation"  # Your Vault secret

      # Pass through user inputs
      short-description: ${{ inputs.short-description }}
      rule-props-changed: ${{ inputs.rule-props-changed }}
      branch: ${{ inputs.branch }}
      release-notes: ${{ inputs.release-notes }}
      new-version: ${{ inputs.new-version }}

  unlock-branch:
    name: Unlock ${{ inputs.branch }} branch
    uses: ./.github/workflows/ToggleLockBranch.yml
    needs: release
    permissions:
      id-token: write
    with:
      branch: ${{ inputs.branch }}

  bump_versions:
    name: Bump versions
    needs: [ release, unlock-branch ]
    uses: ./.github/workflows/bump-versions.yaml
    permissions:
      contents: write
      pull-requests: write
    with:
      version: ${{ needs.release.outputs.new-version }}
```

**See complete example**:
[sonar-dataflow-bug-detection/AutomateRelease.yml](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/AutomateRelease.yml)

### Phase 4: Test and Refine

1. **Initial test**: Use `use-jira-sandbox: true` and `is-draft-release: true`
2. **Verify outputs**: Check Jira sandbox for tickets, draft GitHub release, PRs for SQS/SQC/version-bump
3. **If testing with unreleased workflow**: Use `@branch-name` instead of `@v1`, switch after merge
4. **Production**: Set `use-jira-sandbox: false` and `is-draft-release: false`

### Real Examples

**DBD**:
[AutomateRelease.yml](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/AutomateRelease.yml)

* Uses [`abd-automated-release.yml`](../.github/workflows/abd-automated-release.yml) workflow

**Cloud Security**:
SonarIaC's [AutomateRelease.yml](https://github.com/SonarSource/sonar-iac-enterprise/blob/master/.github/workflows/AutomateRelease.yml)

* Uses [`cloud-security-automated-release.yml`](../.github/workflows/cloud-security-automated-release.yml) - Different
  workflow with separate SQS/SQC artifacts and SonarLint integration

## Resources

* **Reusable Workflows:**
    * [ABD Automated Release Workflow](../.github/workflows/abd-automated-release.yml) - For ABD squad projects
    * [Cloud Security Automated Release Workflow](../.github/workflows/cloud-security-automated-release.yml) - With SonarLint integration
* **Individual Actions:** [README](../README.md#available-actions)
* **Release Instructions using these workflows:**
    * [DBD Release Instructions](https://xtranet-sonarsource.atlassian.net/wiki/spaces/CodeQualit/pages/2824634385/DBD+Release+Instructions)
    * [Cloud Security's Release Instructions](https://xtranet-sonarsource.atlassian.net/wiki/spaces/CSD/pages/4325048388/Release+Instructions)