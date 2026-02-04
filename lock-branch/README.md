# Lock Branch Action

This GitHub Action locks or unlocks a branch by modifying the `lock_branch` setting in branch protection rules.

## Description

The action modifies branch protection settings to:
- **Freeze (lock)**: Prevent all pushes and merges to the branch
- **Unfreeze (unlock)**: Allow normal operations on the branch

This is useful for temporarily locking a branch during release processes.

## Prerequisites

- Branch protection must be enabled on the target branch (or will be created with minimal settings)
- GitHub token with `administration:write` permissions

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `branch` | The branch name to lock/unlock | Yes | - |
| `freeze` | Set to `true` to lock (freeze), `false` to unlock (unfreeze) | Yes | - |
| `slack-channel` | Slack channel to notify about state changes | No | - |
| `github-token` | GitHub token with admin permissions | No | From Vault |
| `slack-token` | Slack token for notifications | No | From Vault |

## Outputs

| Output | Description |
|--------|-------------|
| `previous-state` | The previous lock state (`true`/`false`) |
| `current-state` | The current lock state (`true`/`false`) |
| `branch` | The branch that was modified |

## Usage

### Lock (freeze) a branch

```yaml
- name: Freeze master branch
  uses: SonarSource/release-github-actions/lock-branch@v1
  with:
    branch: master
    freeze: true
    slack-channel: '#releases'
```

### Unlock (unfreeze) a branch

```yaml
- name: Unfreeze master branch
  uses: SonarSource/release-github-actions/lock-branch@v1
  with:
    branch: master
    freeze: false
    slack-channel: '#releases'
```

### Use in automated release workflow

```yaml
jobs:
  freeze-branch:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: SonarSource/release-github-actions/lock-branch@v1
        with:
          branch: ${{ inputs.branch }}
          freeze: true
          slack-channel: ${{ inputs.slack-channel }}

  # ... release steps ...

  unfreeze-branch:
    needs: [release-steps]
    if: always()
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: SonarSource/release-github-actions/lock-branch@v1
        with:
          branch: ${{ inputs.branch }}
          freeze: false
          slack-channel: ${{ inputs.slack-channel }}
```

## Behavior

### Locking a branch
- Sets `lock_branch: true` in branch protection settings
- Prevents all pushes and merges to the branch
- Preserves all other existing branch protection settings

### Unlocking a branch
- Sets `lock_branch: false` in branch protection settings
- Allows normal push and merge operations
- Preserves all other existing branch protection settings

### Idempotent operation
- If the branch is already in the requested state, no changes are made
- The action will succeed and report the current state

### No existing protection
- If the branch has no existing protection, minimal protection is created with just the lock setting
- Existing protection settings are always preserved when updating

## Slack Notifications

When `slack-channel` is provided, the action sends a notification with:
- Lock/unlock icon indicating the action taken
- Branch name and repository
- Link to the workflow run

## Error Handling

The action will fail if:
- GitHub authentication fails
- Branch protection cannot be updated (e.g., insufficient permissions)
- API request fails

The action will succeed with a warning if:
- No branch protection exists (will create minimal protection with lock)
- Branch is already in the requested state
