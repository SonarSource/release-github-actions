#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script creates a Jira integration ticket with a custom summary
and links it to another existing ticket.
"""

import argparse
import os
import re
import sys
import time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))
from jira_common import eprint, get_jira_instance, CUSTOM_FIELDS
from jira.exceptions import JIRAError

# Fix-version name prefixes per Edition; editions not listed (e.g. 'N/A') get none.
EDITION_VERSION_PREFIXES = {
    'Community Build': ('sqcb-',),
    'Server': ('sqs-',),
    'Community Build & Server': ('sqcb-', 'sqs-'),
}

SONAR_ENTERPRISE_TAGS_URL = 'https://api.github.com/repos/SonarSource/sonar-enterprise/git/matching-refs/tags/'

# Jira versions are 'major.minor' only (no bugfix or '-M1' suffix).
VERSION_NAME_PATTERN = re.compile(r'^(\d+)\.(\d+)$')


def version_sort_key(name):
    """Numeric sort key for 'major.minor', so '26.9' < '26.10'."""
    major, minor = VERSION_NAME_PATTERN.match(name).groups()
    return int(major), int(minor)


def sort_by_version(names, prefix):
    """Sorts 'prefix' + 'major.minor' names numerically, so 'sqcb-26.9' < 'sqcb-26.10'."""
    return sorted(names, key=lambda name: version_sort_key(name[len(prefix):]))


def find_lowest_version(versions, prefix):
    """Lowest 'prefix' + 'major.minor' version name, or None."""
    candidates = [
        v.name for v in versions
        if v.name.startswith(prefix) and VERSION_NAME_PATTERN.match(v.name[len(prefix):])
    ]
    if not candidates:
        eprint(f"No open '{prefix}*' version found.")
        return None
    candidates = sort_by_version(candidates, prefix)
    eprint(f"Found '{prefix}*' versions {candidates}, using '{candidates[0]}'.")
    return candidates[0]


def list_tag_refs(github_token, prefix):
    """sonar-enterprise tag refs starting with prefix; raises on HTTP errors and malformed payloads."""
    refs = []
    url, params = SONAR_ENTERPRISE_TAGS_URL + prefix, {'per_page': 100}
    while url:
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {github_token}', 'Accept': 'application/vnd.github+json'},
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        refs.extend(item['ref'] for item in response.json())
        url, params = response.links.get('next', {}).get('url'), None
    return refs


def parse_shipped_versions(refs, prefix):
    """Maps tag refs to Jira names, e.g. 'refs/tags/sqs-2026.5.2.1' -> 'sqs-2026.5'."""
    tag_pattern = re.compile(rf'^refs/tags/{re.escape(prefix)}(\d+)\.(\d+)\.')
    matches = (tag_pattern.match(ref) for ref in refs)
    return {f'{prefix}{m.group(1)}.{m.group(2)}' for m in matches if m}


def fetch_shipped_versions(github_token, prefix):
    """Jira version names already tagged in sonar-enterprise, or None on failure."""
    try:
        return parse_shipped_versions(list_tag_refs(github_token, prefix), prefix)
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        eprint(f"Warning: Failed to list sonar-enterprise '{prefix}*' tags: {e}")
        return None


def fetch_open_versions(jira_client, project_key):
    """Unreleased, non-archived project versions, or None on failure."""
    try:
        versions = jira_client.project_versions(project_key)
    except (JIRAError, requests.RequestException, ValueError) as e:
        eprint(f"Warning: Failed to fetch versions for project '{project_key}': {e}")
        eprint("Warning: Skipping automatic 'Fix versions' assignment.")
        return None
    return [
        v for v in versions
        if not getattr(v, 'released', False) and not getattr(v, 'archived', False)
    ]


def exclude_shipped_versions(versions, github_token, prefix):
    """Drops versions already tagged in sonar-enterprise; unchanged if the lookup fails."""
    shipped = fetch_shipped_versions(github_token, prefix)
    if not shipped:
        return versions
    already_tagged = [v.name for v in versions if v.name in shipped]
    if already_tagged:
        eprint(f"Skipping unreleased '{prefix}*' versions already tagged in sonar-enterprise: "
               f"{sort_by_version(already_tagged, prefix)}")
    return [v for v in versions if v.name not in shipped]


def resolve_fix_versions(jira_client, project_key, edition, github_token):
    """Fix version names for the edition, skipping tagged ones; [] on failure, never blocks."""
    prefixes = EDITION_VERSION_PREFIXES.get(edition)
    if not prefixes:
        eprint(f"No fix versions for edition '{edition}'.")
        return []

    eprint(f"\nResolving fix versions for edition '{edition}' in project '{project_key}'...")
    open_versions = fetch_open_versions(jira_client, project_key)
    if open_versions is None:
        return []

    if not github_token:
        eprint("Warning: No GITHUB_TOKEN, not cross-referencing versions with sonar-enterprise tags.")

    fix_versions = []
    for prefix in prefixes:
        candidates = exclude_shipped_versions(open_versions, github_token, prefix) if github_token else open_versions
        lowest = find_lowest_version(candidates, prefix)
        if lowest:
            fix_versions.append(lowest)
    eprint(f"Adding fix versions: {', '.join(fix_versions)}" if fix_versions else "No fix versions to add.")
    return fix_versions


def validate_release_ticket(jira_client, release_ticket_key):
    """
    Validates that the release ticket exists and is accessible.
    """
    eprint(f"Validating release ticket: {release_ticket_key}")
    try:
        release_ticket = jira_client.issue(release_ticket_key)
        eprint(f"Successfully found release ticket: {release_ticket.key} - {release_ticket.fields.summary}")
        return release_ticket
    except JIRAError as e:
        if e.status_code == 404:
            eprint(f"Error: Ticket '{release_ticket_key}' not found.")
        else:
            eprint(f"Error: Failed to access ticket '{release_ticket_key}'. Status: {e.status_code}")
            eprint(f"Response text: {e.text}")
        sys.exit(1)
    except Exception as e:
        eprint(f"An unexpected error occurred while validating release ticket: {e}")
        sys.exit(1)


def create_integration_ticket(jira_client, args):
    """
    Creates the integration ticket in Jira.
    """
    eprint(f"\nPreparing to create integration ticket in project '{args.target_jira_project}'...")

    # Get the default issue type for the project
    try:
        createmeta_data = jira_client.createmeta(projectKeys=args.target_jira_project, expand='projects.issuetypes')
        issue_types = createmeta_data['projects'][0]['issuetypes']

        # Try to find a suitable issue type (prefer feature, then first available)
        issue_type = None
        for it in issue_types:
            # Improvement and Task are included for backwards compatibility of deprecated Jira taxonomy
            if it['name'].lower() in ['feature', 'maintenance', 'improvement', 'task']:
                issue_type = it['name']
                break

        if not issue_type and issue_types:
            issue_type = issue_types[0]['name']

        if not issue_type:
            eprint(f"Error: No available issue types found for project '{args.target_jira_project}'")
            sys.exit(1)

        eprint(f"Using issue type: {issue_type}")

    except JIRAError as e:
        eprint(f"Error: Failed to access project '{args.target_jira_project}'. Status: {e.status_code}")
        eprint(f"Response text: {e.text}")
        sys.exit(1)

    ticket_details = {
        'project': args.target_jira_project,
        'issuetype': {'name': issue_type},
        'summary': args.ticket_summary,
    }

    if getattr(args, 'parent_epic', None):
        ticket_details['parent'] = {'key': args.parent_epic}

    if getattr(args, 'edition', None):
        eprint(f"Setting Edition: {args.edition}")
        ticket_details[CUSTOM_FIELDS['EDITION']] = {'value': args.edition}
        fix_versions = resolve_fix_versions(
            jira_client, args.target_jira_project, args.edition, os.environ.get('GITHUB_TOKEN')
        )
        if fix_versions:
            ticket_details['fixVersions'] = [{'name': name} for name in fix_versions]

    if getattr(args, 'team', None):
        ticket_details[CUSTOM_FIELDS['TEAM']] = args.team

    try:
        new_ticket = jira_client.create_issue(fields=ticket_details)
        eprint(f"Successfully created ticket: {new_ticket.key}")
        
        # Update description if provided (as a separate operation)
        if args.ticket_description:
            eprint("Waiting 3 seconds before setting description...")
            time.sleep(3)
            eprint("Setting description on ticket...")
            try:
                new_ticket.update(fields={'description': args.ticket_description})
                eprint("Description successfully set")
            except JIRAError as desc_e:
                eprint(f"Warning: Failed to set description on ticket. Status: {desc_e.status_code}")
                eprint(f"Description error: {desc_e.response.text}")
                eprint("Ticket was created successfully but without description")
        
        return new_ticket
    except JIRAError as e:
        eprint(f"Error: Failed to create Jira ticket. Status: {e.status_code}")
        eprint(f"Response text: {e.response.text}")
        sys.exit(1)


def link_tickets(jira_client, integration_ticket, release_ticket, link_type):
    """
    Creates a link between the integration ticket and the specified release ticket.
    """
    eprint(f"\nLinking tickets: {integration_ticket.key} -> {release_ticket.key}")
    eprint(f"Link type: {link_type}")

    try:
        jira_client.create_issue_link(
            type=link_type,
            inwardIssue=integration_ticket.key,
            outwardIssue=release_ticket.key
        )
        eprint(f"Successfully linked {integration_ticket.key} to {release_ticket.key}")
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

    parser.add_argument("--ticket-summary", required=True,
                       help="The summary/title for the integration ticket.")
    parser.add_argument("--ticket-description",
                       help="Optional description for the integration ticket.")
    parser.add_argument("--release-ticket-key", required=True,
                       help="The key of the ticket to link to (e.g., REL-123).")
    parser.add_argument("--target-jira-project", required=True,
                       help="The key of the project where the ticket will be created (e.g., SQS).")
    parser.add_argument("--use-sandbox", default="false",
                        help="Use Jira sandbox (true/false).")
    parser.add_argument("--link-type", default="relates to",
                       help="The type of link to create (e.g., 'relates to', 'depends on').")
    parser.add_argument("--parent-epic",
                       help="Optional Jira issue key to set as parent of the created ticket (e.g. CPP-7858).")
    parser.add_argument("--edition",
                       help="Optional 'Edition' value (e.g. 'Community Build & Server').")
    parser.add_argument("--team",
                       help="Optional Atlassian team UUID for the 'Team' field.")

    args = parser.parse_args()

    # Initialize Jira client
    jira = get_jira_instance(args.use_sandbox)

    # Validate the release ticket exists
    release_ticket = validate_release_ticket(jira, args.release_ticket_key)

    # Create the integration ticket
    integration_ticket = create_integration_ticket(jira, args)

    # Link the tickets
    link_tickets(jira, integration_ticket, release_ticket, args.link_type)

    # Output results
    eprint("\n" + "=" * 50)
    eprint("🎉 Successfully created integration ticket!")
    eprint(f"   Ticket Key: {integration_ticket.key}")
    eprint(f"   Ticket URL: {integration_ticket.permalink()}")
    eprint(f"   Linked to: {release_ticket.key}")
    eprint("=" * 50)

    # Output for GitHub Actions (captured by stdout)
    print(f"ticket_key={integration_ticket.key}")
    print(f"ticket_url={integration_ticket.permalink()}")


if __name__ == "__main__":
    main()
