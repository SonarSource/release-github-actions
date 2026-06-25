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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))
from jira_common import eprint, get_jira_instance
from jira.exceptions import JIRAError



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
