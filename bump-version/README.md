# Bump Project Version GitHub Action

This action updates the version in Maven and Gradle files across your repository. It supports excluding specific modules from the version bump.

## Inputs

| Name              | Description                                                      | Required | Default |
|-------------------|------------------------------------------------------------------|----------|------|
| version           | The new version (without `-SNAPSHOT`)                            | Yes      |      |
| exluded-modules   | Comma-separated list of modules to exclude from version bumping   | No       |      |

## Outputs

| Name              | Description                           |
|-------------------|---------------------------------------|
| pull-request-url  | URL of the created pull request       |

## Usage

```yaml
- name: Bump version
  id: bump
  uses: SonarSource/release-github-action/bump-version@v1
  with:
    version: '1.2.3'
    exluded-modules: 'moduleA,moduleB'

- name: Show PR URL
  run: echo "PR URL: ${{ steps.bump.outputs.pull-request-url }}"
```

## How it works
- Updates all `pom.xml` and `gradle.properties` files to the new version.
- Skips files in modules listed in `exluded-modules`.
- Commits changes and creates a pull request.
