---
name: devex-release-setup
description: >
  Use this skill whenever the user asks to "set up Development Experience release workflow",
  "configure DevEx release automation", "add full-release workflow", "add release
  automation using ide-automated-release", or any variation of setting up the
  automated release workflow for a SonarSource Development Experience project (SonarLint
  Core, SonarLint for IntelliJ, SonarLint for Eclipse, SonarLint for VS Code, etc.).
  This skill gathers project details and creates the necessary workflow file.
---

# Setup Development Experience Automated Release Workflow

This skill sets up the automated release workflow (`ide-automated-release.yml`)
for SonarSource Development Experience projects. It is distinct from the full analyzer
release setup (`automated-release-setup`) — it targets Development Experience projects
that do not need releasability checks, SQS/SQC analyzer update PRs, or Vault permission
changes.

---

### General Principle: Check Before Acting

Before performing any action in the steps below, check the current state of the repository:

- **Already done correctly**: Notify the user ("This part is already in place — no changes needed.") and skip.
- **Done differently**: Show what exists and how it differs from the recommended approach, then ask the user whether to align it. Do not change anything without confirmation.
- **Not done at all**: Proceed with the step as described.

Apply this principle to every file creation, modification, and configuration step.

---

### Step 1: Auto-detect Repository Information

Before asking any questions, gather the following from the repository:

1. **Workflow file extension**: List `.github/workflows/`. If most files use `.yaml`, use `.yaml`; otherwise default to `.yml`.

2. **Build system**: Check root directory for:
   - `pom.xml` → Maven
   - `build.gradle` or `gradle.properties` → Gradle
   - Neither → unknown; must ask the user

3. **Slack channel**: Search `.github/workflows/` files for `slack-channel:` or `slackChannel` values in existing workflows. If exactly one distinct value is found, reuse it. If multiple or none, ask.

4. **Runner name**: Look at existing `.github/workflows/` files for the `runs-on:` value used in non-trivial jobs. Use the most common one as the default for the version bump job.

5. **Default branch**: Run `git symbolic-ref --short refs/remotes/origin/HEAD` or look for `default: 'master'` / `default: 'main'` patterns in existing workflow files.

6. **Workflow SHA pin**: Search existing `.github/workflows/` files for any reference to `SonarSource/release-github-actions` that includes a pinned commit SHA (pattern: `@<40-char-hex> # <version>`). Extract the SHA and version comment. If found, use the same SHA and version in all templates — this ensures consistency with what Renovate bot is already tracking in the repo. If no pinned reference exists, resolve the current SHA of the `v1` tag by running:
   ```bash
   git ls-remote https://github.com/SonarSource/release-github-actions.git refs/tags/v1
   ```
   Use the returned SHA and `# v1` as the comment. If neither works (e.g., no network access), fall back to `@v1` and leave an inline comment `# TODO: pin to commit SHA`.

---

### Step 2: Gather Required Information

Use AskUserQuestion to ask the user. Batch independent questions together.

**Always ask (Batch 1)**:
- **Jira Project Key**: The Jira project key (e.g., `SLCORE`, `SLI`, `SLVS`, `SLE`).
- **Project Name**: Human-readable project name used in Jira REL tickets (e.g., `SonarLint Core`, `SonarLint for IntelliJ`).

**Ask only what wasn't auto-detected (Batch 2)**:
- **Slack channel**: Only ask if not found in existing workflows. Present the default `squad-ide-slcore-bots` as an option.
- **Build system / version bump**:
  - Ask: "Do you want to add a version bump job after the release?"
    - If yes: only ask for build system if it was not auto-detected (Maven / Gradle / Other — if Other, ask for the exact shell command to run, e.g., `sed -i "s/version=.*/version=${NEW_VERSION}-SNAPSHOT/" gradle.properties`).
    - If yes: ask for optional PR labels to apply to the version bump pull request (comma-separated, e.g., `auto-merge,skip-qa`). Leave empty if none.
    - If yes: ask "Are there any modules or subdirectories to exclude from the version bump? (comma-separated paths, e.g. `plugin/it,integration-tests`). Leave empty if all modules should be bumped." Store as `${EXCLUDED_MODULES}`.
  - If auto-detected, confirm with the user ("Found `pom.xml` — I'll use Maven for the version bump. Does that look right?").

