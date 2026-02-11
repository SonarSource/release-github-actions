---
name: automated-release-setup
description: >
  Use this skill whenever the user asks to "set up automated release", "configure release automation",
  "add automated release workflow", or any variation of setting up the automated release workflow for
  a SonarSource analyzer project. This skill gathers project details, creates workflow files, updates
  existing release workflows, and sets up vault permissions.
---

# Setup Automated Release Workflow

Help the user set up the automated release workflow by gathering required information and creating the necessary workflow files.

### Step 1: Gather Required Information

Ask the user for the following details using AskUserQuestion:

1. **Project Name**: Display name (e.g., "SonarCOBOL", "SonarApex")
2. **Plugin Name**: Short identifier used in secrets (e.g., "cobol", "apex")
3. **Jira Project Key**: Jira project key (e.g., "SONARCOBOL", "SONARAPEX")
4. **PM Email**: Product Manager email address
5. **Slack Channel**: Check the existing `release.yml` for `slackChannel` value first - reuse it if present, otherwise ask the user
6. **Build System**: Maven (pom.xml) or Gradle (gradle.properties)
7. **SonarLint Integration**: Whether to create integration tickets for SonarLint IDE plugins:
   - **SLVS** (SonarLint for Visual Studio)
   - **SLVSCode** (SonarLint for VS Code)
   - **SLE** (SonarLint for Eclipse)
   - **SLI** (SonarLint for IntelliJ)

### Step 1b: Check Existing release.yml

Before asking for all information, read the existing `.github/workflows/release.yml` file to extract:
- **slackChannel**: Reuse the existing Slack channel configuration for the automated release workflow

This ensures consistency between the release and automated-release workflows.

### Step 2: Check Prerequisites

Remind the user of these prerequisites and **ask for confirmation** using AskUserQuestion:

1. **Jira Configuration**:
   - Add `Jira Tech User GitHub` as Administrator on the Jira project
   - Add the same user to Jira sandbox for dry-run testing (required for `dry-run: true` mode)
   - **Ask the user to confirm both**:
     - "Have you added 'Jira Tech User GitHub' as Administrator on the {JIRA_PROJECT_KEY} project?" (Production)
     - "Have you added 'Jira Tech User GitHub' as Administrator on the {JIRA_PROJECT_KEY} project in the Jira sandbox?" (For dry-run testing)
   - The user must verify this manually at: Project settings → People → Administrator role
   - Sandbox URL: https://sonarsource-sandbox-608.atlassian.net/

2. **Vault Permissions** (re-terraform-aws-vault):
   - Create a PR to add the `release-automation` secret to the repository's config in the squad config file
   - File: `orders/{squad}.yaml` (e.g., `orders/analysis-jvm-squad.yaml`)
   - This creates secret `sonar-{plugin-name}-release-automation`
   - Example PR: https://github.com/SonarSource/re-terraform-aws-vault/pull/8406
   - **Important**: The skill should create this PR automatically (see Step 5b)

3. **Release Workflow**:
   - Ensure `release.yml` supports `workflow_dispatch` with inputs: `version`, `releaseId`, `dryRun`

### Step 3: Create Workflow Files

Create two workflow files in `.github/workflows/`:

#### 3.1 Create `automated-release.yml`

**Standard workflow (SQS/SQC only):**

