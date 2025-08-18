#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script creates a Jira integration ticket with a custom summary
and links it to another existing ticket.
"""

import argparse
import os
import sys
from jira import JIRA
from jira.exceptions import JIRAError


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


def get_jira_instance(jira_url):
    """
    Initializes and returns a JIRA client instance and the server URL.
    """
    jira_user = os.environ.get('JIRA_USER')
    jira_token = os.environ.get('JIRA_TOKEN')

    if not jira_user or not jira_token:
        eprint("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.")
        sys.exit(1)

    eprint(f"Connecting to JIRA server at: {jira_url}")
    eprint(f"Authenticating with user: {jira_user}")

    try:
        jira_client = JIRA(jira_url, basic_auth=(jira_user, jira_token), get_server_info=True)
        eprint("JIRA authentication successful.")
        return jira_client
    except JIRAError as e:
        eprint(f"Error: JIRA authentication failed. Status: {e.status_code}")
        eprint("Please check your JIRA URL, user, and token.")
        eprint(f"Response text: {e.text}")
        sys.exit(1)
    except Exception as e:
        eprint(f"An unexpected error occurred during JIRA connection: {e}")
        sys.exit(1)


def validate_linked_ticket(jira_client, linked_ticket_key):
    """
    Validates that the linked ticket exists and is accessible.
    """
    eprint(f"Validating linked ticket: {linked_ticket_key}")
    try:
        linked_ticket = jira_client.issue(linked_ticket_key)
        eprint(f"Successfully found linked ticket: {linked_ticket.key} - {linked_ticket.fields.summary}")
        return linked_ticket
    except JIRAError as e:
        if e.status_code == 404:
            eprint(f"Error: Ticket '{linked_ticket_key}' not found.")
        else:
            eprint(f"Error: Failed to access ticket '{linked_ticket_key}'. Status: {e.status_code}")
            eprint(f"Response text: {e.text}")
        sys.exit(1)
    except Exception as e:
        eprint(f"An unexpected error occurred while validating linked ticket: {e}")
        sys.exit(1)


def create_integration_ticket(jira_client, args):
    """
    Creates the integration ticket in Jira.
    """
    eprint(f"\nPreparing to create integration ticket in project '{args.jira_project_key}'...")

    # Get the default issue type for the project (usually Task or Story)
    try:
        project = jira_client.project(args.jira_project_key)
        issue_types = jira_client.createmeta(projectKeys=project.id)['projects'][0]['issuetypes']

        # Try to find a suitable issue type (prefer Task, then Story, then first available)
        issue_type = None
        for it in issue_types:
            if it['name'].lower() in ['task', 'story']:
                issue_type = it['name']
                break

        if not issue_type and issue_types:
            issue_type = issue_types[0]['name']

        if not issue_type:
            eprint(f"Error: No available issue types found for project '{args.jira_project_key}'")
            sys.exit(1)

        eprint(f"Using issue type: {issue_type}")

    except JIRAError as e:
        eprint(f"Error: Failed to access project '{args.jira_project_key}'. Status: {e.status_code}")
        eprint(f"Response text: {e.text}")
        sys.exit(1)

    ticket_details = {
        'project': args.jira_project_key,
        'issuetype': {'name': issue_type},
        'summary': args.ticket_summary,
    }

    # Add description if provided
    if args.ticket_description:
        ticket_details['description'] = args.ticket_description

    try:
        new_ticket = jira_client.create_issue(fields=ticket_details)
        eprint(f"Successfully created ticket: {new_ticket.key}")
        return new_ticket
    except JIRAError as e:
        eprint(f"Error: Failed to create Jira ticket. Status: {e.status_code}")
        eprint(f"Response text: {e.response.text}")
        sys.exit(1)


def link_tickets(jira_client, integration_ticket, linked_ticket, link_type):
    """
    Creates a link between the integration ticket and the specified linked ticket.
    """
    eprint(f"\nLinking tickets: {integration_ticket.key} -> {linked_ticket.key}")
    eprint(f"Link type: {link_type}")

    try:
        jira_client.create_issue_link(
            type=link_type,
            inwardIssue=integration_ticket.key,
            outwardIssue=linked_ticket.key
        )
        eprint(f"Successfully linked {integration_ticket.key} to {linked_ticket.key}")
    except JIRAError as e:
        eprint(f"Error: Failed to link tickets. Status: {e.status_code}")
        eprint(f"Response text: {e.text}")
        # Don't exit here - the ticket was created successfully, linking is secondary
        eprint("Warning: Ticket was created but linking failed.")
    except Exception as e:
        eprint(f"An unexpected error occurred while linking tickets: {e}")
        eprint("Warning: Ticket was created but linking failed.")


def main():
    """
    Main function to parse arguments and orchestrate the ticket creation process.
    """
    parser = argparse.ArgumentParser(
        description="Create a Jira integration ticket and link it to another ticket.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--ticket-summary", required=False,
                       help="The summary/title for the integration ticket.")
    parser.add_argument("--project-name", required=False,
                       help="The name of the project (used to generate ticket summary if ticket-summary is not provided).")
    parser.add_argument("--release-version", required=False,
                       help="The release version (used to generate ticket summary if ticket-summary is not provided).")
    parser.add_argument("--linked-ticket-key", required=True,
                       help="The key of the ticket to link to (e.g., REL-123).")
    parser.add_argument("--jira-project-key", required=True,
                       help="The key of the project where the ticket will be created (e.g., SQS).")
    parser.add_argument("--jira-url", required=True,
                        help="The Jira server URL to connect to.")
    parser.add_argument("--ticket-description", default="",
                       help="The description for the integration ticket.")
    parser.add_argument("--link-type", default="relates to",
                       help="The type of link to create (e.g., 'relates to', 'depends on').")

    args = parser.parse_args()

    # Validate and construct ticket summary
    if not args.ticket_summary:
        if not args.project_name or not args.release_version:
            eprint("Error: Either --ticket-summary must be provided, or both --project-name and --release-version must be provided.")
            sys.exit(1)
        args.ticket_summary = f"Integration for {args.project_name} {args.release_version}"
        eprint(f"Generated ticket summary: {args.ticket_summary}")

    # Initialize Jira client
    jira = get_jira_instance(args.jira_url)

    # Validate the linked ticket exists
    linked_ticket = validate_linked_ticket(jira, args.linked_ticket_key)

    # Create the integration ticket
    integration_ticket = create_integration_ticket(jira, args)

    # Link the tickets
    link_tickets(jira, integration_ticket, linked_ticket, args.link_type)

    # Output results
    eprint("\n" + "=" * 50)
    eprint("🎉 Successfully created integration ticket!")
    eprint(f"   Ticket Key: {integration_ticket.key}")
    eprint(f"   Ticket URL: {integration_ticket.permalink()}")
    eprint(f"   Linked to: {linked_ticket.key}")
    eprint("=" * 50)

    # Output for GitHub Actions (captured by stdout)
    print(f"ticket_key={integration_ticket.key}")
    print(f"ticket_url={integration_ticket.permalink()}")


if __name__ == "__main__":
    main()
