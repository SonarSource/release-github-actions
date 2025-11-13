# How to Add Release Automations to Your Repository

This guide shows how to implement automated releases using the reusable GitHub Actions workflows from this repository.

## Table of Contents

* [About Reusable Workflows](#about-reusable-workflows)
* [Prerequisite: Vault Secrets](#prerequisite-vault-secrets)
* [Prerequisite: Jira Sandbox](#prerequisite-jira-sandbox)
* [Implementation Steps](#implementation-steps)
    * [Phase 1: Create Supporting Workflows](#phase-1-create-supporting-workflows)
    * [Phase 2: Create Placeholder Workflow](#phase-2-create-placeholder-workflow)
    * [Phase 3: Create Your Reusable Workflow](#phase-3-create-your-reusable-workflow)
    * [Phase 4: Integrate with Reusable Workflow](#phase-4-integrate-with-reusable-workflow)
    * [Phase 5: Test and Refine](#phase-5-test-and-refine)
* [Additional Resources](#additional-resources)

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

## Prerequisite: Jira Sandbox

To test the release automation in a safe manner, you should ensure the following:

1. You can open the [Jira sandbox](https://sonarsource-sandbox-608.atlassian.net/jira).
2. You have (admin) access to your analyzer project in the sandbox and you can create versions and tickets there.

## Implementation Steps

### Phase 1: Create Supporting Workflows

In this phase we will add workflows to check releasability, to update metadata, to bump analyzer versions, etc.
If your repository already contains some of these workflows, double-check that they match the requirements below.

#### 1.1 Releasability Status

[//]: # (@formatter:off)

* Copy
  [ABD's releaseability status check](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/8764808bd7622a70f2320a1b9874e58c6e477bf3/.github/workflows/build.yml#L226)
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

  **Pay special attention** that it can take a specific branch as input and that a `workflow_call` trigger is configured as in the given
  examples.
  The branch input must be passed on to the `sonarsource/gh-action-lt-backlog/ToggleLockBranch` action as a `branch_pattern` parameter.
  See the given example.

#### 1.5 Release Action

* We assume that a release action similar to
  [DBD's release action](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/154aeb888d290afbc36f584e415d6608986eb65b/.github/workflows/release.yml)
  is already in place.
* However, make sure that you are using at least version 6 of the release workflow:
  `SonarSource/gh-action_release/.github/workflows/main.yaml@v6`
* Also, a `workflow_dispatch` trigger with three inputs must be present:
  ```yml
  workflow_dispatch:
    inputs:
      version:
        type: string
        description: Version
        required: true
      releaseId:
        type: string
        description: Release ID
        required: true
      dryRun:
        type: boolean
        description: Flag to enable the dry-run execution
        default: false
        required: false
  ```
  and these inputs must be passed on to the release action:
  ```yml
    # [...]
    uses: SonarSource/gh-action_release/.github/workflows/main.yaml@v6
    with:
      # [...]
      version: ${{ inputs.version }}
      releaseId: ${{ inputs.releaseId }}
      dryRun: ${{ inputs.dryRun }}
  ```

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

### Phase 3: Create Your Reusable Workflow

* Create a file for your reusable flow at `.github/workflows/<squad-name>-automated-release.yml`.
* You can use one of the following workflows as a template:
    * [ABD's workflow](https://github.com/SonarSource/release-github-actions/blob/master/.github/workflows/abd-automated-release.yml)
    * [Cloud Security's workflow](https://github.com/SonarSource/release-github-actions/blob/master/.github/workflows/cloud-security-automated-release.yml)
        * This one is considering SonarLint integrations!
* The templates should work for you as-is, but only you know your squad's specific needs.
  Hence, study the workflow and adapt it as needed.
* Upload your changes as a PR. You do not need to get it merged before you are done testing everything.

### Phase 4: Integrate with Reusable Workflow

> [!IMPORTANT]
> **Make sure everything that was created in the phases 1 and 2 is merged.**
>
> However, the changes below can be tested on a PR branch before merging because of the placeholder workflow that we have added.
> When testing, make sure to follow the dry-run guidelines in Phase 5.

1. Replace the placeholder workflow in `.github/workflows/AutomateRelease.yml`.
   Use the contents of one of the following `AutomateRelease.yml` implementations as a basis.
    * [DBD's AutomateRelease.yml](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/AutomateRelease.yml)
    * [Cloud Security's AutomateRelease.yml](https://github.com/SonarSource/sonar-iac-enterprise/blob/master/.github/workflows/AutomateRelease.yml)
        * This one has SonarLint integrations
2. Replace the call to the `abd-automated-release.yml` or `cloud-security-automated-release.yml` template workflow with the name of the
   reusable workflow that you created in Phase 3.
   If your reusable workflow is not yet merged, you might also need to use the last commit hash of your PR branch instead of the version.
3. Adapt the following arguments to fit your project:
   ```yml
   jira-project-key: "<...>"
   project-name: "<...>"
   plugin-artifacts: "<All artifacts (your plugins!) that need to be released, comma-separated>"
   pm-email: "mail.of.your.pm@sonarsource.com"
   release-automation-secret-name: "<name of the secret you created in Phase 1>"
   ```

   These are the parameters of ABD's reusable workflow.
   Depending on whether you used ABD's or Cloud Security's reusable workflow as a base, you might have to adapt additional parameters and
   the parameter names are slightly different.
4. Create a PR on your project with your changes.

### Phase 5: Test and Refine

1. Set `use-jira-sandbox: true` and `is-draft-release: true`
2. Create a test version in the Jira sandbox for your project, and perhaps some dummy tickets associated with the version.
3. Open the `Automate release` workflow in the GitHub UI for your project.
4. Select your PR branch in the `Use workflow from` dropdown.
5. Fill in the rest of the form and submit.
6. Verify outputs: Check Jira sandbox for tickets, check the draft GitHub release, PRs for SQS/SQC/version-bump etc.
7. Iterate until you are satisfied.
8. Once ready, merge any changes you made to the reusable workflow in this repository.
9. Update the `AutomateRelease.yml` to use the released version of your reusable workflow.
10. Set `use-jira-sandbox: false` and `is-draft-release: false`
11. Merge the `AutomateRelease.yml` changes to your main branch.

## Additional Resources

* **Individual Actions:** [README](../README.md#available-actions)
* **Release Instructions using these workflows:**
    * [DBD Release Instructions](https://xtranet-sonarsource.atlassian.net/wiki/spaces/CodeQualit/pages/2824634385/DBD+Release+Instructions)
    * [Cloud Security's Release Instructions](https://xtranet-sonarsource.atlassian.net/wiki/spaces/CSD/pages/4325048388/Release+Instructions)