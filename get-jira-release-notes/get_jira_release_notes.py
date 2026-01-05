#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script fetches Jira release notes and generates the release notes URL 
for a given project and version.
"""

import argparse
import os
import sys
from collections import defaultdict
from jira import JIRA
from jira.exceptions import JIRAError


# noinspection DuplicatedCode
def eprint(*args, **kwargs):
    """Prints messages to stderr to avoid polluting stdout, which is used for the script's output."""
    print(*args, file=sys.stderr, **kwargs)


def get_jira_instance(jira_url):
    """Initializes and returns a JIRA client instance."""
    jira_user = os.environ.get('JIRA_USER')
    jira_token = os.environ.get('JIRA_TOKEN')

    if not jira_user or not jira_token:
        eprint("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.")
        sys.exit(1)

    eprint(f"Connecting to JIRA server at: {jira_url}")

    try:
        jira_client = JIRA(jira_url, basic_auth=(jira_user, jira_token))
        jira_client.server_info()
        eprint("JIRA authentication successful.")
        return jira_client
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


def get_version_id(jira_client, project_key, version_name):
    """Fetches the version ID for the given version name in the project."""
    eprint(f"Fetching version ID for '{version_name}' in project '{project_key}'...")
    try:
        versions = jira_client.project_versions(project_key)
        for version in versions:
            if version.name == version_name:
                eprint(f"Found version ID: {version.id} for version '{version_name}'.")
                return version.id
        
        eprint(f"Error: Version '{version_name}' not found in project '{project_key}'.")
        sys.exit(1)
    except JIRAError as e:
        if e.status_code == 404:
            eprint(f"Error: Project with key '{project_key}' not found.")
        else:
            eprint(f"Error: Failed to fetch versions for project '{project_key}'. Status: {e.status_code}")
        sys.exit(1)


# noinspection DuplicatedCode
def get_issues_for_release(jira_client, project_key, release_name):
    """Fetches all issues for a given 'fixVersion'."""
    eprint(f"Searching for issues in project '{project_key}' with fixVersion '{release_name}'...")
    jql_query = f'project = "{project_key}" AND fixVersion = "{release_name}" ORDER BY issuetype ASC, key ASC'
    try:
        issues = jira_client.search_issues(jql_query, maxResults=False)  # maxResults=False to get all issues
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


def format_notes_as_jira_markup(issues, jira_url, project_name, version, category_order):
    """Formats a list of Jira issues into a categorized Jira wiki markup string."""
    if not issues:
        return f"h1. Release notes - {project_name} - {version}\n\nNo issues found for this release."

    categorized_issues = defaultdict(list)
    for issue in issues:
        issue_type = issue.fields.issuetype.name
        categorized_issues[issue_type].append(issue)

    jira_lines = [f"h1. Release notes - {project_name} - {version}\n"]

    for category_name in category_order:
        if category_name in categorized_issues:
            jira_lines.append(f"h3. {category_name}")
            for issue in categorized_issues[category_name]:
                issue_link = f"{jira_url.rstrip('/')}/browse/{issue.key}"
                line = f"[{issue.key}|{issue_link}] {issue.fields.summary}"
                jira_lines.append(line)
            jira_lines.append("")

    return "\n".join(jira_lines)


def generate_release_notes_url(jira_url, project_key, version_id):
    """Generates the release notes URL using the same logic as create_release_ticket.py."""
    return f"{jira_url.rstrip('/')}/projects/{project_key}/versions/{version_id}/tab/release-report-all-issues"


def generate_release_issue_filter_url(jira_url, version_id):
    """Generates the issue filter URL for the release version."""
    return f"{jira_url.rstrip('/')}/issues/?jql=fixVersion%3D{version_id}"


def main():
    """Main function to orchestrate fetching and formatting notes."""
    parser = argparse.ArgumentParser(
        description="Fetch Jira release notes and generate release notes URL.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--project-key", required=True, help="The Jira project key (e.g., PROJ).")
    parser.add_argument("--version-name", required=True,
                        help="The name of the 'fixVersion' in Jira. This will also be used as the version in the title.")
    parser.add_argument("--issue-types", default="",
                        help="Optional comma-separated list of issue types to include, in order.")
    parser.add_argument("--jira-url", required=True, help="The Jira server URL.")
    
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

    jira = get_jira_instance(args.jira_url)

    # Get version ID for URL generation
    version_id = get_version_id(jira, args.project_key, args.version_name)

    # Generate release notes URL and issue filter URL
    release_notes_url = generate_release_notes_url(args.jira_url, args.project_key, version_id)
    release_issue_filter_url = generate_release_issue_filter_url(args.jira_url, version_id)

    # Get project name and issues for both formats
    project_name = get_project_name(jira, args.project_key)
    issues = get_issues_for_release(jira, args.project_key, args.version_name)
    markdown_notes = format_notes_as_markdown(issues, args.jira_url, project_name, args.version_name, category_order)
    jira_markup_notes = format_notes_as_jira_markup(issues, args.jira_url, project_name, args.version_name, category_order)

    # Output results for GitHub Actions
    # Using multiline string format for the release notes
    print(f"jira-release-url={release_notes_url}")
    print(f"jira-release-issue-filter-url={release_issue_filter_url}")
    print(f"jira-release-id={version_id}")
    print("release-notes<<EOF")
    print(markdown_notes)
    print("EOF")
    print("jira-release-notes<<EOF")
    print(jira_markup_notes)
    print("EOF")


if __name__ == "__main__":
    main()
