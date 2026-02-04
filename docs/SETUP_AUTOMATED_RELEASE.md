# Setting Up Automated Release for Your Repository

This guide walks through setting up the automated release workflow for a SonarSource analyzer project.

For detailed workflow documentation (inputs, outputs, behavior), see [AUTOMATED_RELEASE.md](AUTOMATED_RELEASE.md).

## Prerequisites Checklist

Before the workflow will work, complete these steps:

### Jira Configuration

- [ ] **Add `Jira Tech User GitHub` as Administrator** on your Jira project (required to create/release versions)
- [ ] **Add the same user to Jira sandbox** if testing with `dry-run: true`

### Vault Permissions (re-terraform-aws-vault)

- [ ] **Create PR to add release-automation permission** for analyzer PR creation

Example for `orders/{squad}.yaml`:
```yaml
- <<: *release_automation
  repositories: [your-repo, sonar-enterprise, sonarcloud-core]
```

The secret name defaults to `sonar-{plugin-name}-release-automation`.

See example PR: https://github.com/SonarSource/re-terraform-aws-vault/pull/8406

## Information Needed

Before creating the workflows, gather:

1. **Project Identity:**
   - Jira project key (e.g., SONARARMOR, CSD, SLCORE)
   - Display name (e.g., "SonarArmor", "SonarJava")
   - Plugin name (e.g., "armor", "csd")

2. **Team & Workflow:**
   - Product Manager email (for ticket assignment after release)
   - Slack channel for notifications
   - Release branch (usually `master`)

3. **Integrations:**
   - SonarQube Server integration? (creates PRs in sonar-enterprise, tickets in SONAR project)
   - SonarCloud integration? (creates PRs in sonarcloud-core, tickets in SC project)
   - IDE tickets needed? (SLVS, SLVSCODE, SLE, SLI)

## Create the Workflows

### 1. `.github/workflows/automated-release.yml`

```yaml
# Automated Release Workflow
#
# This workflow automates the complete release process including:
# - Creating Jira release tickets and managing versions
# - Publishing GitHub releases
# - Creating integration tickets for SQC and SQS
# - Updating analyzers with the new version
# - Bumping version numbers for the next development cycle
#
# Usage:
# - Trigger manually via GitHub Actions UI
# - Set 'dry-run: true' to use Jira sandbox and create draft releases (for testing)
# - Set 'dry-run: false' for production releases

name: Automated Release

on:
  workflow_dispatch:
    inputs:
      short-description:
        description: "Short description for the REL ticket"
        required: true
        type: string
      sqc-integration:
        description: "Integrate into SQC"
        type: boolean
        default: true
      sqs-integration:
        description: "Integrate into SQS"
        type: boolean
        default: true
      branch:
        description: "Branch from which to do the release"
        required: true
        default: "master"
        type: string
      new-version:
        description: "New version (without -SNAPSHOT; leave empty to auto-increment minor)"
        required: false
        type: string
      rule-props-changed:
        description: '"@RuleProperty" changed? See SC-4654'
        type: boolean
        default: false
      dry-run:
        description: "Use Jira sandbox and create draft releases (true) or production (false)"
        type: boolean
        default: false

jobs:
  release:
    name: Release
    uses: SonarSource/release-github-actions/.github/workflows/automated-release.yml@v1
    permissions:
      statuses: read
      id-token: write
      contents: write
      actions: write
      pull-requests: write
    with:
      project-name: "YOUR_PROJECT_NAME"          # e.g., "SonarArmor"
      plugin-name: "your-plugin"                  # e.g., "armor"
      jira-project-key: "YOUR_JIRA_KEY"          # e.g., "SONARARMOR"
      rule-props-changed: ${{ github.event.inputs.rule-props-changed }}
      short-description: ${{ github.event.inputs.short-description }}
      new-version: ${{ github.event.inputs.new-version }}
      sqc-integration: ${{ github.event.inputs.sqc-integration == 'true' }}
      sqs-integration: ${{ github.event.inputs.sqs-integration == 'true' }}
      branch: ${{ github.event.inputs.branch }}
      pm-email: "pm@sonarsource.com"             # Product Manager email
      slack-channel: "your-slack-channel"
      verbose: true
      use-jira-sandbox: ${{ github.event.inputs.dry-run == 'true' }}
      is-draft-release: ${{ github.event.inputs.dry-run == 'true' }}

  bump_versions:
    name: Bump versions
    needs: release
    uses: ./.github/workflows/bump-version.yml
    permissions:
      contents: write
      pull-requests: write
    with:
      version: ${{ needs.release.outputs.new-version }}
```

