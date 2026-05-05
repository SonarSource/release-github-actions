# Publish GitHub Release Action

This GitHub Action automates the creation of a GitHub Release using provided release notes and then triggers a downstream release workflow.

## Description

The action performs the following steps:
1. Validates that either a `release-version` input or `RELEASE_VERSION` environment variable is provided
2. Creates a GitHub release using the provided release notes
3. Automatically triggers a specified release workflow in the caller repository
4. Monitors the workflow execution and waits for it to complete

## gh-action_release v6/v7 Compatibility

The action automatically detects whether the caller's release workflow uses `gh-action_release` v6 or v7 by inspecting the workflow file:

- **v6**: Uses the original flow — publishes releases when `draft=false`, passes `releaseId` to the triggered workflow.
- **v7 (default)**: Uses a draft-first flow — always creates draft releases and passes only `version` and `dryRun`. `gh-action_release` v7 handles the draft-to-published promotion after successful artifact promotion.

No changes are needed in calling workflows — the detection is automatic.

## Duplicate Release Handling

The action automatically checks for existing releases with the same title before creating a new one:

- **When `draft=true`**: If a release with the same title already exists, the action logs a warning and skips creation without failing.
- **When `draft=false`**: If an existing draft release with the same title is found, it will be published instead of creating a new release. If a published release with the same title already exists, the action will fail with an error.
- **When using v7**: Existing drafts are reused (idempotent). Existing published releases cause an error.

## Release Workflow Triggering

After creating the GitHub release, this action automatically triggers a release workflow in the caller repository. The action:

- Triggers the specified release workflow (default: `release.yml`)
- Passes the release tag name, release ID (v6 only), and dry-run flag (based on the `draft` input) to the triggered workflow
- Monitors the workflow execution and waits for it to complete (checking only runs from the last 5 minutes)
- Succeeds if the release workflow completes successfully, or fails if the release workflow fails

This ensures that the entire release process (GitHub release creation + downstream release workflow) succeeds or fails as a unit.

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
- Detects `gh-action_release` version by grepping the caller's release workflow for `@v6` or `@v7`
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
