# Bump Version Action

This GitHub Action bumps the project version to the next development iteration and optionally creates a Pull Request with the version changes.

## Description

The action automates version management by:
1. Extracting the current version from `gradle.properties` or `pom.xml` (removing `-SNAPSHOT` suffix)
2. Determining the next version (either from input or by auto-incrementing the minor version)
3. Updating the version in the appropriate build files to the new snapshot version
4. Optionally creating a Pull Request with the version changes

## Requirements

### Permissions
This action requires the following GitHub token permissions when creating Pull Requests:
```yaml
permissions:
  contents: write      # write for peter-evans/create-pull-request, read for actions/checkout
  pull-requests: write # write for peter-evans/create-pull-request
```

Note: If `create-pull-request` is set to `false`, only `contents: read` permission is required.

## Inputs

| Input                  | Description                                                                                           | Required | Default  |
|------------------------|-------------------------------------------------------------------------------------------------------|----------|----------|
| `version`              | Next version to set (e.g., 1.2.0) or leave empty to auto-increment the minor version                 | No       | -        |
| `create-pull-request`  | Create a Pull Request (true) or just output the next version (false)                                  | No       | `true`   |
| `pull-request-labels`  | Labels to add to the pull request                                                                     | No       | -        |
| `build-system`         | The build system used in the project (maven or gradle)                                               | No       | `gradle` |
| `maven-exclude-paths`  | Paths to exclude when updating Maven pom.xml files (space-separated list)                            | No       | -        |

## Outputs

| Output             | Description                                            |
|--------------------|--------------------------------------------------------|
| `current-version`  | The version of the current development iteration       |
| `next-version`     | The version of the next development iteration          |
| `pull-request-url` | The URL of the created Pull Request                    |
| `branch-name`      | The branch name of the created Pull Request           |

## Usage

### Complete Workflow Examples

#### Example 1: Auto-increment version and create PR (default behavior)
```yaml
name: Bump Version
on:
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  bump-version:
    runs-on: ubuntu-latest
    steps:
      - name: Bump version
        id: bump-version
        uses: SonarSource/release-github-actions/bump-version
        # Will auto-increment minor version and create a PR
```

#### Example 2: Set specific version with labels
```yaml
name: Bump to Specific Version
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to bump to'
        required: true
        type: string

permissions:
  contents: write
  pull-requests: write

jobs:
  bump-version:
    runs-on: ubuntu-latest
    steps:
      - name: Bump to specific version
        id: bump-version
        uses: SonarSource/release-github-actions/bump-version
        with:
          version: ${{ inputs.version }}
          pull-request-labels: "version-bump,automated"
```

#### Example 3: Only calculate next version without creating PR
```yaml
name: Get Next Version
on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  get-version:
    runs-on: ubuntu-latest
    steps:
      - name: Get next version
        id: bump-version
        uses: SonarSource/release-github-actions/bump-version
        with:
          create-pull-request: "false"
      
      - name: Display version info
        run: |
          echo "Current version: ${{ steps.bump-version.outputs.current-version }}"
          echo "Next version: ${{ steps.bump-version.outputs.next-version }}"
```

#### Example 4: Maven project with custom exclusions
```yaml
name: Bump Maven Version
on:
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  bump-maven-version:
    runs-on: ubuntu-latest
    steps:
      - name: Bump Maven version
        id: bump-version
        uses: SonarSource/release-github-actions/bump-version
        with:
          build-system: "maven"
          maven-exclude-paths: "./test/* ./examples/* ./e2e/*"
```

### Step-only Examples (for use within existing workflows)

#### Auto-increment version and create PR
```yaml
- name: Bump version
  id: bump-version
  uses: SonarSource/release-github-actions/bump-version
  # Will auto-increment minor version and create a PR
```

#### Set specific version
```yaml
- name: Bump to specific version
  id: bump-version
  uses: SonarSource/release-github-actions/bump-version
  with:
    version: "2.5.0"
```

#### Only calculate next version without creating PR
```yaml
- name: Get next version
  id: bump-version
  uses: SonarSource/release-github-actions/bump-version
  with:
    create-pull-request: "false"
```

#### Using outputs
```yaml
- name: Use version outputs
  run: |
    echo "Current version: ${{ steps.bump-version.outputs.current-version }}"
    echo "Next version: ${{ steps.bump-version.outputs.next-version }}"
    echo "PR URL: ${{ steps.bump-version.outputs.pull-request-url }}"
    echo "Branch: ${{ steps.bump-version.outputs.branch-name }}"
```

## Features

- **Flexible version input**: Use a specific version or auto-increment the minor version
- **Multi-build system support**: Works with both Gradle and Maven projects
- **Configurable file exclusions**: Customize which Maven pom.xml files to exclude from updates
- **Automatic file updates**: Updates `gradle.properties` or `pom.xml` files with new snapshot versions
- **Pull Request creation**: Optionally creates a PR with version changes for review
- **Smart version extraction**: Automatically finds and parses version from build files
- **Comprehensive outputs**: Returns current version, next version, and PR details

## Version Logic

### Auto-increment behavior
When no `version` input is provided:
- Extracts current version from build file (e.g., `1.2.3-SNAPSHOT` → `1.2.3`)
- Increments minor version and resets patch to 0 (e.g., `1.2.3` → `1.3.0`)
- Creates snapshot version for development (e.g., `1.3.0-SNAPSHOT`)

### Manual version setting
When `version` input is provided:
- Uses the specified version as the next version
- Creates snapshot version for development (e.g., `2.5.0` → `2.5.0-SNAPSHOT`)

## File Updates

### Gradle projects
- Updates `version=` property in `gradle.properties`

### Maven projects
- Updates `<version>` tags in all `pom.xml` files
- Excludes files based on `maven-exclude-paths` input (default: `./e2e/projects/*` and `./e2e/benchmarks/*`)
- Allows customization of excluded paths for different project structures

## Maven Exclusion Configuration

The `maven-exclude-paths` input allows you to specify which directories should be excluded when updating Maven pom.xml files:

- **Default exclusions**: `./e2e/projects/* ./e2e/benchmarks/*`
- **Custom exclusions**: Provide a space-separated list of paths (e.g., `"./test/* ./examples/* ./demos/*"`)
- **No exclusions**: Use an empty string `""` to update all pom.xml files

## Pull Request Details

When `create-pull-request` is `true`, the action:
- Creates a branch named `bot/prepare-next-development-iteration-{version}`
- Sets commit message and PR title to "Prepare next development iteration {version}"
- Targets the `master` branch
- Assigns the triggering user as reviewer
- Applies any specified labels

## Error Handling

The action will fail if:
- No version can be extracted from the build file
- The build file doesn't exist or is malformed
- File update operations fail
