#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script automates creating a version in Jira.
"""

import argparse
import os
import sys
from jira import JIRA
from jira.exceptions import JIRAError

def eprint(*args, **kwargs):
    """Prints messages to the standard error stream (stderr) for logging."""
    print(*args, file=sys.stderr, **kwargs)

# noinspection DuplicatedCode
def get_jira_instance(use_sandbox=False):
    """
    Initializes and returns a JIRA client instance.
    Authentication is handled via environment variables.
    """
    jira_user = os.environ.get('JIRA_USER')
    jira_token = os.environ.get('JIRA_TOKEN')
    jira_prod_url = os.environ.get('JIRA_PROD_URL')
    jira_sandbox_url = os.environ.get('JIRA_SANDBOX_URL')

    if not jira_user or not jira_token:
        eprint("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.")
        sys.exit(1)

    jira_url = jira_sandbox_url if use_sandbox else jira_prod_url

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
    """Main function to orchestrate the creation process."""
    parser = argparse.ArgumentParser(
        description="Releases a Jira version and creates the next one.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--project-key", required=True, help="The key of the Jira project (e.g., SONARIAC).")
    parser.add_argument("--version-name", required=True, help="The name for the next version.")
    parser.add_argument('--use-sandbox', action='store_true', help="Use the sandbox Jira server.")
    args = parser.parse_args()

    jira = get_jira_instance(args.use_sandbox)

    eprint(f"Try to create new version '{args.version_name}'")
    try:
        new_version = jira.create_version(name=args.version_name, project=args.project_key)
        eprint(f"✅ Successfully created new version '{new_version.name}'")

        print(f"new_version_id={new_version.id}")
        print(f"new_version_name={new_version.name}")

    except JIRAError as e:
        if "A version with this name already exists" in e.text:
            eprint(f"Warning: Version '{args.version_name}' already exists. Skipping creation.")

            # Fetch the existing version details
            project = jira.project(args.project_key)
            existing_version = None
            for version in project.versions:
                if version.name == args.version_name:
                    existing_version = version
                    break

            if existing_version:
                print(f"new_version_id={existing_version.id}")
                print(f"new_version_name={existing_version.name}")
            else:
                eprint(f"Error: Could not find existing version '{args.version_name}' in project.")
                sys.exit(1)
        else:
            eprint(f"Error: Failed to create new version. Status: {e.status_code}, Text: {e.text}")
            sys.exit(1)



if __name__ == "__main__":
    main()