**Optional configuration (Batch 3)**:
- **Dry-run input**: "Do you want to expose a `dry-run` dispatch input? (Recommended — lets you test with Jira sandbox and draft releases before the real thing.)"
- **Workflow name**: Name shown in the GitHub Actions UI (default: `Full release`). Only ask if the user seems to want a custom name; otherwise use the default.

---

### Step 3: Update `release.yml`

The `publish-github-release` action (used inside `ide-automated-release.yml`) publishes the GitHub release and **then triggers `release.yml` directly via `gh workflow run`** — passing `version`, `releaseId`, and `dryRun` as inputs. It does not rely on the `release: published` GitHub event.

Check `.github/workflows/release.yml`:

1. **Ensure `workflow_dispatch` inputs are present** with exactly these names:
   ```yaml
   on:
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

2. **Remove the `release: published` trigger** if present — it is no longer needed and would cause a double run. The workflow is now invoked exclusively via `workflow_dispatch` by `publish-github-release`. Ask the user to confirm before removing: "I'll remove the `release: published` trigger from `release.yml` since `ide-automated-release.yml` now triggers it directly. OK?"

3. If `release.yml` uses a **non-default filename** (i.e., not `release.yml`), pass `release-workflow: <filename>` to the `publish-github-release` step inside `ide-automated-release.yml`. However, this is a parameter of the reusable workflow itself; in that case, check whether `ide-automated-release.yml` exposes a `release-workflow` input — if not, ask the user to raise this with the release-github-actions team.

---

### Step 4: Confirm Jira Prerequisites

Remind the user and ask for confirmation using AskUserQuestion:

> The `Jira Tech User GitHub` service account must be an **Administrator** on the `{JIRA_PROJECT_KEY}` Jira project before the workflow can release Jira versions.
> - Project settings → People → Administrator role
> - For dry-run testing, also add the account to the Jira sandbox: https://sonarsource-sandbox-608.atlassian.net/

Ask: "Have you added 'Jira Tech User GitHub' as Administrator on the `{JIRA_PROJECT_KEY}` project (and sandbox if you plan to use dry-run)?"

**Note**: No Vault permission changes are required. Unlike the full analyzer release workflow, `ide-automated-release.yml` does not create analyzer update PRs in external repositories.

---

### Step 5: Create the Workflow File

Check if `.github/workflows/full-release{EXT}` already exists. If it does, ask the user whether to overwrite it or use a different filename.

Use the appropriate template from the variants below, substituting all `${PLACEHOLDERS}`.

#### Variant A: No version bump, no dry-run input

```yaml
name: ${WORKFLOW_NAME}

on:
  workflow_dispatch:
    inputs:
      short-description:
        description: 'A short description for the release ticket'
        required: true
        type: string
      branch:
        description: 'The branch from which to release.'
        required: false
        default: '${DEFAULT_BRANCH}'
        type: string
      new-version:
        description: 'New Jira version to create after the release (e.g. 10.9). Leave empty to auto-increment the last segment.'
        required: false
        type: string

jobs:
  release:
    name: Release
    uses: SonarSource/release-github-actions/.github/workflows/ide-automated-release.yml@${WORKFLOW_SHA}
    if: always() && !failure() && !cancelled()
    permissions:
      statuses: read
      id-token: write
      contents: write
      actions: write
      pull-requests: write
    with:
      jira-project-key: "${JIRA_PROJECT_KEY}"
      project-name: "${PROJECT_NAME}"
      short-description: ${{ inputs.short-description }}
      branch: ${{ inputs.branch }}
      slack-channel: "${SLACK_CHANNEL}"
      new-version: ${{ inputs.new-version }}
