# release-github-actions

A centralized collection of reusable GitHub Actions designed to streamline and automate every stage of the analyzer release process. This repository serves as a versatile toolbox, offering modular automations to eliminate manual, repetitive steps and reduce friction across squads managing analyzer projects. Whether standardizing changelog generation, automating version bumps, handling release publishing, or coordinating cross-repository tasks, these actions help teams back away from cumbersome workflows and focus more on code quality. Pick and combine the automations best suited for your analyzer’s unique release requirements, and easily extend the toolbox to cover new scenarios as they arise.

## Available Actions

* [**Create Jira Release Ticket**](create-jira-release-ticket/README.md): Automates the creation of an "Ask for release" ticket in Jira.
* [**Check Releasability Status**](check-releasability-status/README.md): Checks the releasability status and extracts the version if successful.
* [**Update Release ticket Status**](update-release-ticket-status/README.md): Updates the status of a Jira release ticket and can change its assignee.
* [**Publish GitHub Release**](publish-github-release/README.md): Publishes a GitHub Release with notes fetched from Jira or provided directly.
* [**Release Jira Version**](release-jira-version/README.md): Releases a Jira version and creates the next one.
* [**Update integration tickets**](update-integration-tickets/README.md): Finds and optionally updates SQS and SC integration tickets.
* [**Update Analyzer**](update-analyzer/README.md): Updates an analyzer version in SonarQube or SonarCloud and creates a pull request.