### 2. `.github/workflows/bump-version.yml`

```yaml
name: Bump version

on:
  workflow_dispatch:
    inputs:
      version:
        description: "Next version (e.g., 1.2.0) or leave empty to auto-increment minor"
        type: string
      create-pull-request:
        description: "Create a Pull Request"
        type: boolean
        default: true
  workflow_call:
    inputs:
      version:
        type: string

jobs:
  bump-version:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Get Next Version
        id: get_next_version
        env:
          INPUT_VERSION: ${{ inputs.version }}
        run: |
          if [ -n "$INPUT_VERSION" ]; then
            next_version="$INPUT_VERSION"
            echo "Using provided version: $next_version"
          else
            # Extract version from gradle.properties
            raw_version=$(grep -oPm1 "(?<=version=).*-SNAPSHOT" gradle.properties)
            current_version="$(echo "$raw_version" | sed 's/-SNAPSHOT//')"

            if [[ -z "$current_version" ]]; then
              echo "::error::Failed to extract version from gradle.properties"
              exit 1
            fi

            # Increment minor version, reset patch to 0
            next_version=$(echo $current_version | awk -F. -v OFS=. '{$2++; $3=0; print}')
            echo "Auto-incremented to: $next_version"
          fi

          echo "next-version=$next_version" >> $GITHUB_OUTPUT
          echo "NEXT_VERSION=$next_version" >> $GITHUB_ENV

      - name: Update Version
        if: ${{ inputs.create-pull-request != false }}
        run: |
          snapshot_version="${NEXT_VERSION}-SNAPSHOT"
          sed -i "s/version=.*-SNAPSHOT/version=${snapshot_version}/" gradle.properties

      - name: Create Pull Request
        if: ${{ inputs.create-pull-request != false }}
        uses: peter-evans/create-pull-request@v7
        with:
          commit-message: "Bump version to ${{ env.NEXT_VERSION }}"
          branch: "bump-version-to-${{ env.NEXT_VERSION }}"
          title: "Bump version to ${{ env.NEXT_VERSION }}"
          body: "This PR bumps the project version to ${{ env.NEXT_VERSION }}."
          reviewers: ${{ github.actor }}

      - name: Summary
        run: |
          echo "## Version Bump Summary" >> $GITHUB_STEP_SUMMARY
          echo "Next version: ${{ env.NEXT_VERSION }}" >> $GITHUB_STEP_SUMMARY
```

### 3. Update existing `.github/workflows/release.yml`

Add `workflow_dispatch` support for manual triggering (needed for the automated release to trigger artifact publishing):

```yaml
on:
  release:
    types:
      - published
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
        description: Do not publish artifacts
        default: false

jobs:
  release:
    # ... existing job config ...
    uses: SonarSource/gh-action_release/.github/workflows/main.yaml@v6
    with:
      version: ${{ inputs.version }}
      releaseId: ${{ inputs.releaseId }}
      dryRun: ${{ inputs.dryRun }}
      # ... other existing inputs ...
```

## Testing the Setup

1. **First test with dry-run**: Run the automated-release workflow with `dry-run: true`
   - This uses Jira sandbox and creates draft GitHub releases
   - Verify tickets are created in Jira sandbox
   - Verify PRs are created as drafts

2. **Production release**: Once validated, run with `dry-run: false`

## Example Implementation

See the sonar-armor implementation: https://github.com/SonarSource/sonar-armor/pull/1253

## Common Customizations

### Custom Plugin Artifacts

If SQS and SQC use different artifact names:
```yaml
plugin-artifacts-sqs: "your-sqs-artifact"
plugin-artifacts-sqc: "your-sqc-artifact"
```

### Custom Release Automation Secret

If not using the default `sonar-{plugin-name}-release-automation`:
```yaml
release-automation-secret-name: "custom-secret-name"
```

### IDE Integration Tickets

Enable creation of tickets for IDE teams:
```yaml
create-slvs-ticket: true
create-slvscode-ticket: true
create-sle-ticket: true
create-sli-ticket: true
sq-ide-short-description: "Changes relevant to IDE integrations"
```

### Runner Environment

Specify a different runner:
```yaml
runner-environment: "sonar-s"
```
