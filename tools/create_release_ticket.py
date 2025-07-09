#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script automates the creation of an 'Ask for release' ticket in Jira.

It fetches the latest unreleased version for a specified Jira project,
and then creates a new release ticket with the provided details.

The script is designed to be run from a command line and is suitable for
integration into CI/CD pipelines like GitHub Actions.
"""

import argparse
import sys
from collections import namedtuple
from jira.exceptions import JIRAError
from jira_utils import get_jira_instance

# A dictionary mapping human-readable field names to Jira's custom field IDs.
CUSTOM_FIELDS = {
    'SHORT_DESCRIPTION': 'customfield_10146',
    'TARGETED_PRODUCT': 'customfield_10163',
    'SQ_COMPATIBILITY': 'customfield_10148',
    'LINK_TO_RELEASE_NOTES': 'customfield_10145',
    'DOCUMENTATION_STATUS': 'customfield_10147',
    'RULE_PROPS_CHANGED': 'customfield_11263',
}


def get_jira_release_notes_info(jira_client, project_key, jira_server_url):
    """
    Finds the latest unreleased version for a given project.

    Args:
        jira_client (JIRA): The authenticated JIRA client.
        project_key (str): The key of the project to search within (e.g., 'SONARIAC').
        jira_server_url (str): The base URL of the Jira server.

    Returns:
        namedtuple: A named tuple 'ReleaseNotes' with 'name' and 'url' of the latest
                    unreleased version.

    Raises:
        SystemExit: If the project is not found or no unreleased versions exist.
    """
    print(f"\nFetching versions for project '{project_key}'...")
    try:
        versions = jira_client.project_versions(project_key)
    except JIRAError as e:
        if e.status_code == 404:
            print(f"Error: Project with key '{project_key}' not found.", file=sys.stderr)
        else:
            print(f"Error: Failed to fetch versions for project '{project_key}'. Status: {e.status_code}",
                  file=sys.stderr)
        sys.exit(1)

    unreleased_versions = [v for v in versions if not v.released]

    if not unreleased_versions:
        print(f"Error: No unreleased versions found for project '{project_key}'.", file=sys.stderr)
        print("Please ensure there is at least one unreleased version in Jira.", file=sys.stderr)
        sys.exit(1)

    # Sort by version ID to find the most recently created one
    latest_unreleased_version = sorted(
        unreleased_versions,
        key=lambda v: int(v.id),
        reverse=True
    )[0]

    version_link = (
        f"{jira_server_url}/projects/{project_key}/"
        f"versions/{latest_unreleased_version.id}/tab/release-report-all-issues"
    )

    ReleaseNotes = namedtuple("ReleaseNotes", "name url")
    info = ReleaseNotes(latest_unreleased_version.name, version_link)

    print(f"🚀 Latest UNRELEASED version found: {info.name}")
    print(f"   🔗 Direct Link: {info.url}")

    return info


def create_release_ticket(jira_client, args, link_to_release_notes):
    """
    Creates the 'Ask for release' ticket in Jira.

    Args:
        jira_client (JIRA): The authenticated JIRA client.
        args (argparse.Namespace): The parsed command-line arguments.
        link_to_release_notes (str): The URL to the release notes report.

    Returns:
        jira.Issue: The newly created Jira issue object.

    Raises:
        SystemExit: If the ticket creation fails.
    """
    print("\nPreparing to create release ticket...")
    ticket_details = {
        'project': 'REL',
        'issuetype': 'Ask for release',
        'summary': f'{args.project_name} {args.new_version}',
        CUSTOM_FIELDS['SHORT_DESCRIPTION']: args.short_description,
        CUSTOM_FIELDS['TARGETED_PRODUCT']: {'value': args.targeted_product},
        CUSTOM_FIELDS['SQ_COMPATIBILITY']: args.sq_compatibility,
        CUSTOM_FIELDS['LINK_TO_RELEASE_NOTES']: link_to_release_notes,
        CUSTOM_FIELDS['DOCUMENTATION_STATUS']: args.documentation_status,
        CUSTOM_FIELDS['RULE_PROPS_CHANGED']: {'value': args.rule_props_changed}
    }

    try:
        new_ticket = jira_client.create_issue(fields=ticket_details)
        return new_ticket
    except JIRAError as e:
        print(f"Error: Failed to create Jira ticket. Status: {e.status_code}", file=sys.stderr)
        print(f"Response text: {e.response.text}", file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main function to parse arguments and orchestrate the ticket creation process.
    """
    parser = argparse.ArgumentParser(
        description="Create a 'Ask for release' Jira ticket.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Mandatory arguments
    parser.add_argument("--project-key", required=True, help="The key of the project (e.g., SONARIAC).")
    parser.add_argument("--project-name", required=True, help="The display name of the project (e.g., SonarIaC).")
    parser.add_argument("--new-version", required=True, help="The new version being released (e.g., 11.44.2).")
    parser.add_argument("--short-description", required=True, help="A short description for the release.")
    parser.add_argument("--targeted-product", required=True, help="The targeted product version (e.g., 11.0).")
    parser.add_argument("--sq-compatibility", required=True, help="SonarQube compatibility version (e.g., 2025.3).")

    # Optional arguments
    parser.add_argument('--use-sandbox', default=True, help="Use the sandbox server instead of the production Jira.")
    parser.add_argument("--documentation-status", default="N/A", help="Status of the documentation.")
    parser.add_argument("--rule-props-changed", default="No", choices=['Yes', 'No'],
                        help="Whether rule properties have changed.")

    args = parser.parse_args()

    jira, jira_server_url = get_jira_instance(args.use_sandbox)

    release_notes_info = get_jira_release_notes_info(jira, args.project_key, jira_server_url)
    ticket = create_release_ticket(jira, args, release_notes_info.url)

    print("\n" + "=" * 50)
    print("🎉 Successfully created release ticket!")
    print(f"   Ticket Key: {ticket.key}")
    print(f"   Ticket URL: {ticket.permalink()}")
    print("=" * 50)

    print(f"::set-output name=ticket-key::{ticket.key}")

if __name__ == "__main__":
    main()
