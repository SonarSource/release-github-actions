#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script automates the creation of an 'Ask for release' ticket in Jira.
"""

import argparse
import os
import sys
from collections import namedtuple
from jira import JIRA
from jira.exceptions import JIRAError

JIRA_SANDBOX_URL = "https://sonarsource-sandbox-608.atlassian.net/"
JIRA_PROD_URL = "https://sonarsource.atlassian.net/"
CUSTOM_FIELDS = {
    'SHORT_DESCRIPTION': 'customfield_10146',
    'SQ_COMPATIBILITY': 'customfield_10148',
    'TARGETED_PRODUCT': 'customfield_10163',
    'LINK_TO_RELEASE_NOTES': 'customfield_10145',
    'DOCUMENTATION_STATUS': 'customfield_10147',
    'RULE_PROPS_CHANGED': 'customfield_11263',
    'SONARLINT_CHANGELOG': 'customfield_11264',
}


def eprint(*args, **kwargs):
    """
    Prints messages to the standard error stream (stderr).

    This function serves as a dedicated logger for informational messages,
    warnings, or errors. In a CI/CD pipeline, this ensures that diagnostic
    output is kept separate from the primary result of the script, which is
    written to standard output (stdout). This separation allows for cleaner
    data parsing and redirection.
    """
    print(*args, file=sys.stderr, **kwargs)


def get_jira_instance(use_sandbox=False):
    """
    Initializes and returns a JIRA client instance and the server URL used.
    """
    jira_user = os.environ.get('JIRA_USER')
    jira_token = os.environ.get('JIRA_TOKEN')

    if not jira_user or not jira_token:
        eprint("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.")
        sys.exit(1)

    jira_url = JIRA_SANDBOX_URL if use_sandbox else JIRA_PROD_URL

    eprint(f"Connecting to JIRA server at: {jira_url}")
    eprint(f"Authenticating with user: {jira_user}")

    try:
        jira_client = JIRA(jira_url, basic_auth=(jira_user, jira_token), get_server_info=True)
        eprint("JIRA authentication successful.")
        return jira_client, jira_url
    except JIRAError as e:
        eprint(f"Error: JIRA authentication failed. Status: {e.status_code}")
        eprint("Please check your JIRA URL, user, and token.")
        eprint(f"Response text: {e.text}")
        sys.exit(1)
    except Exception as e:
        eprint(f"An unexpected error occurred during JIRA connection: {e}")
        sys.exit(1)


def _get_specific_jira_release(project_key, jira_release_name, versions):
    """
    Finds and returns a specific, unreleased version by its name.
    """
    eprint(f"Searching for specified release version: '{jira_release_name}'...")
    found_versions = [v for v in versions if v.name == jira_release_name]
    if not found_versions:
        eprint(f"Error: Specified Jira release '{jira_release_name}' not found for project '{project_key}'.")
        sys.exit(1)

    target_version = found_versions[0]

    if target_version.released:
        eprint(f"Error: The specified version '{jira_release_name}' has already been released.")
        eprint("Please provide an unreleased version or omit the 'jira_release_name' parameter.")
        sys.exit(1)

    eprint(f"✅ Found specified unreleased version: {target_version.name}")

    return target_version


def _get_unreleased_version(project_key, versions):
    """
    Retrieves the single unreleased version from a list of project versions.
    """
    eprint("No specific release version provided. Searching for unreleased versions...")
    unreleased_versions = [v for v in versions if not v.released]

    if not unreleased_versions:
        eprint(f"Error: No unreleased versions found for project '{project_key}'.")
        eprint("Please ensure there is at least one unreleased version in Jira.")
        sys.exit(1)

    if len(unreleased_versions) > 1:
        eprint(f"Error: Multiple unreleased versions found for project '{project_key}'.")
        eprint("Please specify which version to release using the '--jira-release-name' argument.")
        eprint("Found versions:")
        for v in unreleased_versions:
            eprint(f"  - {v.name}")
        sys.exit(1)

    target_version = unreleased_versions[0]
    eprint(f"✅ Found a single unreleased version: {target_version.name}")

    return target_version


def get_jira_release_notes_info(jira_client, project_key, jira_server_url, jira_release_name=None):
    """
    Finds a specific or the single unreleased version for a given project.
    """
    eprint(f"\nFetching versions for project '{project_key}'...")
    try:
        versions = jira_client.project_versions(project_key)
    except JIRAError as e:
        if e.status_code == 404:
            eprint(f"Error: Project with key '{project_key}' not found.")
        else:
            eprint(f"Error: Failed to fetch versions for project '{project_key}'. Status: {e.status_code}")
        sys.exit(1)

    if jira_release_name:
        target_version = _get_specific_jira_release(project_key, jira_release_name, versions)
    else:
        target_version = _get_unreleased_version(project_key, versions)

    version_link = (
        f"{jira_server_url}/projects/{project_key}/"
        f"versions/{target_version.id}/tab/release-report-all-issues"
    )

    ReleaseNotes = namedtuple("ReleaseNotes", "name url")
    info = ReleaseNotes(target_version.name, version_link)
    eprint(f"   🔗 Direct Link: {info.url}")

    return info


def create_release_ticket(jira_client, args, link_to_release_notes):
    """
    Creates the 'Ask for release' ticket in Jira.
    """
    eprint("\nPreparing to create release ticket...")
    ticket_details = {
        'project': 'REL',
        'issuetype': 'Ask for release',
        'summary': f'{args.project_name} {args.version}',
        CUSTOM_FIELDS['SHORT_DESCRIPTION']: args.short_description,
        CUSTOM_FIELDS['SQ_COMPATIBILITY']: args.sq_compatibility,
        CUSTOM_FIELDS['LINK_TO_RELEASE_NOTES']: link_to_release_notes,
        CUSTOM_FIELDS['DOCUMENTATION_STATUS']: args.documentation_status,
        CUSTOM_FIELDS['RULE_PROPS_CHANGED']: {'value': args.rule_props_changed},
        CUSTOM_FIELDS['SONARLINT_CHANGELOG']: args.sonarlint_changelog
    }

    if args.targeted_product:
        ticket_details[CUSTOM_FIELDS['TARGETED_PRODUCT']] = {'value': args.targeted_product}

    try:
        new_ticket = jira_client.create_issue(fields=ticket_details)
        return new_ticket
    except JIRAError as e:
        eprint(f"Error: Failed to create Jira ticket. Status: {e.status_code}")
        eprint(f"Response text: {e.response.text}")
        sys.exit(1)


def main():
    """
    Main function to parse arguments and orchestrate the ticket creation process.
    """
    parser = argparse.ArgumentParser(
        description="Create a 'Ask for release' Jira ticket.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--project-key", required=True, help="The key of the project (e.g., SONARIAC).")
    parser.add_argument("--project-name", required=True, help="The display name of the project (e.g., SonarIaC).")
    parser.add_argument("--version", required=True, help="The version being released (e.g., 11.44.2).")
    parser.add_argument("--short-description", required=True, help="A short description for the release.")
    parser.add_argument("--sq-compatibility", required=True, help="SonarQube compatibility version (e.g., 2025.3).")
    parser.add_argument("--targeted-product", help="The targeted product version (e.g., 11.0).")
    parser.add_argument('--use-sandbox', action='store_true', help="Use the sandbox server instead of the production Jira.")
    parser.add_argument("--documentation-status", default="N/A", help="Status of the documentation.")
    parser.add_argument("--rule-props-changed", default="No", choices=['Yes', 'No'],
                        help="Whether rule properties have changed.")
    parser.add_argument("--jira-release-name", default="", help="The specific Jira release version to use.")
    parser.add_argument("--sonarlint-changelog", default="", help="The SonarLint changelog content.")

    args = parser.parse_args()

    jira, jira_server_url = get_jira_instance(args.use_sandbox)

    release_notes_info = get_jira_release_notes_info(jira, args.project_key, jira_server_url, args.jira_release_name)
    ticket = create_release_ticket(jira, args, release_notes_info.url)

    eprint("\n" + "=" * 50)
    eprint("🎉 Successfully created release ticket!")
    eprint(f"   Ticket Key: {ticket.key}")
    eprint(f"   Ticket URL: {ticket.permalink()}")
    eprint("=" * 50)

    print(ticket.key)


if __name__ == "__main__":
    main()
