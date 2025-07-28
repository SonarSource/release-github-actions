#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script finds SQS and SC integration tickets linked to a given release ticket,
optionally updates the SQS ticket's fix versions, and returns both keys.
"""

import argparse
import os
import sys
from jira import JIRA
from jira.exceptions import JIRAError

JIRA_SANDBOX_URL = "https://sonarsource-sandbox-608.atlassian.net/"
JIRA_PROD_URL = "https://sonarsource.atlassian.net/"
SQS_PROJECT_KEY = "SONAR"
SC_PROJECT_KEY = "SC"


def eprint(*args, **kwargs):
    """Prints messages to the standard error stream."""
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
        return jira_client
    except JIRAError as e:
        eprint(f"Error: JIRA authentication failed. Status: {e.status_code}, Response: {e.text}")
        sys.exit(1)


def find_linked_ticket(release_issue, target_project_key):
    """Finds a linked ticket from a specific project."""
    eprint(f"Searching for linked ticket in project '{target_project_key}'...")

    linked_tickets = []
    for link in release_issue.fields.issuelinks:
        linked_issue = getattr(link, 'outwardIssue', getattr(link, 'inwardIssue', None))
        if linked_issue and linked_issue.key.startswith(f"{target_project_key}-"):
            linked_tickets.append(linked_issue.key)

    if len(linked_tickets) == 0:
        eprint(f"Error: No linked ticket found in project '{target_project_key}' for ticket '{release_issue.key}'.")
        sys.exit(1)

    if len(linked_tickets) > 1:
        eprint(
            f"Error: Found multiple linked tickets in project '{target_project_key}': {', '.join(linked_tickets)}. Please ensure only one is linked.")
        sys.exit(1)

    found_key = linked_tickets[0]
    eprint(f"✅ Found linked ticket: {found_key}")
    return found_key


def update_sqs_fix_versions(jira, ticket_key, fix_versions_str):
    """Attempts to update the fixVersions of the SQS ticket."""
    if not fix_versions_str:
        return

    eprint(f"Attempting to set fix versions for SQS ticket {ticket_key} to: '{fix_versions_str}'")
    versions_list = [{'name': v.strip()} for v in fix_versions_str.split(',')]

    try:
        issue = jira.issue(ticket_key)
        issue.update(fields={'fixVersions': versions_list})
        eprint("✅ Successfully updated fix versions for SQS ticket.")
    except JIRAError as e:
        eprint(
            f"##[warning]Could not update fix versions for {ticket_key}. Jira API failed with status {e.status_code}: {e.text}")


def main():
    parser = argparse.ArgumentParser(description="Finds linked Jira tickets and optionally updates one.")
    parser.add_argument("--release-ticket-key", required=True, help="The key of the release ticket.")
    parser.add_argument("--sqs-fix-versions", help="Comma-separated list of fix versions for the SQS ticket.")
    parser.add_argument('--use-sandbox', action='store_true', help="Use the sandbox Jira server.")

    args = parser.parse_args()

    jira = get_jira_instance(args.use_sandbox)

    try:
        eprint(f"Fetching release ticket '{args.release_ticket_key}' to find linked issues...")
        release_issue = jira.issue(args.release_ticket_key, fields='issuelinks')
    except JIRAError as e:
        eprint(
            f"Error: Could not retrieve issue '{args.release_ticket_key}'. Status: {e.status_code}, Response: {e.text}")
        sys.exit(1)

    sqs_ticket_key = find_linked_ticket(release_issue, SQS_PROJECT_KEY)
    sc_ticket_key = find_linked_ticket(release_issue, SC_PROJECT_KEY)

    update_sqs_fix_versions(jira, sqs_ticket_key, args.sqs_fix_versions)

    # Output for the GitHub Action
    print(f"sqs_ticket_key={sqs_ticket_key}")
    print(f"sc_ticket_key={sc_ticket_key}")


if __name__ == "__main__":
    main()
