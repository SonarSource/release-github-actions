# release-github-actions

A centralized collection of reusable GitHub Actions designed to streamline and automate every stage of the analyzer release process. This repository serves as a versatile toolbox, offering modular automations to eliminate manual, repetitive steps and reduce friction across squads managing analyzer projects. Whether standardizing changelog generation, automating version bumps, handling release publishing, or coordinating cross-repository tasks, these actions help teams back away from cumbersome workflows and focus more on code quality. Pick and combine the automations best suited for your analyzer’s unique release requirements, and easily extend the toolbox to cover new scenarios as they arise.

## Available Actions

* [**Check Releasability Status**](check-releasability-status/README.md): Checks the releasability status and extracts the version if successful.
* [**Create Integration Ticket**](create-integration-ticket/README.md): Creates a Jira integration ticket with a custom summary and links it to another existing ticket.
* [**Create Jira Release Ticket**](create-jira-release-ticket/README.md): Automates the creation of an "Ask for release" ticket in Jira.
* [**Create Jira Version**](create-jira-version/README.md): Creates a new version in a Jira project, with the ability to automatically determine the next version number.
* [**Get Jira Release Notes**](get-jira-release-notes/README.md): Fetches Jira release notes and generates the release notes URL for a given project and version.
* [**Get Jira Version**](get-jira-version/README.md): Extracts a Jira-compatible version number from a release version by formatting it appropriately for Jira.
* [**Get Release Version**](get-release-version/README.md): Extracts the release version from the repox status on a specified branch.
* [**Notify Slack on Failure**](notify-slack/README.md): Sends a Slack notification when a job fails.
* [**Publish GitHub Release**](publish-github-release/README.md): Publishes a GitHub Release with notes fetched from Jira or provided directly.
* [**Release Jira Version**](release-jira-version/README.md): Releases a Jira version and creates the next one.
* [**Update Analyzer**](update-analyzer/README.md): Updates an analyzer version in SonarQube or SonarCloud and creates a pull request.
* [**Update Release Ticket Status**](update-release-ticket-status/README.md): Updates the status of a Jira release ticket and can change its assignee.
* [**Update Rule Metadata**](update-rule-metadata/README.md): Automates updating rule metadata across all supported languages using the rule-api tooling.
* [**Automated Release Workflow**](docs/AUTOMATED_RELEASE.md): Orchestrates the end-to-end release across Jira and GitHub, with optional integration tickets and analyzer PRs.

## Development

### Update Action Versions Workflow

The repository includes an `update-action-versions` workflow that creates a pull request to update all internal action references to use a specific commit or the latest version from the master branch. This workflow scans all `action.yml` files in the repository and updates any references to `SonarSource/release-github-actions` actions to point to the specified reference, ensuring consistency across all actions when updates are made to shared components.
