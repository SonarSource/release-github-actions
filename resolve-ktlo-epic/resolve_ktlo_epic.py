#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Resolves the current KTLO epic in a Jira project by querying for in-progress
epics whose summary matches a configurable regex pattern.
"""

import argparse
import os
import re
import sys
from jira import JIRA
from jira.exceptions import JIRAError


# noinspection DuplicatedCode
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# noinspection DuplicatedCode
def get_jira_instance(jira_url):
    jira_user = os.environ.get('JIRA_USER')
    jira_token = os.environ.get('JIRA_TOKEN')

    if not jira_user or not jira_token:
        eprint("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.")
        sys.exit(1)

    eprint(f"Connecting to Jira at: {jira_url}")
    try:
        client = JIRA(jira_url, basic_auth=(jira_user, jira_token), get_server_info=True)
        eprint("Jira authentication successful.")
        return client
    except JIRAError as e:
        eprint(f"Error: Jira authentication failed. Status: {e.status_code}")
        eprint(f"Response text: {e.text}")
        sys.exit(1)
    except Exception as e:
        eprint(f"An unexpected error occurred during Jira connection: {e}")
        sys.exit(1)


def resolve_ktlo_epic(jira, project, pattern):
    """
    Returns the key of the first in-progress epic matching the regex pattern,
    or None if none found. Warns when zero or multiple epics match.
    """
    try:
        re.compile(pattern)
    except re.error as e:
        eprint(f"Error: invalid --epic-name-pattern '{pattern}': {e}")
        sys.exit(1)

    jql = f'project = {project} AND issuetype = Epic AND statusCategory = "In Progress"'
    eprint(f"Searching for KTLO epic in project '{project}' with pattern '{pattern}'...")
    epics = jira.search_issues(jql, maxResults=False)

    matches = [e for e in epics if re.search(pattern, e.fields.summary, re.IGNORECASE)]

    if not matches:
        warn(f"No in-progress epic matching '{pattern}' found in project '{project}'. Integration ticket will be created without a parent.")
        return None

    if len(matches) > 1:
        keys = [e.key for e in matches]
        warn(f"Multiple epics matching '{pattern}' found in project '{project}': {keys}. Using the first one: {matches[0].key}.")

    eprint(f"Resolved KTLO epic: {matches[0].key} — {matches[0].fields.summary}")
    return matches[0].key


def warn(message):
    """Emit a GitHub Actions warning annotation to stderr."""
    eprint(f"::warning::{message}")


def main():
    parser = argparse.ArgumentParser(description="Resolve the current KTLO epic in a Jira project.")
    parser.add_argument("--jira-project", required=True, help="Jira project key (e.g. CPP).")
    parser.add_argument("--epic-name-pattern", default="KTLO",
                        help="Regex pattern matched against epic summaries (default: KTLO).")
    parser.add_argument("--jira-url", required=True, help="Jira server URL.")
    args = parser.parse_args()

    jira = get_jira_instance(args.jira_url)
    epic_key = resolve_ktlo_epic(jira, args.jira_project, args.epic_name_pattern)

    print(f"epic_key={epic_key or ''}")


if __name__ == "__main__":
    main()
