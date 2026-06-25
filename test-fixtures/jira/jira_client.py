#!/usr/bin/env python3
"""Shared Jira connection helper for test fixtures."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from path_utils import safe_path

from jira import JIRA
from jira.exceptions import JIRAError


def eprint(*args, **kwargs):
    """Prints messages to stderr for logging."""
    print(*args, file=sys.stderr, **kwargs)


JIRA_URL_PROD    = "https://sonarsource.atlassian.net/"
JIRA_URL_SANDBOX = "https://sonarsource-sandbox-608.atlassian.net/"


def get_jira_instance(use_sandbox):
    """
    Initializes and returns a JIRA client instance.
    Accepts use_sandbox as bool or 'true'/'false' string.
    Authentication via JIRA_USER and JIRA_TOKEN environment variables.
    """
    if isinstance(use_sandbox, str):
        use_sandbox = use_sandbox.lower() == 'true'
    jira_url = JIRA_URL_SANDBOX if use_sandbox else JIRA_URL_PROD

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
