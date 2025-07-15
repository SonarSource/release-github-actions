#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script automates the process of updating a Jira release ticket's status
and optionally reassigning it.
"""

import argparse
import os
import sys
from jira import JIRA
from jira.exceptions import JIRAError

# Jira server URLs
JIRA_SANDBOX_URL = "https://sonarsource-sandbox-608.atlassian.net/"
JIRA_PROD_URL = "https://sonarsource.atlassian.net/"


def eprint(*args, **kwargs):
    """
    Prints messages to the standard error stream (stderr) for logging purposes.
    This separates diagnostic output from the script's primary result.
    """
    print(*args, file=sys.stderr, **kwargs)


# noinspection DuplicatedCode
def get_jira_instance(use_sandbox=False):
    """
    Initializes and returns a JIRA client instance based on environment variables.

    Args:
        use_sandbox (bool): If True, connects to the sandbox Jira server.

    Returns:
        JIRA: An authenticated JIRA client instance.
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
        return jira_client
    except JIRAError as e:
        eprint(f"Error: JIRA authentication failed. Status: {e.status_code}")
        eprint(f"Response text: {e.text}")
        sys.exit(1)
    except Exception as e:
        eprint(f"An unexpected error occurred during JIRA connection: {e}")
        sys.exit(1)


def update_ticket_status(jira_client, ticket_key, new_status, assignee_email):
    """
    Updates the status of a Jira ticket and optionally assigns it to a new user.

    Args:
        jira_client (JIRA): The authenticated JIRA client.
        ticket_key (str): The key of the ticket to update (e.g., 'REL-1234').
        new_status (str): The target status for the ticket.
        assignee_email (str): The email of the user to assign the ticket to. Can be None.
    """
    try:
        eprint(f"Fetching ticket: {ticket_key}")
        issue = jira_client.issue(ticket_key)
    except JIRAError as e:
        if e.status_code == 404:
            eprint(f"Error: Ticket '{ticket_key}' not found.")
        else:
            eprint(f"Error: Failed to fetch ticket '{ticket_key}'. Status: {e.status_code}")
            eprint(f"Response text: {e.text}")
        sys.exit(1)

    if assignee_email:
        eprint(f"Attempting to assign ticket to: {assignee_email}")
        try:
            jira_client.assign_issue(ticket_key, assignee_email)
            eprint(f"Successfully assigned ticket to {assignee_email}")
        except JIRAError as e:
            eprint(f"Error: Failed to assign ticket to '{assignee_email}'. Status: {e.status_code}")
            eprint(f"Response text: {e.text}")
            eprint("Please ensure the user exists and has assignable permissions for this project.")
            sys.exit(1)

    try:
        jira_client.transition_issue(issue, new_status)
        eprint(f"Successfully transitioned ticket to '{new_status}'.")
    except JIRAError as e:
        eprint(f"Error: Failed to transition ticket to '{new_status}'. Status: {e.status_code}")
        eprint(f"Response text: {e.text}")
        eprint("Please ensure this is a valid transition from the ticket's current status.")
        sys.exit(1)


def main():
    """
    Main function to parse arguments and orchestrate the ticket update process.
    """
    parser = argparse.ArgumentParser(
        description="Update a Jira release ticket's status and assignee.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--ticket-key", required=True, help="The key of the Jira ticket to update (e.g., REL-1234).")
    parser.add_argument("--status", required=True, choices=['Start Progress', 'Technical Release Done'],
                        help="The target status for the ticket.")
    parser.add_argument("--assignee", required=False, default=None,
                        help="The email of the user to assign the ticket to.")
    parser.add_argument('--use-sandbox', action='store_true',
                        help="Use the sandbox server instead of the production Jira.")

    args = parser.parse_args()

    jira = get_jira_instance(args.use_sandbox)
    update_ticket_status(jira, args.ticket_key, args.status, args.assignee)

    eprint("\n" + "=" * 50)
    eprint("🎉 Successfully updated Jira ticket!")
    eprint(f"   Ticket Key: {args.ticket_key}")
    eprint(f"   New Status: {args.status}")
    if args.assignee:
        eprint(f"   Assignee: {args.assignee}")
    eprint("=" * 50)


if __name__ == "__main__":
    main()
