#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script fetches issues associated with a specific Jira release version
and formats them into Markdown for use in GitHub Release notes.
"""

import argparse
import os
import sys
from collections import defaultdict
from jira import JIRA
from jira.exceptions import JIRAError

JIRA_SANDBOX_URL = "https://sonarsource-sandbox-608.atlassian.net/"
JIRA_PROD_URL = "https://sonarsource.atlassian.net/"

def eprint(*args, **kwargs):
    """Prints messages to stderr to avoid polluting stdout, which is used for the script's output."""
    print(*args, file=sys.stderr, **kwargs)


# noinspection DuplicatedCode
def get_jira_instance(use_sandbox=False):
    """Initializes and returns a JIRA client instance."""
    jira_user = os.environ.get('JIRA_USER')
    jira_token = os.environ.get('JIRA_TOKEN')

    if not jira_user or not jira_token:
        eprint("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.")
        sys.exit(1)

    jira_url = JIRA_SANDBOX_URL if use_sandbox else JIRA_PROD_URL
    eprint(f"Connecting to JIRA server at: {jira_url}")

    try:
        jira_client = JIRA(jira_url, basic_auth=(jira_user, jira_token))
        jira_client.server_info()
        eprint("JIRA authentication successful.")
        return jira_client, jira_url
    except JIRAError as e:
        eprint(f"Error: JIRA authentication failed. Status: {e.status_code}")
        eprint(f"Response text: {e.text}")
        sys.exit(1)
    except Exception as e:
        eprint(f"An unexpected error occurred during JIRA connection: {e}")
        sys.exit(1)

def get_project_name(jira_client, project_key):
    """Fetches the full project name from its key."""
    try:
        project = jira_client.project(project_key)
        eprint(f"Found project name: '{project.name}' for key '{project_key}'.")
        return project.name
    except JIRAError as e:
        eprint(f"Error: Could not fetch project details for key '{project_key}'. Status: {e.status_code}")
        sys.exit(1)


def get_issues_for_release(jira_client, project_key, release_name):
    """Fetches all issues for a given 'fixVersion'."""
    eprint(f"Searching for issues in project '{project_key}' with fixVersion '{release_name}'...")
    jql_query = f'project = "{project_key}" AND fixVersion = "{release_name}" ORDER BY issuetype ASC, key ASC'
    try:
        issues = jira_client.search_issues(jql_query, maxResults=False) # maxResults=False to get all issues
        eprint(f"Found {len(issues)} issues for release '{release_name}'.")
        return issues
    except JIRAError as e:
        eprint(f"Error searching for issues. Status: {e.status_code}")
        eprint(f"JQL Query: {jql_query}")
        eprint(f"Response text: {e.text}")
        sys.exit(1)

def format_notes_as_markdown(issues, jira_url, project_name, version, category_order):
    """Formats a list of Jira issues into a categorized Markdown string matching Jira's export."""
    if not issues:
        return f"# Release notes - {project_name} - {version}\n\nNo issues found for this release."

    categorized_issues = defaultdict(list)
    for issue in issues:
        issue_type = issue.fields.issuetype.name
        categorized_issues[issue_type].append(issue)

    markdown_lines = [f"# Release notes - {project_name} - {version}\n"]

    for category_name in category_order:
        if category_name in categorized_issues:
            markdown_lines.append(f"### {category_name}")
            for issue in categorized_issues[category_name]:
                issue_link = f"{jira_url.rstrip('/')}/browse/{issue.key}"
                line = f"[{issue.key}]({issue_link}) {issue.fields.summary}"
                markdown_lines.append(line)
            markdown_lines.append("")

    return "\n".join(markdown_lines)

def main():
    """Main function to orchestrate fetching and formatting notes."""
    parser = argparse.ArgumentParser(
        description="Fetch Jira release notes and format as Markdown.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--project-key", required=True, help="The Jira project key (e.g., PROJ).")
    parser.add_argument("--release-name", required=True, help="The name of the 'fixVersion' in Jira. This will also be used as the version in the title.")
    parser.add_argument("--issue-types", default="", help="Optional comma-separated list of issue types to include, in order.")
    parser.add_argument('--use-sandbox', action='store_true', help="Use the sandbox Jira server.")
    args = parser.parse_args()

    if args.issue_types:
        category_order = [item.strip() for item in args.issue_types.split(',')]
        eprint(f"Using custom issue type order: {category_order}")
    else:
        category_order = [
            "New Feature",
            "False Positive",
            "False Negative",
            "Bug",
            "Improvement"
        ]
        eprint(f"Using default issue type order: {category_order}")

    jira, jira_url = get_jira_instance(args.use_sandbox)

    project_name = get_project_name(jira, args.project_key)
    issues = get_issues_for_release(jira, args.project_key, args.release_name)
    markdown_notes = format_notes_as_markdown(issues, jira_url, project_name, args.release_name, category_order)

    print(markdown_notes)

if __name__ == "__main__":
    main()
