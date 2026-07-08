# Update Plugins Deployer Action

Updates a plugin version in [sonar-plugins-deployer](https://github.com/SonarSource/sonar-plugins-deployer) by modifying the version anchor in the `versions:` block of `plugins.yaml`, and creates a pull request with the change.

## Description

The action updates analyzer versions by:
1. Validating the ticket key starts with `SC-`
2. Checking out `plugins.yaml` from `sonar-plugins-deployer`
3. Computing the anchor key from `plugin-name` (strips `-enterprise` suffix; maps `csharp`/`vbnet` → `dotnet`)
4. Updating the version anchor in the `versions:` block — all alias references in `plugins:` pick up the new value automatically
5. Creating a pull request with the changes

## Prerequisites

The `secret-name` provided must have `contents: write` and `pull-requests: write` permissions on `SonarSource/sonar-plugins-deployer`. Add `sonar-plugins-deployer` to the repositories list of the `release-automation` secret in `re-terraform-aws-vault`.

## Dependencies

- [SonarSource/vault-action-wrapper@v3](https://github.com/SonarSource/vault-action-wrapper) for secure token retrieval
- [actions/checkout@v4](https://github.com/actions/checkout) for repository checkout
- [SonarSource/release-github-actions/create-pull-request](../create-pull-request) for pull request creation

## Inputs

| Input | Description | Required | Default |
|---|---|---|---|
| `release-version` | The new version to set (e.g. `1.12.0.12345`) | Yes | |
| `ticket-key` | Jira ticket number. Must start with `SC-`. | Yes | |
| `plugin-name` | Plugin language key, used for the anchor lookup, PR title, commit and branch name | Yes | |
| `sonar-prefix` | Whether the anchor key is prefixed with `sonar-` (`true`/`false`) | No | `true` |
| `secret-name` | Vault secret name granting write access to `sonar-plugins-deployer` | Yes | |
| `base-branch` | Base branch for the PR | No | `master` |
| `draft` | Create PR as draft (`true`/`false`) | No | `false` |
| `reviewers` | Comma-separated GitHub usernames to request review from | No | |
| `pull-request-body` | Body of the pull request | No | |

## Outputs

| Output | Description |
|---|---|
| `pull-request-url` | URL of the created pull request |

## Plugin-name to anchor key mapping

| `plugin-name` value | Anchor key in `plugins.yaml` |
|---|---|
| `java` | `sonar-java` |
| `security` | `sonar-security` |
| `go-enterprise` | `sonar-go` |
| `iac-enterprise` | `sonar-iac` |
| `text-enterprise` | `sonar-text` |
| `python-enterprise` | `sonar-python` |
| `dotnet-enterprise` | `sonar-dotnet` |
| `php`, `kotlin`, etc. | `sonar-{plugin-name}` |
| `java-a3s-context-collector` | `java-a3s-context-collector` |

General rule: strip `-enterprise` suffix, then prepend `sonar-` when `sonar-prefix` is `true` (the default). Exceptions:
- `dotnet-enterprise` maps to `sonar-dotnet` (covers both `csharp-enterprise` and `vbnet-enterprise` via aliases).
- Plugins whose anchor is **not** prefixed with `sonar-` (e.g. `java-a3s-context-collector`) must be updated by passing `sonar-prefix: false`.

## Usage

```yaml
- name: Update PHP analyzer in sonar-plugins-deployer
  uses: SonarSource/release-github-actions/update-plugins-deployer@v1
  with:
    release-version: '3.58.0.16057'
    ticket-key: 'SC-67890'
    plugin-name: 'php'
    secret-name: 'sonar-php-release-automation'
```

```yaml
- name: Update security analyzer (all frontends share the sonar-security anchor)
  uses: SonarSource/release-github-actions/update-plugins-deployer@v1
  with:
    release-version: '11.30.0.46000'
    ticket-key: 'SC-12345'
    plugin-name: 'security'
    secret-name: 'sonar-security-release-automation'
```
