# release-github-actions

A centralized collection of reusable GitHub Actions designed to streamline and automate every stage of the analyzer release process. This repository serves as a versatile toolbox, offering modular automations to eliminate manual, repetitive steps and reduce friction across squads managing analyzer projects. Whether standardizing changelog generation, automating version bumps, handling release publishing, or coordinating cross-repository tasks, these actions help teams back away from cumbersome workflows and focus more on code quality. Pick and combine the automations best suited for your analyzer’s unique release requirements, and easily extend the toolbox to cover new scenarios as they arise.

## Available Actions

| Action | Description |
|--------|-------------|
| [Check Releasability Status](check-releasability-status/README.md) | Checks the releasability status and extracts the version if successful |
| [Create Integration Ticket](create-integration-ticket/README.md) | Creates a Jira integration ticket with a custom summary and links it to another existing ticket |
| [Create Pull Request](create-pull-request/README.md) | Creates or updates a pull request using the `gh` CLI, with vault-based token resolution |
| [Create Jira Release Ticket](create-jira-release-ticket/README.md) | Automates the creation of an "Ask for release" ticket in Jira |
| [Create Jira Version](create-jira-version/README.md) | Creates a new version in a Jira project, with the ability to automatically determine the next version number |
| [Get Jira Release Notes](get-jira-release-notes/README.md) | Fetches Jira release notes and generates the release notes URL for a given project and version |
| [Get Jira Version](get-jira-version/README.md) | Extracts a Jira-compatible version number from a release version by formatting it appropriately for Jira |
| [Get Release Version](get-release-version/README.md) | Extracts the release version from the repox status on a specified branch |
| [Lock Branch](lock-branch/README.md) | Locks or unlocks a branch by modifying the `lock_branch` setting in branch protection rules |
| [Notify Slack on Failure](notify-slack/README.md) | Sends a Slack notification when a job fails |
| [Publish GitHub Release](publish-github-release/README.md) | Publishes a GitHub Release with notes fetched from Jira or provided directly |
| [Release Jira Version](release-jira-version/README.md) | Releases a Jira version and creates the next one |
| [Update Analyzer](update-analyzer/README.md) | Updates an analyzer version in SonarQube or SonarCloud and creates a pull request |
| [Update Release Ticket Status](update-release-ticket-status/README.md) | Updates the status of a Jira release ticket and can change its assignee |
| [Update Rule Metadata](update-rule-metadata/README.md) | Automates updating rule metadata across all supported languages using the rule-api tooling |

## Available Workflows

| Workflow | Description |
|----------|-------------|
| [Automated Release Workflow](docs/AUTOMATED_RELEASE.md) | Orchestrates the end-to-end release across Jira and GitHub, with optional integration tickets and analyzer PRs |

## Claude Code Skills

This repository includes Claude Code skills for automating common tasks related to release workflows. Skills are instruction files (`.claude/skills/<skill-name>/SKILL.md`) that teach Claude Code how to perform specific tasks, using YAML frontmatter for metadata followed by detailed instructions.

### Available Skills

| Skill | Description |
|-------|-------------|
| [automated-release-setup](.claude/skills/automated-release-setup/) | Set up automated release workflow for SonarSource analyzer projects |

### Usage

#### In this repository (automatic)

Skills in `.claude/skills/` are automatically discovered by Claude Code when you work in this repository. Simply ask Claude Code to perform the task:

- "Set up automated release workflow"
- "Configure automated release for this project"
- "Help me create the release automation workflows"

Or use the slash command: `/automated-release-setup`

#### In other repositories (manual installation)

To use these skills in other repositories, you can either download them or symlink them.

**Option 1: Download and Install Manually**

```bash
# Create the skills directory if it doesn't exist
mkdir -p .claude/skills/automated-release-setup

# Download the skill
curl -o .claude/skills/automated-release-setup/SKILL.md \
  https://raw.githubusercontent.com/SonarSource/release-github-actions/master/.claude/skills/automated-release-setup/SKILL.md
```

**Option 2: Clone and Symlink**

1. Clone this repository (if you haven't already):

   ```bash
   git clone https://github.com/SonarSource/release-github-actions.git
   ```

2. Create a symlink to the skill directory in your target repository:

   ```bash
   mkdir -p .claude/skills
   ln -s /path/to/release-github-actions/.claude/skills/automated-release-setup \
     .claude/skills/automated-release-setup
   ```

### Updating Skills

```bash
# If installed via curl
curl -o .claude/skills/automated-release-setup/SKILL.md \
  https://raw.githubusercontent.com/SonarSource/release-github-actions/master/.claude/skills/automated-release-setup/SKILL.md

# If installed via symlink, just pull the latest changes
cd /path/to/release-github-actions
git pull
```

### Creating New Skills

1. Create a new directory under `.claude/skills/` with your skill name
2. Add a `SKILL.md` file with YAML frontmatter (`name`, `description`) followed by the skill instructions
3. Update this README to include your skill in the "Available Skills" table
4. Submit a pull request

```markdown
---
name: my-skill-name
description: >
  Trigger description explaining when Claude Code should activate this skill.
  Include example phrases like "set up X", "configure Y", etc.
---

# Skill Title

Detailed instructions for Claude Code to follow...
```

## Development

### Update Action Versions Workflow

The repository includes an `update-action-versions` workflow that creates a pull request to update all internal action references to use a specific commit or the latest version from the master branch. This workflow scans all `action.yml` files in the repository and updates any references to `SonarSource/release-github-actions` actions to point to the specified reference, ensuring consistency across all actions when updates are made to shared components.
