# Create Pull Request Action

This GitHub Action creates or updates a pull request using the `gh` CLI. It is designed as an in-house replacement for `peter-evans/create-pull-request`, with integrated vault-based token resolution.

## Description

The action:
- Stages and commits file changes on a new branch
- Creates a pull request if one doesn't exist, or updates an existing one
- Supports all common PR options: labels, reviewers, assignees, milestones, drafts
- Automatically resolves authentication tokens via vault, falling back to the provided input token

## Prerequisites

- The repository must be checked out before using this action
- A GitHub token with `contents: write` and `pull-requests: write` permissions
- For vault token resolution: `id-token: write` permission and a vault secret at `development/github/token/{REPO_OWNER_NAME_DASH}-release-automation`

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `token` | GitHub token (vault token preferred, falls back to this) | No | `${{ github.token }}` |
| `add-paths` | Comma or newline-separated file paths to stage | No | `''` (all changes) |
| `commit-message` | Commit message for changes | No | `[create-pull-request] automated change` |
| `committer` | Committer in `Name <email>` format | No | `github-actions[bot] <...>` |
| `author` | Author in `Name <email>` format | No | `${{ github.actor }} <...>` |
| `signoff` | Add `Signed-off-by` trailer | No | `false` |
| `branch` | PR branch name | No | `create-pull-request/patch` |
| `branch-suffix` | Suffix: `random`, `timestamp`, or `short-commit-hash` | No | `''` |
| `base` | Base branch for PR | No | Current branch |
| `title` | PR title | No | `Changes by create-pull-request action` |
| `body` | PR body | No | `''` |
| `body-path` | File path for PR body content | No | `''` |
| `labels` | Comma or newline-separated labels | No | `''` |
| `assignees` | Comma or newline-separated assignees | No | `''` |
| `reviewers` | Comma or newline-separated reviewers | No | `''` |
| `team-reviewers` | Comma or newline-separated team reviewers | No | `''` |
| `milestone` | Milestone number | No | `''` |
| `draft` | Create as draft PR | No | `false` |
| `delete-branch` | Delete branch after PR is merged | No | `false` |
| `maintainer-can-modify` | Allow maintainer edits | No | `true` |

## Outputs

| Output | Description |
|--------|-------------|
| `pull-request-number` | The number of the created or updated PR |
| `pull-request-url` | The URL of the created or updated PR |
| `pull-request-operation` | The operation performed: `created`, `updated`, or `none` |
| `pull-request-head-sha` | The SHA of the head commit on the PR branch |
| `pull-request-branch` | The name of the PR branch |

## Usage

### Basic usage

```yaml
- uses: actions/checkout@v4

- name: Make changes
  run: echo "updated" > file.txt

- name: Create Pull Request
  uses: SonarSource/release-github-actions/create-pull-request@v1
  with:
    title: 'Automated update'
    branch: bot/automated-update
```

### With explicit token

```yaml
- name: Create Pull Request
  uses: SonarSource/release-github-actions/create-pull-request@v1
  with:
    token: ${{ secrets.MY_TOKEN }}
    commit-message: 'Update dependencies'
    title: 'Update dependencies'
    branch: bot/update-deps
```

### With labels and reviewers

```yaml
- name: Create Pull Request
  uses: SonarSource/release-github-actions/create-pull-request@v1
  with:
    title: 'Update rule metadata'
    branch: bot/update-rule-metadata
    branch-suffix: timestamp
    labels: skip-qa
    reviewers: user1,user2
    team-reviewers: team-a
```

### With draft PR

```yaml
- name: Create Pull Request
  uses: SonarSource/release-github-actions/create-pull-request@v1
  with:
    title: 'WIP: New feature'
    branch: bot/new-feature
    draft: true
    body: |
      ## Summary
      This PR adds a new feature.

      ## Details
      - Change 1
      - Change 2
```

### With branch suffix

```yaml
- name: Create Pull Request
  uses: SonarSource/release-github-actions/create-pull-request@v1
  with:
    title: 'Automated changes'
    branch: bot/changes
    branch-suffix: timestamp  # or: random, short-commit-hash
```

## Token Resolution

The action resolves the GitHub token using the following priority:

1. **Vault token** (preferred): Fetches `development/github/token/{REPO_OWNER_NAME_DASH}-release-automation` via `SonarSource/vault-action-wrapper@v3` with `continue-on-error: true`
2. **Input token** (fallback): Uses the `token` input (defaults to `${{ github.token }}`)

If both fail, the action errors. This design allows the action to work in repositories with vault access (using a more privileged token) while gracefully falling back to the workflow token.

## Migration from peter-evans/create-pull-request

This action provides a compatible interface. Key differences:

| Feature | peter-evans/create-pull-request | This action |
|---------|--------------------------------|-------------|
| Runtime | Node.js | Bash + `gh` CLI |
| Token | Input only | Vault-preferred, input fallback |
| Push | Built-in | `git push --force-with-lease` |
| PR create/update | GitHub API | `gh pr create` / `gh pr edit` |

To migrate, replace the `uses:` reference and ensure inputs match. Most inputs are compatible by name and behavior.

## Behavior

### No changes detected
When no files have changed, the action outputs `pull-request-operation=none` and exits successfully without creating a branch or PR.

### Existing PR
When an open PR already exists for the same head and base branch, the action updates it (title, body, labels, reviewers) rather than creating a duplicate.

### Branch management
- The action uses `git checkout -B` to create or reset the PR branch
- Push uses `--force-with-lease` to safely update the remote branch
- When `delete-branch: true`, the branch is deleted only after the PR is merged

## Error Handling

The action will fail if:
- No valid token is available (vault and input both empty)
- The committer format is invalid
- An invalid `branch-suffix` value is provided
- Git operations fail (commit, push)
- PR creation or update fails
