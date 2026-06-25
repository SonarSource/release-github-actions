#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared helpers for the Jira-integration actions.

Imported by each action's script via a sys.path insert (the actions run
standalone via @v1, which checks out the whole repo, so this file is present at
`../shared/jira_common.py` at runtime). Do NOT package this with pyproject /
`pip install -e .` — that forces an install step into every consumer workflow
(see reverted commit ad8a663).
"""

import os
import sys

JIRA_URL_PROD    = "https://sonarsource.atlassian.net/"
JIRA_URL_SANDBOX = "https://sonarsource-sandbox-608.atlassian.net/"

# Jira custom field IDs — single source of truth (also documented in CLAUDE.md).
CUSTOM_FIELDS = {
    'SHORT_DESCRIPTION': 'customfield_10146',
    'LINK_TO_RELEASE_NOTES': 'customfield_10145',
    'DOCUMENTATION_STATUS': 'customfield_10147',
    'RULE_PROPS_CHANGED': 'customfield_11263',
    'SONARLINT_CHANGELOG': 'customfield_11264',
}


def get_jira_url(use_sandbox):
    """Return the Jira URL for the given environment. Accepts bool, 'true'/'false' string, or None."""
    if isinstance(use_sandbox, str):
        use_sandbox = use_sandbox.lower() == 'true'
    return JIRA_URL_SANDBOX if use_sandbox else JIRA_URL_PROD


def eprint(*args, **kwargs):
    """
    Print to stderr, keeping diagnostics separate from stdout (which carries the
    script's result, redirected to $GITHUB_OUTPUT by the action.yml).
    """
    print(*args, file=sys.stderr, **kwargs)


def get_jira_instance(use_sandbox):
    """
    Initialize and return a JIRA client for the given environment.
    Accepts the same values as get_jira_url: bool, 'true'/'false' string, or None.
    Authenticates with JIRA_USER / JIRA_TOKEN env vars. Exits(1) on failure.
    """
    # Imported here so callers that only need eprint/CUSTOM_FIELDS don't pull in jira.
    from jira import JIRA
    from jira.exceptions import JIRAError

    jira_url = get_jira_url(use_sandbox)
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
