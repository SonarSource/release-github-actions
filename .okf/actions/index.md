# Actions

* [bump-version](bump-version.md) - updates the version in Maven/Gradle files, opens a PR.
* [check-releasability-status](check-releasability-status.md) - verifies the Releasability commit status on a branch.
* [create-integration-ticket](create-integration-ticket.md) - creates a Jira integration ticket linked to a release ticket.
* [create-jira-release-ticket](create-jira-release-ticket.md) - creates the "Ask for release" ticket in Jira.
* [create-jira-version](create-jira-version.md) - creates a new version in a Jira project.
* [create-pull-request](create-pull-request.md) - shared PR-creation building block using the `gh` CLI.
* [get-jira-release-notes](get-jira-release-notes.md) - fetches and formats Jira release notes.
* [get-jira-version](get-jira-version.md) - converts a release version to Jira's version naming convention.
* [get-release-version](get-release-version.md) - extracts the release version from the repox commit status.
* [lock-branch](lock-branch.md) - locks/unlocks a branch via branch protection rules.
* [notify-failure](notify-failure.md) - rich Slack failure notification with root-cause extraction.
* [notify-slack](notify-slack.md) - minimal Slack failure notification.
* [publish-github-release](publish-github-release.md) - creates a GitHub release and triggers the downstream release workflow.
* [release-jira-version](release-jira-version.md) - marks a Jira version as released.
* [resolve-ktlo-epic](resolve-ktlo-epic.md) - finds the current KTLO epic in a Jira project.
* [slack-message](slack-message.md) - sends a markdown message to Slack.
* [sonar-update-center-release](sonar-update-center-release.md) - adds a release entry to sonar-update-center-properties.
* [update-analysis-as-a-service](update-analysis-as-a-service.md) - updates analyzer versions in sonar-analysis-as-a-service.
* [update-analyzer](update-analyzer.md) - updates an analyzer version in sonar-enterprise.
* [update-plugins-deployer](update-plugins-deployer.md) - updates a plugin version anchor in sonar-plugins-deployer.
* [update-release-ticket-status](update-release-ticket-status.md) - transitions a release ticket's status.
* [update-rule-metadata](update-rule-metadata.md) - refreshes rule metadata via the rule-api tooling.
