# Update Plugins Deployer Action

Updates a plugin version in [sonar-plugins-deployer](https://github.com/SonarSource/sonar-plugins-deployer) by modifying the version anchor in the `versions:` block of `plugins.yaml`, and creates a pull request with the change.

## Description

The action updates analyzer versions by:
1. Validating the ticket key starts with `SC-`
2. Checking out `plugins.yaml` from `sonar-plugins-deployer`
3. For each artifact, computing the anchor key (strips `-enterprise` suffix; maps `csharp`/`vbnet` → `dotnet`)
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
| `plugin-name` | Plugin language key, used for PR title, commit and branch name | Yes | |
| `secret-name` | Vault secret name granting write access to `sonar-plugins-deployer` | Yes | |
| `plugin-artifacts` | Comma-separated artifact names to update; falls back to `plugin-name` | No | |
| `base-branch` | Base branch for the PR | No | `master` |
| `draft` | Create PR as draft (`true`/`false`) | No | `false` |
| `reviewers` | Comma-separated GitHub usernames to request review from | No | |
| `pull-request-body` | Body of the pull request | No | |

## Outputs

| Output | Description |
|---|---|
| `pull-request-url` | URL of the created pull request |

## Artifact to anchor key mapping

| Artifact (plugin-artifacts value) | Anchor key in plugins.yaml |
|---|---|
| `java` | `sonar-java` |
| `security` | `sonar-security` |
| `go-enterprise` | `sonar-go` |
| `iac-enterprise` | `sonar-iac` |
| `text-enterprise` | `sonar-text` |
| `python-enterprise` | `sonar-python` |
| `csharp-enterprise` | `sonar-dotnet` |
| `vbnet-enterprise` | `sonar-dotnet` |

General rule: strip `-enterprise` suffix, prepend `sonar-`. Exception: `csharp` and `vbnet` both map to `sonar-dotnet`.

## Usage

```yaml
- name: Update analyzer in sonar-plugins-deployer
  uses: SonarSource/release-github-actions/update-plugins-deployer@v1
  with:
    release-version: '1.12.0.12345'
    ticket-key: 'SC-67890'
    plugin-name: 'java'
    secret-name: 'sonar-java-release-automation'
```

```yaml
- name: Update Java analyzer (plugin + symbolic execution)
  uses: SonarSource/release-github-actions/update-plugins-deployer@v1
  with:
    release-version: '8.30.0.44000'
    ticket-key: 'SC-12345'
    plugin-name: 'java'
    secret-name: 'sonar-java-release-automation'
    plugin-artifacts: 'java,java-symbolic-execution'
```
