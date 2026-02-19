# Bump Project Version GitHub Action

This action updates the version in Maven and Gradle files across your repository. It supports excluding specific modules from the version bump.

## Inputs

| Name             | Description                                                      | Required | Default  |
|------------------|------------------------------------------------------------------|----------|----------|
| version          | The new version (without `-SNAPSHOT`)                            | Yes      |          |
| token            | The GitHub token for PR creation                                 | No       |          |
| excluded-modules | Comma-separated list of modules to exclude from version bumping  | No       |          |
| base-branch      | The base branch for the pull request                             | No       | `master` |
| pr-labels        | Comma-separated list of labels to add to the pull request        | No       |          |

## Outputs

| Name              | Description                           |
|-------------------|---------------------------------------|
| pull-request-url  | URL of the created pull request       |

## Usage

```yaml
- name: Bump version
  id: bump
  uses: SonarSource/release-github-actions/bump-version@v1
  with:
    version: '1.2.3'
    token: ${{ secrets.GITHUB_TOKEN }}
    excluded-modules: 'moduleA,moduleB'

- name: Show PR URL
  run: echo "PR URL: ${{ steps.bump.outputs.pull-request-url }}"
```

## How it works
- Updates all `pom.xml` and `gradle.properties` files to the new version.
- Skips files in modules listed in `excluded-modules`.
- Commits changes and creates a pull request.