```yaml
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
        description: "New version to release (without -SNAPSHOT; if left empty, the current minor version will be auto-incremented)"
        required: false
        type: string
      rule-props-changed:
        description: >
          "@RuleProperty" changed? See SC-4654
        type: boolean
        default: false
      verbose:
        description: "Enable verbose logging"
        type: boolean
        default: false
      dry-run:
        description: "Test mode: uses Jira sandbox and creates draft GitHub release"
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
      project-name: "${PROJECT_NAME}"
      plugin-name: "${PLUGIN_NAME}"
      jira-project-key: "${JIRA_PROJECT_KEY}"
      rule-props-changed: ${{ github.event.inputs.rule-props-changed }}
      short-description: ${{ github.event.inputs.short-description }}
      new-version: ${{ github.event.inputs.new-version }}
      sqc-integration: ${{ github.event.inputs.sqc-integration == 'true' }}
      sqs-integration: ${{ github.event.inputs.sqs-integration == 'true' }}
      branch: ${{ github.event.inputs.branch }}
      pm-email: "${PM_EMAIL}"
      slack-channel: "${SLACK_CHANNEL}"
      verbose: ${{ github.event.inputs.verbose == 'true' }}
      use-jira-sandbox: ${{ github.event.inputs.dry-run == 'true' }}
      is-draft-release: ${{ github.event.inputs.dry-run == 'true' }}

  bump_versions:
    name: Bump versions
    needs: release
    uses: ./.github/workflows/bump-versions.yaml
    permissions:
      contents: write
      pull-requests: write
    with:
      version: ${{ needs.release.outputs.new-version }}
```

**Workflow with SonarLint integration (includes IDE ticket creation):**

```yaml
name: Automated Release
on:
  workflow_dispatch:
    inputs:
      short-description:
        description: "Short description for the REL ticket"
        required: true
        type: string
      sq-ide-short-description:
        description: "Short description for the SonarLint IDE tickets (leave empty to skip IDE tickets)"
        required: false
        type: string
      sqc-integration:
        description: "Integrate into SQC"
        type: boolean
        default: true
      sqs-integration:
        description: "Integrate into SQS"
        type: boolean
        default: true
      slvs-integration:
        description: "Create SLVS ticket (SonarLint for Visual Studio)"
        type: boolean
        default: false
      slvscode-integration:
        description: "Create SLVSCode ticket (SonarLint for VS Code)"
        type: boolean
        default: false
      sle-integration:
        description: "Create SLE ticket (SonarLint for Eclipse)"
        type: boolean
        default: false
      sli-integration:
        description: "Create SLI ticket (SonarLint for IntelliJ)"
        type: boolean
        default: false
      branch:
        description: "Branch from which to do the release"
        required: true
        default: "master"
        type: string
      new-version:
        description: "New version to release (without -SNAPSHOT; if left empty, the current minor version will be auto-incremented)"
        required: false
        type: string
      rule-props-changed:
        description: >
          "@RuleProperty" changed? See SC-4654
        type: boolean
        default: false
      verbose:
        description: "Enable verbose logging"
        type: boolean
        default: false
      dry-run:
        description: "Test mode: uses Jira sandbox and creates draft GitHub release"
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
      project-name: "${PROJECT_NAME}"
      plugin-name: "${PLUGIN_NAME}"
      jira-project-key: "${JIRA_PROJECT_KEY}"
      rule-props-changed: ${{ github.event.inputs.rule-props-changed }}
      short-description: ${{ github.event.inputs.short-description }}
      new-version: ${{ github.event.inputs.new-version }}
      sqc-integration: ${{ github.event.inputs.sqc-integration == 'true' }}
      sqs-integration: ${{ github.event.inputs.sqs-integration == 'true' }}
      create-slvs-ticket: ${{ github.event.inputs.slvs-integration == 'true' }}
      create-slvscode-ticket: ${{ github.event.inputs.slvscode-integration == 'true' }}
      create-sle-ticket: ${{ github.event.inputs.sle-integration == 'true' }}
      create-sli-ticket: ${{ github.event.inputs.sli-integration == 'true' }}
      sq-ide-short-description: ${{ github.event.inputs.sq-ide-short-description }}
      branch: ${{ github.event.inputs.branch }}
      pm-email: "${PM_EMAIL}"
      slack-channel: "${SLACK_CHANNEL}"
      verbose: ${{ github.event.inputs.verbose == 'true' }}
      use-jira-sandbox: ${{ github.event.inputs.dry-run == 'true' }}
      is-draft-release: ${{ github.event.inputs.dry-run == 'true' }}

  bump_versions:
    name: Bump versions
    needs: release
    uses: ./.github/workflows/bump-versions.yaml
    permissions:
      contents: write
      pull-requests: write
    with:
      version: ${{ needs.release.outputs.new-version }}
```

#### 3.2 Create `bump-versions.yaml`

