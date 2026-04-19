#!/usr/bin/env python3
"""Shared Jira connection helper for test fixtures."""

import os
import sys

from jira import JIRA
from jira.exceptions import JIRAError


def eprint(*args, **kwargs):
    """Prints messages to stderr for logging."""
    print(*args, file=sys.stderr, **kwargs)


def get_jira_instance(jira_url):
    """
    Initializes and returns a JIRA client instance.
    Authentication is handled via JIRA_USER and JIRA_TOKEN environment variables.
    """
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
