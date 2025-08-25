#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script automates releasing a version in Jira.
"""

import argparse
import os
import sys
import datetime
from jira import JIRA
from jira.exceptions import JIRAError


# noinspection DuplicatedCode
def eprint(*args, **kwargs):
    """Prints messages to the standard error stream (stderr) for logging."""
    print(*args, file=sys.stderr, **kwargs)

# noinspection DuplicatedCode
def get_jira_instance(jira_url):
    """
    Initializes and returns a JIRA client instance.
    Authentication is handled via environment variables.
    """
    jira_user = os.environ.get('JIRA_USER')
    jira_token = os.environ.get('JIRA_TOKEN')

    if not jira_user or not jira_token:
        eprint("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.")
        sys.exit(1)

    eprint(f"Connecting to JIRA server at: {jira_url}")
    try:
        jira_client = JIRA(jira_url, basic_auth=(jira_user, jira_token))
        # Verify connection
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

def main():
    """Main function to orchestrate the release process."""
    parser = argparse.ArgumentParser(
        description="Releases a Jira version.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--project-key", required=True, help="The key of the Jira project (e.g., SONARIAC).")
    parser.add_argument("--version-name", required=True, help="The name for the next version.")
    parser.add_argument('--jira-url', required=True, help="URL of the Jira instance to use.")
    args = parser.parse_args()

    jira = get_jira_instance(args.jira_url)

    eprint(f"Searching for version '{args.version_name}' in project '{args.project_key}'")

    project = jira.project(args.project_key)
    version_to_release = None
    for version in project.versions:
        if version.name == args.version_name:
            version_to_release = version
            break

    if not version_to_release:
        eprint(f"Error: Version '{args.version_name}' not found in project '{args.project_key}'.")
        sys.exit(1)

    if version_to_release.released:
        eprint(f"Warning: Version '{version_to_release.name}' is already released. Skipping release step.")
    else:
        eprint(f"Found version '{version_to_release.name}'. Releasing it now...")
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            version_to_release.update(released=True, releaseDate=today)
            eprint(f"✅ Successfully released version '{version_to_release.name}'.")
        except JIRAError as e:
            eprint(f"Error: Failed to release version. Status: {e.status_code}, Text: {e.text}")
            sys.exit(1)

if __name__ == "__main__":
    main()
