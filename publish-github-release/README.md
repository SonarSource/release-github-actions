# Publish GitHub Release Action

This GitHub Action automates the creation of a GitHub Release using provided release notes and then triggers a downstream release workflow.

## Description

The action performs the following steps:
1. Validates that either a `release-version` input or `RELEASE_VERSION` environment variable is provided
2. Creates a **draft** GitHub release (or reuses an existing draft)
3. Optionally downloads artifacts from Repox and attaches them to the draft
4. Publishes the draft release (v6 with `draft=false` only; v7 defers to the downstream workflow)
5. Triggers a specified release workflow in the caller repository
6. Monitors the workflow execution and waits for it to complete

## gh-action_release v6/v7 Compatibility

The action automatically detects whether the caller's release workflow uses `gh-action_release` v6 or v7 by inspecting the workflow file. Detection works with all common pinning strategies:

- **Tag references**: `@v6`, `@6.8.1`

- **SHA-pinned with version comment**: `@abc123def # 6.8.1`
- **`releaseId` fallback**: If no version is detected from the action reference, the presence of a `releaseId` input in the workflow indicates v6.
- **Default**: If none of the above match, v7 is assumed.

Both versions use a draft-first flow — releases are always created as drafts so that artifacts can be attached before publishing.

- **v6**: Creates a draft, attaches artifacts, then publishes the draft when `draft=false`. Passes `releaseId` to the triggered workflow.
- **v7 (default)**: Creates a draft, attaches artifacts, then passes only `version` and `dryRun` to the triggered workflow. `gh-action_release` v7 handles the draft-to-published promotion after successful artifact promotion.

No changes are needed in calling workflows — the detection is automatic.

## Duplicate Release Handling

The action automatically checks for existing releases with the same title before creating a new one:

- Existing **draft** releases are reused (idempotent). Artifacts are re-attached with `--clobber`, and the release is published after attachment if needed.
- Existing **published** releases always cause an error.

## Release Workflow Triggering

After creating the GitHub release, this action automatically triggers a release workflow in the caller repository. The action:

- Triggers the specified release workflow (default: `release.yml`)
- Passes the release tag name, release ID (v6 only), and dry-run flag (based on the `draft` input) to the triggered workflow
- Monitors the workflow execution and waits for it to complete (checking only runs from the last 5 minutes)
- Succeeds if the release workflow completes successfully, or fails if the release workflow fails

This ensures that the entire release process (GitHub release creation + downstream release workflow) succeeds or fails as a unit.

## Artifact Attachment

The action can optionally download artifacts from Repox (JFrog Artifactory) and attach them to the draft GitHub release before triggering the downstream release workflow. Two inputs control this:

- `release-artifacts-public`: Paths authenticated with the `{REPO}-public-reader` Vault role
- `release-artifacts-private`: Paths authenticated with the `{REPO}-private-reader` Vault role

Each path should include the Artifactory repository name and can use `{version}` as a placeholder that is replaced with the validated release version at runtime. On retries, existing assets are overwritten (`--clobber`).

```yaml
- name: Publish GitHub Release
  uses: SonarSource/release-github-actions/publish-github-release@v1
  with:
    release-version: 'v1.2.3.456'
    release-artifacts-public: |
      sonarsource-public-builds/org/sonarsource/java/sonar-java-plugin/{version}/sonar-java-plugin-{version}.jar
    release-artifacts-private: |
      sonarsource-nuget-private-builds/A3S.NET.{version}.nupkg
    draft: false
```

### Vault Roles

The calling repository must have the appropriate Vault roles configured:
- `{REPO}-public-reader` for public artifact downloads
- `{REPO}-private-reader` for private artifact downloads

The calling job must have `id-token: write` permission for Vault authentication.

## Prerequisites

This action requires a GitHub token with `contents: write`, `id-token: write`, and `actions: write` permissions to create releases and trigger workflows.

## Inputs

| Input              | Description                                                                                                                                            | Required | Default               |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|----------|-----------------------|
| `github-token`     | The GitHub token for API calls.                                                                                                                        | Yes      | `${{ github.token }}` |
| `release-version`  | The version number for the new release (e.g., `v1.0.0`). This will also be the tag name. If not provided, uses `RELEASE_VERSION` environment variable. | No       |                       |
| `branch`           | The branch, commit, or tag to create the release from.                                                                                                 | No       | `master`              |
| `release-notes`    | The full markdown content for the release notes.                                                                                                       | No       |                       |
| `draft`            | A boolean value to indicate if the release should be a draft.                                                                                          | No       | `true`                |
| `release-workflow` | The filename of the release workflow to trigger in the caller repository.                                                                              | No       | `release.yml`         |
| `release-artifacts-public` | Newline-separated Repox paths for public artifacts to attach to the release. Include the Artifactory repo name in each path. Use `{version}` as a placeholder. Authenticated via `{REPO}-public-reader` Vault role. | No | |
| `release-artifacts-private` | Newline-separated Repox paths for private artifacts to attach to the release. Include the Artifactory repo name in each path. Use `{version}` as a placeholder. Authenticated via `{REPO}-private-reader` Vault role. | No | |

## Outputs

| Output        | Description                           |
|---------------|---------------------------------------|
| `release-url` | The URL of the newly created release. |

## Usage

### Basic usage with version input

```yaml
- name: Publish GitHub Release
  uses: SonarSource/release-github-actions/publish-github-release@v1
  with:
    release-version: 'v1.2.3'
    release-notes: |
      ## What's New
      - Added new feature X
      - Fixed bug Y

      ## Breaking Changes
      - Removed deprecated API Z
    draft: false
```

### Using RELEASE_VERSION environment variable

```yaml
- name: Publish GitHub Release
  uses: SonarSource/release-github-actions/publish-github-release@v1
  env:
    RELEASE_VERSION: 'v1.2.3'
  with:
    release-notes: |
      ## Release Notes
      Content generated from previous steps...
    draft: false
```

### With custom release workflow

```yaml
- name: Publish GitHub Release
  uses: SonarSource/release-github-actions/publish-github-release@v1
  with:
    release-version: 'v1.2.3'
    release-notes: ${{ steps.generate-notes.outputs.notes }}
    release-workflow: 'custom-release.yml'
    branch: 'main'
    draft: true
```

## Implementation Details

The action:
- Uses the GitHub CLI (`gh`) to create releases and trigger workflows
- Validates version input using either the `release-version` input or `RELEASE_VERSION` environment variable
- Detects `gh-action_release` version by checking the caller's release workflow for v6 references (`@v6` or `@6.x.y` tag, `# 6` comment, or `releaseId` input); defaults to v7 if not found
- Creates releases with provided markdown content directly
- Monitors triggered workflows with a 5-minute time window to prevent picking up stale runs
- Uses kebab-case naming conventions for all inputs and outputs

## Error Handling

The action will fail with a non-zero exit code if:
- Neither `release-version` input nor `RELEASE_VERSION` environment variable is provided
- The GitHub API calls fail (authentication, permissions, etc.)
- A published release with the same title already exists when `draft=false`
- The triggered release workflow fails or is cancelled
- The workflow run ID cannot be retrieved after triggering

## Notes

- Release notes are provided directly as input
- The action requires the GitHub CLI tool (pre-installed on GitHub-hosted runners)
- Workflow monitoring only considers runs from the last 5 minutes to avoid timing issues
- The action ensures atomic success/failure of both release creation and workflow execution