**For Maven projects (pom.xml):**

```yaml
name: bump-versions
on:
  workflow_call:
    inputs:
      version:
        required: true
        type: string
  workflow_dispatch:
    inputs:
      version:
        description: The new version (without -SNAPSHOT)
        required: true
        type: string

jobs:
  bump-version:
    runs-on: sonar-xs
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - env:
          VERSION: "${{ inputs.version }}-SNAPSHOT"
        run: |
          find . -type f -name "pom.xml" -exec sed -i "s/<version>.*-SNAPSHOT<\/version>/<version>${VERSION}<\/version>/" {} +
      - uses: peter-evans/create-pull-request@v7
        with:
          author: ${{ github.actor }} <${{ github.actor }}>
          commit-message: Prepare next development iteration
          title: Prepare next development iteration
          branch: bot/bump-project-version
          branch-suffix: timestamp
          base: master
          reviewers: ${{ github.actor }}
```

**For Gradle projects (gradle.properties):**

```yaml
name: bump-versions
on:
  workflow_call:
    inputs:
      version:
        required: true
        type: string
  workflow_dispatch:
    inputs:
      version:
        description: The new version (without -SNAPSHOT)
        required: true
        type: string

jobs:
  bump-version:
    runs-on: sonar-xs
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - env:
          VERSION: "${{ inputs.version }}-SNAPSHOT"
        run: |
          sed -i "s/version=.*-SNAPSHOT/version=${VERSION}/" gradle.properties
      - uses: peter-evans/create-pull-request@v7
        with:
          author: ${{ github.actor }} <${{ github.actor }}>
          commit-message: Prepare next development iteration
          title: Prepare next development iteration
          branch: bot/bump-project-version
          branch-suffix: timestamp
          base: master
          reviewers: ${{ github.actor }}
```

### Step 4: Update release.yml

The existing `release.yml` must be updated to:
1. Add `workflow_dispatch` trigger with inputs
2. Pass inputs to the reusable workflow with fallbacks for release events

Add the `workflow_dispatch` trigger:

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
        description: Flag to enable the dry-run execution
        default: false
```

Then update the job's `with:` block to pass the inputs with fallbacks for release events:

```yaml
jobs:
  release:
    # ... existing permissions ...
    uses: SonarSource/gh-action_release/.github/workflows/main.yaml@v6
    with:
      # ... existing inputs like publishToBinaries, mavenCentralSync, slackChannel ...
      # We do not have any inputs if this workflow is triggered by a release event, hence we have to use a fallback for all inputs
      version: ${{ inputs.version || github.event.release.tag_name }}
      releaseId: ${{ inputs.releaseId || github.event.release.id }}
      dryRun: ${{ inputs.dryRun == true }}
```

**Important:** The fallbacks (`|| github.event.release.tag_name` and `|| github.event.release.id`) are required because when triggered by a `release` event, there are no `inputs` - only `github.event.release` context is available.

### Step 5: Create Branch and Commit

After creating/modifying all workflow files, create a branch and commit the changes:

```bash
# Create a new branch
git checkout -b add-automated-release-workflow

# Stage the workflow files
git add .github/workflows/automated-release.yml .github/workflows/bump-versions.yaml .github/workflows/release.yml

# Commit with descriptive message
git commit -m "Add automated release workflow

