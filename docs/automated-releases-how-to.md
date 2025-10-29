# How to Add Release Automations to Your Repository

This guide shows how to implement automated releases using the reusable GitHub Actions workflows from this repository.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Implementation Steps](#implementation-steps)
- [Configuration Reference](#configuration-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## About Reusable Workflows

This guide uses the **reusable workflow pattern**: a shared workflow in `release-github-actions` (like `abd-automated-release.yml`) that
multiple repositories can call with product-specific configuration. This is ideal when multiple projects share similar release processes (
e.g., ABD squad repos). For unique requirements, you can instead define workflows locally using individual actions from this repository.

## Prerequisites

**Vault Secrets** (configure
via [SPEED portal](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)):

- `development/github/token/{REPO_OWNER_NAME_DASH}-lock`
- `development/kv/data/slack`
- `development/artifactory/token/{REPO_OWNER_NAME_DASH}-private-reader`
- `{your-project}-release-automation`

**Required Permissions:**

```yaml
permissions:
  statuses: read
  contents: write
  pull-requests: write
  actions: write
  id-token: write
```

## Implementation Steps

### Phase 1: Create Supporting Workflows

Copy these workflows from [sonar-dataflow-bug-detection](https://github.com/SonarSource/sonar-dataflow-bug-detection/tree/master/.github/workflows) to your repository's `.github/workflows/`:

#### 1.1 Releasability Status

Copy [`releaseability-status.yml`](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/releaseability-status.yml) as-is.

#### 1.2 Rule Metadata Update

Copy [`rule-metadata-update.yml`](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/rule-metadata-update.yml) as-is.

#### 1.3 Bump Versions

Copy [`bump-versions.yaml`](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/bump-versions.yaml) and customize the `find` command if needed:

```yaml
# Customize this path pattern to match your project structure
find . -type f -name "pom.xml" \
  ! -path "./its/end-to-end/projects/*" \  # Exclude test fixtures
  -exec sed -i "s/<version>.*-SNAPSHOT<\/version>/<version>${snapshot_version}<\/version>/" {} +
```

**Important**: Don't forget the `actions/checkout@v4` step before the version update!

#### 1.4 Toggle Lock Branch

Copy [`ToggleLockBranch.yml`](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/ToggleLockBranch.yml) and update:

```yaml
slack-channel: squad-abd  # TODO: Change to your squad's channel
```

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

**See complete example**: [sonar-dataflow-bug-detection/AutomateRelease.yml](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/AutomateRelease.yml)

### Phase 4: Test and Refine

1. **Initial test**: Use `use-jira-sandbox: true` and `is-draft-release: true`
2. **Verify outputs**: Check Jira sandbox for tickets, draft GitHub release, PRs for SQS/SQC/version-bump
3. **If testing with unreleased workflow**: Use `@branch-name` instead of `@v1`, switch after merge
4. **Production**: Set `use-jira-sandbox: false` and `is-draft-release: false`

## Configuration Reference

### Required Inputs

| Input                            | Description               | Example                        |
|----------------------------------|---------------------------|--------------------------------|
| `jira-project-key`               | Jira project identifier   | `"DBD"`                        |
| `project-name`                   | Display name              | `"SonarDBD"`                   |
| `plugin-artifacts`               | Comma-separated artifacts | `"dbd,dbd-java-frontend"`      |
| `pm-email`                       | PM email for assignment   | `"pm@sonarsource.com"`         |
| `release-automation-secret-name` | Vault secret              | `"project-release-automation"` |

### Optional Inputs

| Input              | Default | Description                       |
|--------------------|---------|-----------------------------------|
| `use-jira-sandbox` | `true`  | Use sandbox for testing           |
| `is-draft-release` | `true`  | Create draft releases             |
| `release-notes`    | `""`    | Custom notes (or fetch from Jira) |
| `new-version`      | `""`    | Next version (or auto-increment)  |

### Real Examples

**DBD**: [AutomateRelease.yml](https://github.com/SonarSource/sonar-dataflow-bug-detection/blob/master/.github/workflows/AutomateRelease.yml) - Uses `abd-automated-release.yml` workflow

**Cloud Security**: Uses [`cloud-security-automated-release.yml`](../.github/workflows/cloud-security-automated-release.yml) - Different workflow with separate SQS/SQC artifacts and SonarLint integration

## Testing

```bash
# Test individual workflows
gh workflow run rule-metadata-update.yml
gh workflow run bump-versions.yaml -f version=2.5
gh workflow run ToggleLockBranch.yml -f branch=master

# Test full automation with safety flags
# In AutomateRelease.yml: use-jira-sandbox: true, is-draft-release: true
gh workflow run AutomateRelease.yml

# Verify:
# - Jira sandbox tickets/versions created
# - Draft GitHub release exists
# - PRs created for SQS/SQC updates and version bump
```

## Troubleshooting

### Missing Checkout Action

**Symptom**: "no pom.xml found" in bump-versions

**Fix**: Add `- uses: actions/checkout@v4` before version update step

### Vault Secrets Not Found

**Symptom**: "Secret not found in Vault"

**Fix**: Configure
via [SPEED portal](https://xtranet-sonarsource.atlassian.net/wiki/spaces/Platform/pages/3553787989/Manage+Vault+Policy+-+SPEED)

### Rule Metadata Changes Block Release

**Symptom**: Release blocked with metadata changes detected

**Fix**: Expected behavior - review and merge the generated PR, then re-run release

### Releasability Check Fails

**Symptom**: "Releasability status is not success"

**Fix**: Ensure CI passes on target branch, check: `gh api /repos/{owner}/{repo}/commits/{branch}/status`

## Resources

- **Reusable Workflows:**
  - [ABD Automated Release Workflow](../.github/workflows/abd-automated-release.yml) - For ABD squad projects
  - [Cloud Security Automated Release Workflow](../.github/workflows/cloud-security-automated-release.yml) - With SonarLint integration
- **Reference Implementations:**
  - [sonar-dataflow-bug-detection workflows](https://github.com/SonarSource/sonar-dataflow-bug-detection/tree/master/.github/workflows)
- **Individual Actions:** [README](../README.md#available-actions)
- **Manual Process (now automated):**
  [DBD Release Instructions](https://xtranet-sonarsource.atlassian.net/wiki/spaces/CodeQualit/pages/2824634385/DBD+Release+Instructions)