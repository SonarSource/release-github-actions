# How to Add Release Automations to Your Repository

This guide explains how to implement automated releases for analyzer repositories using the reusable GitHub Actions workflows provided by this repository.

## Table of Contents

- [Overview](#overview)
- [Architecture Approaches](#architecture-approaches)
- [Prerequisites](#prerequisites)
- [Step-by-Step Implementation](#step-by-step-implementation)
- [Configuration Reference](#configuration-reference)
- [Testing Strategy](#testing-strategy)
- [Troubleshooting](#troubleshooting)
- [Complete Example](#complete-example)

## Overview

The release automation system streamlines the entire release process by orchestrating multiple stages:

1. **Pre-release checks**: Verify releasability status and update rule metadata
2. **Version extraction**: Get current version from repox and format for Jira
3. **Jira management**: Create release tickets, fetch release notes, manage versions
4. **GitHub release**: Publish releases with automated notes
5. **Integration**: Create SC/SONAR tickets and update analyzers in SQS/SQC
6. **Post-release**: Bump version for next development iteration

## Architecture Approaches

### Reusable Workflow Pattern (Recommended for Similar Projects)

**When to use**: Multiple repositories with similar release processes (e.g., ABD squad: sonar-dataflow-bug-detection, sonar-cobol)

This approach uses a shared workflow defined in `release-github-actions` (like `abd-automated-release.yml`) that multiple repositories can call with product-specific configuration. This guide focuses on this pattern.

**Benefits**:
- Single source of truth for release logic
- Consistent process across multiple projects
- Centralized updates and improvements
- Reduced duplication

### Local Workflow Pattern (For Unique Requirements)

**When to use**: Repository has unique release requirements not shared with others

Define the entire workflow locally in your repository, calling individual actions from `release-github-actions` directly. While not covered in detail here, this approach offers maximum flexibility for custom release processes.

**Note**: The rest of this guide focuses on the reusable workflow pattern, as demonstrated by the sonar-dataflow-bug-detection implementation.

## Prerequisites

### Required Vault Secrets

Your repository needs the following secrets configured in Vault (via [SPEED self-service portal](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)):

- `development/github/token/{REPO_OWNER_NAME_DASH}-lock` - For branch locking
- `development/kv/data/slack` - For Slack notifications
- `development/artifactory/token/{REPO_OWNER_NAME_DASH}-private-reader` - For downloading rule-api
- Release automation secrets (varies by project, e.g., `sonar-dataflow-bug-detection-release-automation`)

### GitHub Permissions

Your workflows will need these permissions:

```yaml
permissions:
  statuses: read        # Check releasability status
  contents: write       # Create releases, PRs
  pull-requests: write  # Create and manage PRs
  actions: write        # Trigger workflows
  id-token: write       # Vault authentication
```

### Repository Structure

- Maven project with `pom.xml` files using `-SNAPSHOT` versions
- Rule metadata files (`sonarpedia.json`) for language-specific rules
- Existing CI setup with Cirrus CI or similar

### Existing Workflows

You should already have (or will create):
- CI workflow that produces releasability status
- Release workflow for publishing to binaries (if applicable)

## Step-by-Step Implementation

### Phase 1: Create Supporting Workflows

These workflows are prerequisites that the automation will call. Create them first and test them independently.

#### 1.1 Releasability Status Workflow

Create `.github/workflows/releaseability-status.yml`:

```yaml
name: Releasability status
on:
  check_suite:
    types: [ completed ]
jobs:
  update_releasability_status:
    runs-on: sonar-xs
    name: Releasability status
    permissions:
      id-token: write
      statuses: write
      contents: read
    if: >-
      (
        contains(fromJSON('["main", "master"]'), github.event.check_suite.head_branch) ||
        startsWith(github.event.check_suite.head_branch, 'branch-')
      ) &&
      (
        (github.event.check_suite.conclusion == 'success' && github.event.check_suite.app.slug == 'cirrus-ci') ||
        github.event_name == 'workflow_dispatch'
      )
    steps:
      - uses: SonarSource/gh-action_releasability/releasability-status@v3
        with:
          optional_checks: "Jira"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Purpose**: Automatically sets GitHub releasability status based on CI results. The automation checks this before allowing a release.

#### 1.2 Rule Metadata Update Workflow

Create `.github/workflows/rule-metadata-update.yml`:

```yaml
name: rule-metadata-update
on:
  workflow_dispatch:

jobs:
  rule-metadata-update:
    runs-on: sonar-runner
    permissions:
      id-token: write
      contents: write
      pull-requests: write
    steps:
      - name: Update Rule Metadata
        id: update-rule-metadata
        uses: SonarSource/release-github-actions/update-rule-metadata@v1

      - name: Check Rule Metadata Changes
        run: |
          if [ "${{ steps.update-rule-metadata.outputs.has-changes }}" == "true" ]; then
            echo "::notice title=Rule Metadata Changes::Changes detected and PR created: ${{ steps.update-rule-metadata.outputs.pull-request-url }}"
          else
            echo "::notice title=Rule Metadata Status::No changes to the rules metadata were detected"
          fi
```

**Purpose**: Updates rule metadata from RSPEC/Jira. Can be run manually or called by automation. The automation will check if changes are detected and block release until they're merged.

#### 1.3 Bump Versions Workflow

Create `.github/workflows/bump-versions.yaml`:

```yaml
name: bump-versions
on:
  workflow_call:
    inputs:
      version:
        description: The new version
        required: true
        type: string
  workflow_dispatch:
    inputs:
      version:
        description: The new version
        required: true
        type: string

jobs:
  bump-version:
    runs-on: sonar-runner
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Update Version in pom.xml
        run: |
          snapshot_version="${{ inputs.version }}-SNAPSHOT"

          # Update all pom.xml files (excluding embedded e2e projects) to the new snapshot version
          find . -type f -name "pom.xml" \
            ! -path "./its/end-to-end/projects/*" \
            -exec sed -i "s/<version>.*-SNAPSHOT<\/version>/<version>${snapshot_version}<\/version>/" {} +

      - uses: peter-evans/create-pull-request@v7
        with:
          author: ${{ github.actor }} <${{ github.actor }}@users.noreply.github.com>
          commit-message: Prepare next development iteration
          title: Prepare next development iteration
          branch: bot/bump-project-version
          branch-suffix: timestamp
          base: master
          reviewers: ${{ github.actor }}
```

**Purpose**: Bumps version to next `-SNAPSHOT` after release. Called automatically by the automation workflow.

**Important**: Note the `checkout` action - this was initially missing and had to be added in a fix commit!

#### 1.4 Enhance Toggle Lock Branch Workflow

If you don't already have `.github/workflows/ToggleLockBranch.yml`, create it. If you do, enhance it to support `workflow_call`:

```yaml
name: Toggle lock branch

on:
  workflow_call:
    inputs:
      branch:
        required: true
        type: string
        default: "master"
  workflow_dispatch:
    inputs:
      branch:
        description: "Branch to toggle lock on"
        required: true
        default: "master"

jobs:
  ToggleLockBranch_job:
    name: Toggle lock branch
    runs-on: sonar-runner
    permissions:
      id-token: write
    steps:
      - id: secrets
        uses: SonarSource/vault-action-wrapper@v3
        with:
          secrets: |
            development/github/token/{REPO_OWNER_NAME_DASH}-lock token | lock_token;
            development/kv/data/slack token | slack_api_token;
      - uses: sonarsource/gh-action-lt-backlog/ToggleLockBranch@v2
        with:
          github-token: ${{ fromJSON(steps.secrets.outputs.vault).lock_token }}
          slack-token: ${{ fromJSON(steps.secrets.outputs.vault).slack_api_token }}
          slack-channel: squad-abd  # Update to your squad's channel
          branch-pattern: ${{ inputs.branch }}
```

**Purpose**: Locks/unlocks the release branch to prevent commits during release. The automation calls this before and after the release process.

**Note**: Update `slack-channel` to your squad's Slack channel.

### Phase 2: Create Placeholder Workflow

Create the automation workflow with a dummy job first. This establishes the API contract and allows you to validate inputs before implementing the full automation.

Create `.github/workflows/AutomateRelease.yml`:

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
        description: |
          Did any rule properties change in this release?
        required: true
        default: "No"
        options:
          - "Yes"
          - "No"
      branch:
        description: |
          Branch from which to do the release.
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
        run: |
          echo "Hello Dummy Step"
          echo "Short description: ${{ inputs.short-description }}"
          echo "Branch: ${{ inputs.branch }}"
```

**Purpose**: Test the workflow trigger and validate inputs. This is safer than implementing everything at once.

**Test**: Run this workflow manually from GitHub UI to ensure inputs appear correctly.

### Phase 3: Integrate with Reusable Workflow

Replace the dummy job with the actual automation by calling the reusable workflow.

Update `.github/workflows/AutomateRelease.yml`:

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
        description: |
          Did any rule properties change in this release?
        required: true
        default: "No"
        options:
          - "Yes"
          - "No"
      branch:
        description: |
          Branch from which to do the release.
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
      jira-project-key: "DBD"              # Your Jira project key
      project-name: "SonarDBD"             # Your project display name
      plugin-artifacts: "dbd,dbd-java-frontend,dbd-python-frontend"  # Comma-separated artifact names
      use-jira-sandbox: false              # Use production Jira (set true for testing)
      is-draft-release: false              # Create real releases (set true for testing)
      pm-email: "product.manager@sonarsource.com"  # Product manager email
      release-automation-secret-name: "sonar-dataflow-bug-detection-release-automation"  # Your secret name in Vault
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

**Key Configuration Points**:
- `jira-project-key`: Your Jira project (e.g., "DBD", "SONARIAC")
- `project-name`: Display name (e.g., "SonarDBD")
- `plugin-artifacts`: Comma-separated list of artifacts to update
- `pm-email`: Product manager who receives assignment after release
- `release-automation-secret-name`: Your Vault secret name for release automation

### Phase 4: Testing and Refinement

#### Initial Testing with Safety Flags

For your first test run, use these safety settings:

```yaml
use-jira-sandbox: true    # Use sandbox Jira instead of production
is-draft-release: true    # Create draft GitHub releases
```

#### Testing During Development

If the reusable workflow is still in development (not yet merged to v1), you can reference the feature branch:

```yaml
uses: SonarSource/release-github-actions/.github/workflows/abd-automated-release.yml@ahbnr/automate-abd-releases
```

Once the PR is merged and tagged, switch to:

```yaml
uses: SonarSource/release-github-actions/.github/workflows/abd-automated-release.yml@v1
```

#### Common Issues to Watch For

1. **Missing checkout in bump-versions**: Ensure the `actions/checkout@v4` step is present
2. **Permissions**: Verify all required permissions are granted
3. **Vault secrets**: Ensure all secrets are configured via SPEED portal
4. **Slack channel**: Update to your squad's channel in ToggleLockBranch.yml

## Configuration Reference

### Required Inputs

| Input | Description | Example |
|-------|-------------|---------|
| `jira-project-key` | Jira project identifier | `"DBD"` |
| `project-name` | Display name for project | `"SonarDBD"` |
| `plugin-artifacts` | Comma-separated artifact names | `"dbd,dbd-java-frontend"` |
| `pm-email` | Product manager email | `"pm@sonarsource.com"` |
| `release-automation-secret-name` | Vault secret name | `"sonar-project-release-automation"` |
| `short-description` | Release summary for tickets | User input |
| `rule-props-changed` | Did rule properties change? | `"Yes"` or `"No"` |
| `branch` | Release branch | `"master"` |

### Optional Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `use-jira-sandbox` | Use Jira sandbox for testing | `true` |
| `is-draft-release` | Create draft GitHub releases | `true` |
| `release-notes` | Custom release notes (or fetch from Jira) | `""` |
| `new-version` | Next version (or auto-increment) | `""` |

### Product-Specific Examples

**sonar-dataflow-bug-detection (DBD)**:
```yaml
jira-project-key: "DBD"
project-name: "SonarDBD"
plugin-artifacts: "dbd,dbd-java-frontend,dbd-python-frontend"
pm-email: "denis.troller@sonarsource.com"
release-automation-secret-name: "sonar-dataflow-bug-detection-release-automation"
```

**Cloud Security** (uses different artifacts for SQS/SQC):
```yaml
jira-project-key: "SONARIAC"
project-name: "SonarIaC"
plugin-name: "IaC"
plugin-artifacts-sqs: "iac"
plugin-artifacts-sqc: "iac"
pm-email: "pm@sonarsource.com"
release-automation-secret-name: "cloud-security-release-automation"
```

## Testing Strategy

### Incremental Testing Approach

1. **Test individual workflows first**:
   ```bash
   # Test releasability status (runs automatically on CI)
   # Test rule metadata update
   gh workflow run rule-metadata-update.yml

   # Test bump versions
   gh workflow run bump-versions.yaml -f version=2.5

   # Test branch locking
   gh workflow run ToggleLockBranch.yml -f branch=master
   ```

2. **Test with dummy workflow**:
   - Verify inputs appear correctly in GitHub UI
   - Ensure workflow triggers successfully

3. **Test with full automation in safe mode**:
   ```yaml
   use-jira-sandbox: true
   is-draft-release: true
   ```

4. **Validate outputs**:
   - Check Jira sandbox for created tickets and versions
   - Verify draft GitHub release is created
   - Check that PRs are created for SQS/SQC updates
   - Verify version bump PR is created

5. **Production release**:
   ```yaml
   use-jira-sandbox: false
   is-draft-release: false
   ```

## Troubleshooting

### Missing Checkout Action

**Symptom**: Bump versions workflow fails with "no pom.xml found"

**Solution**: Ensure `actions/checkout@v4` step exists in bump-versions.yaml before the version update step.

### Permission Denied Errors

**Symptom**: "Resource not accessible by integration" or "403 Forbidden"

**Solution**:
- Verify all required permissions are in the workflow permissions block
- Check that GitHub App has necessary repository access

### Vault Secrets Not Found

**Symptom**: "Secret not found in Vault"

**Solution**:
- Configure secrets via [SPEED self-service portal](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)
- Verify secret path matches exactly (e.g., `development/github/token/{REPO_OWNER_NAME_DASH}-lock`)

### Releasability Check Fails

**Symptom**: "Releasability status is not success"

**Solution**:
- Ensure CI is passing on the target branch
- Check that releaseability-status.yml workflow has run successfully
- Verify status is set correctly: `gh api /repos/{owner}/{repo}/commits/{branch}/status`

### Rule Metadata Changes Block Release

**Symptom**: Release blocked due to metadata changes

**Solution**: This is expected behavior! The automation detected rule metadata updates that need review:
1. Review the PR created by update-rule-metadata
2. Merge the PR
3. Re-run the release workflow

### Jira Connection Issues

**Symptom**: Cannot create tickets or fetch release notes

**Solution**:
- Verify Jira project key is correct
- Ensure you have proper Jira permissions
- Check if using correct Jira instance (production vs sandbox)
- Verify version exists in Jira project

## Complete Example

Here's the complete workflow from sonar-dataflow-bug-detection as a reference:

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
        description: |
          Did any rule properties change in this release?
        required: true
        default: "No"
        options:
          - "Yes"
          - "No"
      branch:
        description: |
          Branch from which to do the release.
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
      jira-project-key: "DBD"
      project-name: "SonarDBD"
      plugin-artifacts: "dbd,dbd-java-frontend,dbd-python-frontend"
      use-jira-sandbox: false
      is-draft-release: false
      pm-email: "denis.troller@sonarsource.com"
      release-automation-secret-name: "sonar-dataflow-bug-detection-release-automation"
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

## Additional Resources

- [ABD Automated Release Workflow](../.github/workflows/abd-automated-release.yml) - The reusable workflow this guide uses
- [Cloud Security Automated Release Workflow](../.github/workflows/cloud-security-automated-release.yml) - Alternative example with SonarLint integration
- [DBD Release Instructions](https://xtranet-sonarsource.atlassian.net/wiki/spaces/CodeQualit/pages/2824634385/DBD+Release+Instructions) - Manual release process (now automated)
- [SPEED Self-Service Portal](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED) - For configuring Vault secrets
- [Individual Action Documentation](../README.md#available-actions) - Details on each reusable action

## Questions or Issues?

If you encounter issues not covered in this guide, please:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review existing releases in sonar-dataflow-bug-detection as examples
3. Reach out to the squad that created the automation (ABD squad for abd-automated-release.yml)