Add workflows for automated release process:
- automated-release.yml: Main workflow that orchestrates the release
- bump-versions.yaml: Bumps version file after release
- Update release.yml to support workflow_dispatch for automated releases
"
```

### Step 5b: Create PR for Vault Permissions (re-terraform-aws-vault)

Create a PR in the `re-terraform-aws-vault` repository to add the release-automation secret:

1. Clone the repository:
   ```bash
   gh repo clone SonarSource/re-terraform-aws-vault /tmp/re-terraform-aws-vault --depth 1
   ```

2. Find the squad configuration file that contains the repository (e.g., `orders/analysis-jvm-squad.yaml`)

3. Check if a `release_automation` YAML anchor already exists at the top of the file. If not, add it after the other anchors (like `github_lock`):
   ```yaml
   release_automation: &release_automation
     suffix: release-automation
     description: access to sonar-enterprise and sonarcloud-core repositories to create PRs to update analyzers
     organization: SonarSource
     permissions:
       contents: write
       pull_requests: write
   ```

4. Add the `release-automation` secret to the repository's `github.customs` section using the anchor:
   ```yaml
   - <<: *release_automation
     repositories: [${REPO_NAME}, sonar-enterprise, sonarcloud-core]
   ```

   **Important:** Include the repository itself (e.g., `sonar-apex`) in the repositories list along with `sonar-enterprise` and `sonarcloud-core`.

5. Create branch, commit, and PR:
   ```bash
   cd /tmp/re-terraform-aws-vault
   git checkout -b add-release-automation-${REPO_NAME}
   git add orders/${SQUAD_CONFIG_FILE}
   git commit -m "Add release-automation secret for ${REPO_NAME}

   This enables the automated release workflow to create PRs
   in sonar-enterprise and sonarcloud-core repositories."
   git push -u origin add-release-automation-${REPO_NAME}
   gh pr create --title "Add release-automation secret for ${REPO_NAME}" --body "## Summary
   - Add release-automation secret for ${REPO_NAME} to enable automated release workflow
   - This creates the secret \`sonar-${PLUGIN_NAME}-release-automation\` which allows creating PRs in sonar-enterprise and sonarcloud-core

   ## Test plan
   - [ ] Verify secret is created after merge
   - [ ] Test automated release workflow with dry-run"
   ```

### Step 6: Testing Instructions

Provide these instructions to the user:

1. **Test with dry-run first**:
   - Go to Actions → Automated Release → Run workflow
   - Set `dry-run: true`
   - Verify Jira tickets in sandbox, draft PRs, no production artifacts

2. **Production release**:
   - Set `dry-run: false`
   - All tickets, releases, and PRs will be created in production

### Step 7: Post-Release Checklist

Remind user of post-release tasks:
- Review and merge the bump-version PR
- Review and merge the SQS PR in sonar-enterprise
- Review and merge the SQC PR in sonarcloud-core
- Update integration ticket statuses in Jira
- Set fix versions on the SONAR ticket

**If SonarLint integration is enabled:**
- Monitor the SLVS, SLVSCode, SLE, and/or SLI tickets created in Jira
- Coordinate with IDE teams for integration timelines
- Verify analyzer compatibility with SonarLint versions

### Advanced Options

Mention these optional configurations if relevant:

- **Custom artifact names**: `plugin-artifacts-sqs`, `plugin-artifacts-sqc`
- **Custom secret name**: `release-automation-secret-name`
- **Disable releasability check**: `check-releasability: false`

### SonarLint Integration Details

When SonarLint integration is enabled, the workflow creates Jira tickets for the relevant IDE teams:

| Input | Jira Project | Description |
|-------|--------------|-------------|
| `create-slvs-ticket` | SLVS | SonarLint for Visual Studio |
| `create-slvscode-ticket` | SLVSCODE | SonarLint for VS Code |
| `create-sle-ticket` | SLE | SonarLint for Eclipse |
| `create-sli-ticket` | SLI | SonarLint for IntelliJ |

The `sq-ide-short-description` input is used as the description for all IDE tickets. This should describe what changes are relevant for IDE integrations (e.g., "New rules for X", "Updated analysis engine", "Breaking API changes").

**When to enable SonarLint integration:**
- The analyzer is used by SonarLint (standalone analysis)
- New rules or rule changes that affect IDE users
- Breaking changes in the analyzer API
- Performance improvements relevant to IDE analysis

**Note:** Not all analyzers are integrated with SonarLint. Check with the IDE teams if unsure whether your analyzer requires SonarLint integration tickets.

### References

- Setup Guide: https://github.com/SonarSource/release-github-actions/blob/master/docs/SETUP_AUTOMATED_RELEASE.md
- Workflow Documentation: https://github.com/SonarSource/release-github-actions/blob/master/docs/AUTOMATED_RELEASE.md
- Example: https://github.com/SonarSource/sonar-abap/blob/master/.github/workflows/automated-release.yml
