#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared Jira client helper for sandbox test scripts.
"""

import os
import sys
from jira import JIRA
from jira.exceptions import JIRAError

from config import SANDBOX_URL


def get_jira_client() -> JIRA:
    """
    Returns an authenticated JIRA client for the sandbox instance.
    Reads JIRA_USER and JIRA_TOKEN from environment variables.
    """
    jira_user = os.environ.get("JIRA_USER")
    jira_token = os.environ.get("JIRA_TOKEN")

    if not jira_user or not jira_token:
        print("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to Jira sandbox at: {SANDBOX_URL}", file=sys.stderr)
    try:
        client = JIRA(SANDBOX_URL, basic_auth=(jira_user, jira_token))
        client.server_info()
        print("Jira authentication successful.", file=sys.stderr)
        return client
    except JIRAError as e:
        print(f"Error: Jira authentication failed. Status: {e.status_code}", file=sys.stderr)
        print(f"Response text: {e.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during Jira connection: {e}", file=sys.stderr)
        sys.exit(1)