```

#### Variant B: No version bump, **with** dry-run input

Add a `dry-run` input and pass `is-test-run` through:

```yaml
name: ${WORKFLOW_NAME}

on:
  workflow_dispatch:
    inputs:
      short-description:
        description: 'A short description for the release ticket'
        required: true
        type: string
      branch:
        description: 'The branch from which to release.'
        required: false
        default: '${DEFAULT_BRANCH}'
        type: string
      new-version:
        description: 'New Jira version to create after the release (e.g. 10.9). Leave empty to auto-increment the last segment.'
        required: false
        type: string
      dry-run:
        description: 'Test mode: use Jira sandbox and create a draft GitHub release'
        required: false
        default: false
        type: boolean

jobs:
  release:
    name: Release
    uses: SonarSource/release-github-actions/.github/workflows/ide-automated-release.yml@${WORKFLOW_SHA}
    if: always() && !failure() && !cancelled()
    permissions:
      statuses: read
      id-token: write
      contents: write
      actions: write
      pull-requests: write
    with:
      jira-project-key: "${JIRA_PROJECT_KEY}"
      project-name: "${PROJECT_NAME}"
      short-description: ${{ inputs.short-description }}
      branch: ${{ inputs.branch }}
      slack-channel: "${SLACK_CHANNEL}"
      is-test-run: ${{ inputs.dry-run == true }}
      new-version: ${{ inputs.new-version }}
```

#### Variant C: With version bump (Maven), with dry-run input

Use `tool: maven` for the `bump-version` action. Replace the `bump-version` job with Variant D or E if using a different build system.

```yaml
name: ${WORKFLOW_NAME}

on:
  workflow_dispatch:
    inputs:
      short-description:
        description: 'A short description for the release ticket'
        required: true
        type: string
      branch:
        description: 'The branch from which to release.'
        required: false
        default: '${DEFAULT_BRANCH}'
        type: string
      new-version:
        description: 'New Jira version to create after the release (e.g. 10.9). Leave empty to auto-increment the last segment.'
        required: false
        type: string
      dry-run:
        description: 'Test mode: use Jira sandbox and create a draft GitHub release'
        required: false
        default: false
        type: boolean

jobs:
  release:
    name: Release
    uses: SonarSource/release-github-actions/.github/workflows/ide-automated-release.yml@${WORKFLOW_SHA}
    if: always() && !failure() && !cancelled()
    permissions:
      statuses: read
      id-token: write
      contents: write
      actions: write
      pull-requests: write
    with:
      jira-project-key: "${JIRA_PROJECT_KEY}"
      project-name: "${PROJECT_NAME}"
      short-description: ${{ inputs.short-description }}
      branch: ${{ inputs.branch }}
      slack-channel: "${SLACK_CHANNEL}"
      is-test-run: ${{ inputs.dry-run == true }}
      new-version: ${{ inputs.new-version }}

  bump-version:
    name: Bump version
    needs:
      - release
    runs-on: ${RUNNER}
    permissions:
      id-token: write
      contents: write
      pull-requests: write
    steps:
      - uses: SonarSource/release-github-actions/bump-version@${WORKFLOW_SHA}
        with:
          version: ${{ needs.release.outputs.new-version }}
          token: ${{ github.token }}
          tool: maven
          base-branch: ${{ inputs.branch }}
          # pr-labels: "${BUMP_VERSION_PR_LABELS}"  # uncomment and set if needed
          # excluded-modules: "${EXCLUDED_MODULES}"  # uncomment and set if needed
```

Omit the `pr-labels` line if the user did not provide any labels. Replace the `excluded-modules` comment with an actual value if the user provided modules to exclude; otherwise omit the line entirely.

#### Variant D: With version bump (Gradle or mixed), with dry-run input

Same as Variant C but omit `tool:` in the `bump-version` step. The default shell script updates both `pom.xml` and `gradle.properties` files:

```yaml
      - uses: SonarSource/release-github-actions/bump-version@${WORKFLOW_SHA}
        with:
          version: ${{ needs.release.outputs.new-version }}
          token: ${{ github.token }}
          base-branch: ${{ inputs.branch }}
          # pr-labels: "${BUMP_VERSION_PR_LABELS}"  # uncomment and set if needed
          # excluded-modules: "${EXCLUDED_MODULES}"  # uncomment and set if needed
