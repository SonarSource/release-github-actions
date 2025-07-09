#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A reusable utility module for connecting to a Jira instance.
"""

import os
import sys
from jira import JIRA
from jira.exceptions import JIRAError

# --- Constants ---
JIRA_SANDBOX_URL = "https://sonarsource-sandbox-608.atlassian.net/"
JIRA_PROD_URL = "https://sonarsource.atlassian.net/"

def get_jira_instance(use_sandbox=True):
    """
    Initializes and returns a JIRA client instance and the server URL used.

    This function reads credentials from the JIRA_USER and JIRA_TOKEN
    environment variables. It then selects the Jira server (sandbox or
    production) based on the use_sandbox flag, authenticates, and performs
    an initial connection test.

    Args:
        use_sandbox (bool): If True, connects to the sandbox server. If False,
                            connects to the production server. Defaults to True.

    Returns:
        tuple[JIRA, str]: A tuple containing:
                          - An authenticated JIRA client instance.
                          - The URL of the Jira server that was connected to.

    Raises:
        SystemExit: If environment variables are not set, or if
                    authentication or connection fails.
    """
    jira_user = os.environ.get('JIRA_USER')
    jira_token = os.environ.get('JIRA_TOKEN')

    if not jira_user or not jira_token:
        print("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.", file=sys.stderr)
        sys.exit(1)

    jira_url = JIRA_SANDBOX_URL if use_sandbox else JIRA_PROD_URL

    print(f"Connecting to JIRA server at: {jira_url}")
    print(f"Authenticating with user: {jira_user}")

    try:
        jira_client = JIRA(jira_url, basic_auth=(jira_user, jira_token), get_server_info=True)
        print("JIRA authentication successful.")
        return jira_client, jira_url
    except JIRAError as e:
        print(f"Error: JIRA authentication failed. Status: {e.status_code}", file=sys.stderr)
        print("Please check your JIRA URL, user, and token.", file=sys.stderr)
        print(f"Response text: {e.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during JIRA connection: {e}", file=sys.stderr)
        sys.exit(1)
