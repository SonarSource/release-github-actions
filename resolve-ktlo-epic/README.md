# Resolve KTLO Epic Action

Finds the current KTLO (Keep The Lights On) epic in a Jira project by querying for in-progress epics whose summary matches a configurable regex pattern.

When zero matches are found, the action logs a warning and outputs an empty string — it does **not** fail, so callers can proceed without a parent. When multiple matches are found, the action picks the first and logs a warning.

## Dependencies

- [SonarSource/vault-action-wrapper](https://github.com/SonarSource/vault-action-wrapper) for retrieving Jira credentials

## Inputs

| Input | Description | Required | Default |
|---|---|---|---|
| `jira-project` | The Jira project key to search in (e.g. `CPP`) | Yes | - |
| `epic-name-pattern` | Regex pattern matched case-insensitively against epic summaries | No | `KTLO` |
| `use-jira-sandbox` | Use the Jira sandbox instead of production | No | - |

## Outputs

| Output | Description |
|---|---|
| `epic-key` | Key of the matching KTLO epic (e.g. `CPP-7858`), or empty string if none found |

## Usage

### Basic usage

```yaml
- name: Resolve KTLO Epic
  id: ktlo
  uses: SonarSource/release-github-actions/resolve-ktlo-epic@v1
  with:
    jira-project: CPP

- name: Create Integration Ticket
  uses: SonarSource/release-github-actions/create-integration-ticket@v1
  with:
    target-jira-project: SONAR
    release-ticket-key: REL-123
    plugin-name: cfamily
    parent-epic: ${{ steps.ktlo.outputs.epic-key }}
```

### With custom pattern

```yaml
- name: Resolve KTLO Epic
  id: ktlo
  uses: SonarSource/release-github-actions/resolve-ktlo-epic@v1
  with:
    jira-project: NET
    epic-name-pattern: 'KTLO\s+\d{4}'
```

### With sandbox

```yaml
- name: Resolve KTLO Epic
  uses: SonarSource/release-github-actions/resolve-ktlo-epic@v1
  with:
    jira-project: CPP
    use-jira-sandbox: 'true'
```