```

The `bump-version` job permissions are the same as Variant C (`id-token: write`, `contents: write`, `pull-requests: write`). Apply the same `excluded-modules` substitution rule as Variant C.

#### Variant E: With version bump (custom command), with dry-run input

When the build system is neither Maven nor Gradle (or the user needs a custom bump command):

```yaml
  bump-version:
    name: Bump version
    needs:
      - release
    runs-on: ${RUNNER}
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - name: Bump version
        env:
          NEW_VERSION: ${{ needs.release.outputs.new-version }}
        run: |
          ${USER_PROVIDED_BUMP_COMMAND}
      - uses: SonarSource/release-github-actions/create-pull-request@${WORKFLOW_SHA}
        with:
          commit-message: Prepare next development iteration ${{ needs.release.outputs.new-version }}
          title: Prepare next development iteration ${{ needs.release.outputs.new-version }}
          branch: bot/prepare-next-development-iteration-${{ needs.release.outputs.new-version }}
          base: ${{ inputs.branch }}
          reviewers: ${{ github.actor }}
```

**Important**: For Variant E, ask the user to review the `actions/checkout` and `create-pull-request` SHA pins and update them to match the versions already used in other workflows in the repo, if any.

---

### Step 6: Create Branch and Commit

```bash
git checkout -b add-devex-release-workflow
```

Stage the new and modified files:

```bash
git add .github/workflows/full-release${EXT}
git add .github/workflows/release.yml
```

Commit:

```bash
git commit -m "Add Development Experience automated release workflow"
```

---

### Step 7: Provide Testing and Next-Step Instructions

#### Testing with dry-run (if dry-run input was included):

1. Merge or push the workflow to the default branch (GitHub Actions only runs `workflow_dispatch` on the default branch by default).
2. Go to **Actions → {WORKFLOW_NAME} → Run workflow**.
3. Set `dry-run: true`.
4. Verify in the Jira sandbox that a REL ticket was created.
5. Verify a **draft** GitHub release was created (not published).

#### First real release:

1. Go to **Actions → {WORKFLOW_NAME} → Run workflow**.
2. Fill in `short-description` with a summary of what the release contains.
3. Override `branch` if releasing from a non-default branch.
4. Leave `dry-run` unchecked (or false).

#### After a successful release:

- Review and merge the bump-version pull request (if version bumping is enabled).
- Verify the Jira REL ticket status moved to **Technical Release Done**.
- Check the GitHub release was published correctly.

---

### Notes and Common Variations

- **`pm-email`**: The PM email defaults to the Development Experience PM (`farah.bouassida@sonarsource.com`). If a different PM should receive the release ticket, add `pm-email: "pm@example.com"` to the `with:` block.
- **`documentation-status`**: Defaults to `N/A`. To override, add `documentation-status: "Done"` to the `with:` block.
- **SHA pinning**: All templates use a pinned commit SHA resolved in Step 1 (`${WORKFLOW_SHA}`). This makes the workflow tamper-proof and lets Renovate bot track and auto-update the pin. The format is `@<sha> # <version>` (e.g., `@2d944d5ff92467db2dee4e1629a6c1b88cc6e953 # 1.4.3`).

---

### References

- Reusable Workflow (`ide-automated-release.yml`): https://github.com/SonarSource/release-github-actions/blob/master/.github/workflows/ide-automated-release.yml
- Bump Version Action: https://github.com/SonarSource/release-github-actions/tree/master/bump-version
- Example (SonarLint Core): https://github.com/SonarSource/sonarlint-core/blob/master/.github/workflows/full-release.yml
