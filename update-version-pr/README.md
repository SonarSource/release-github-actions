# Update Version PR

Checks out a target repository (sparse), runs a caller-supplied edit script, and opens a pull request via [`create-pull-request`](../create-pull-request/README.md).

This action owns the common wrapper shared by [`update-analyzer`](../update-analyzer/README.md), [`update-analysis-as-a-service`](../update-analysis-as-a-service/README.md), and [`update-plugins-deployer`](../update-plugins-deployer/README.md). Each of those actions holds its own edit script (the genuinely-different file-format logic) and calls this action for the git/PR plumbing.

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `secret-name` | ✅ | | Vault secret name. Resolves to `development/github/token/SonarSource-<secret-name>`. |
| `target-repo` | ✅ | | Repository to check out, e.g. `SonarSource/sonar-plugins-deployer`. |
| `sparse-paths` | ✅ | | Sparse-checkout path(s) for the target file(s). |
| `base-branch` | | `master` | Branch to check out and target for the PR. |
| `edit-script` | ✅ | | Absolute path to the script that edits the checked-out file(s). Pass `${{ github.action_path }}/your-script.sh` from the calling action so the path resolves to the caller's directory. |
| `edit-env` | | `''` | Newline-separated `KEY=VALUE` pairs exported into the environment before the edit script runs. |
| `commit-message` | ✅ | | Commit message for the pull request. |
| `title` | ✅ | | Pull request title. |
| `body` | | `''` | Pull request body. |
| `branch` | ✅ | | Branch name for the pull request. |
| `draft` | | `false` | Open the pull request as a draft. |
| `reviewers` | | `''` | Comma-separated list of GitHub usernames to request review from. |

## Outputs

| Output | Description |
|--------|-------------|
| `pull-request-url` | URL of the created or updated pull request. |

## Usage

```yaml
- name: Update version and open PR
  uses: SonarSource/release-github-actions/update-version-pr@v1
  with:
    secret-name: my-analyzer-release-automation
    target-repo: SonarSource/my-target-repo
    sparse-paths: path/to/version-file.toml
    edit-script: ${{ github.action_path }}/update_version.sh
    edit-env: |
      TARGET_FILE=path/to/version-file.toml
      PLUGIN_NAME=${{ inputs.plugin-name }}
      RELEASE_VERSION=${{ inputs.release-version }}
    commit-message: '[MY-123] Update my-plugin to ${{ inputs.release-version }}'
    title: '[MY-123] Update my-plugin to ${{ inputs.release-version }}'
    branch: my-plugin/update-${{ inputs.release-version }}
    draft: ${{ inputs.draft }}
    reviewers: ${{ inputs.reviewers }}
```
