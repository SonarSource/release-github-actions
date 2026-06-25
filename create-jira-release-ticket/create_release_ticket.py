#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script automates the creation of an 'Ask for release' ticket in Jira.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))
from jira_common import eprint, get_jira_instance, CUSTOM_FIELDS
from jira.exceptions import JIRAError


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
        CUSTOM_FIELDS['LINK_TO_RELEASE_NOTES']: link_to_release_notes,
        CUSTOM_FIELDS['DOCUMENTATION_STATUS']: args.documentation_status,
        CUSTOM_FIELDS['RULE_PROPS_CHANGED']: {'value': args.rule_props_changed},
        CUSTOM_FIELDS['SONARLINT_CHANGELOG']: args.sonarlint_changelog
    }

    if args.due_date:
        ticket_details['duedate'] = args.due_date

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
    parser.add_argument("--use-sandbox", default="false", help="Use Jira sandbox (true/false).")
    parser.add_argument("--documentation-status", default="N/A", help="Status of the documentation.")
    parser.add_argument("--rule-props-changed", default="No", choices=['Yes', 'No'],
                        help="Whether rule properties have changed.")
    parser.add_argument("--jira-release-url", default="", help="The URL to the Jira release notes page.")
    parser.add_argument("--sonarlint-changelog", default="", help="The SonarLint changelog content.")
    parser.add_argument("--due-date", default="", help="Due date of the release, for example '2029-12-24'.")

    args = parser.parse_args()

    jira = get_jira_instance(args.use_sandbox)

    eprint(f"Using release URL: {args.jira_release_url}")
    ticket = create_release_ticket(jira, args, args.jira_release_url)

    eprint("\n" + "=" * 50)
    eprint("🎉 Successfully created release ticket!")
    eprint(f"   Ticket Key: {ticket.key}")
    eprint(f"   Ticket URL: {ticket.permalink()}")
    eprint(f"   Release URL: {args.jira_release_url}")
    eprint("=" * 50)

    print(f"ticket_key={ticket.key}")
    print(f"ticket_url={ticket.permalink()}")


if __name__ == "__main__":
    main()
