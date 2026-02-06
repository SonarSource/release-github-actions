# Claude Code Skills

This directory contains Claude Code skills for automating common tasks related to release workflows.

## What are Skills?

Skills are instruction files that teach Claude Code how to perform specific tasks. When you install a skill, Claude Code can automatically help you with that task when you ask for it.

## Available Skills

| Skill | Description |
|-------|-------------|
| [automated-release-setup](./automated-release-setup/) | Set up automated release workflow for SonarSource analyzer projects |

## Installation

### Option 1: Download and Install Manually

Download the skill file to your Claude Code skills directory:

```bash
# Create the skills directory if it doesn't exist
mkdir -p ~/.claude/skills

# Download the skill
curl -o ~/.claude/skills/automated-release-setup.md \
  https://raw.githubusercontent.com/SonarSource/release-github-actions/master/skills/automated-release-setup/automated-release-setup.md
```

### Option 2: Clone and Symlink

1. Clone this repository (if you haven't already):

   ```bash
   git clone https://github.com/SonarSource/release-github-actions.git
   ```

2. Create a symlink to the skill:

   ```bash
   mkdir -p ~/.claude/skills
   ln -s /path/to/release-github-actions/skills/automated-release-setup/automated-release-setup.md \
     ~/.claude/skills/automated-release-setup.md
   ```

## Usage

Once installed, simply ask Claude Code to help you with the task. For example:

- "Set up automated release workflow"
- "Configure automated release for this project"
- "Help me create the release automation workflows"

Claude Code will recognize the request and follow the skill instructions to guide you through the process.

## Updating Skills

To update a skill to the latest version:

```bash
# If installed via curl
curl -o ~/.claude/skills/automated-release-setup.md \
  https://raw.githubusercontent.com/SonarSource/release-github-actions/master/skills/automated-release-setup/automated-release-setup.md

# If installed via symlink, just pull the latest changes
cd /path/to/release-github-actions
git pull
```

## Creating New Skills

If you want to contribute a new skill:

1. Create a new directory under `skills/` with your skill name
2. Add a markdown file with the skill instructions (use the existing skill as a template)
3. Update this README and the main repository README to include your skill in the "Available Skills" table
4. Submit a pull request