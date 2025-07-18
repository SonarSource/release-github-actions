#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script automates releasing a version in Jira and creating the next one.
"""

import argparse
import os
import sys
import datetime
from jira import JIRA
from jira.exceptions import JIRAError

# Jira server URLs
JIRA_SANDBOX_URL = "https://sonarsource-sandbox-608.atlassian.net/"
JIRA_PROD_URL = "https://sonarsource.atlassian.net/"

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

    if not jira_user or not jira_token:
        eprint("Error: JIRA_USER and JIRA_TOKEN environment variables must be set.")
        sys.exit(1)

    jira_url = JIRA_SANDBOX_URL if use_sandbox else JIRA_PROD_URL

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

def increment_version_string(version_name):
    """
    Increments the last component of a version string (e.g., '1.2.3' -> '1.2.4').
    """
    parts = version_name.split('.')
    try:
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    except (ValueError, IndexError):
        eprint(f"Error: Could not auto-increment version '{version_name}'. It does not seem to follow a standard x.y.z format.")
        sys.exit(1)

def main():
    """Main function to orchestrate the release and creation process."""
    parser = argparse.ArgumentParser(
        description="Releases a Jira version and creates the next one.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--project-key", required=True, help="The key of the Jira project (e.g., SONARIAC).")
    parser.add_argument("--jira-release-name", required=True, help="The name of the version to release.")
    parser.add_argument("--new-version-name", default="", help="The name for the next version.")
    parser.add_argument('--use-sandbox', action='store_true', help="Use the sandbox Jira server.")
    args = parser.parse_args()

    jira = get_jira_instance(args.use_sandbox)

    eprint(f"Searching for version '{args.jira_release_name}' in project '{args.project_key}'...")
    try:
        versions = jira.project_versions(args.project_key)
    except JIRAError as e:
        eprint(f"Error: Could not fetch versions for project '{args.project_key}'. Status: {e.status_code}")
        sys.exit(1)

    version_to_release = None
    for v in versions:
        if v.name == args.jira_release_name:
            version_to_release = v
            break

    if not version_to_release:
        eprint(f"Error: Version '{args.jira_release_name}' not found in project '{args.project_key}'.")
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


    if args.new_version_name:
        new_name = args.new_version_name
        eprint(f"Using provided name for new version: '{new_name}'.")
    else:
        new_name = increment_version_string(args.jira_release_name)
        eprint(f"Auto-incremented version name to: '{new_name}'.")

    eprint(f"Creating new version '{new_name}'...")
    try:
        new_version = jira.create_version(name=new_name, project=args.project_key)
        eprint(f"✅ Successfully created new version '{new_version.name}'.")
    except JIRAError as e:
        if "A version with this name already exists" in e.text:
            eprint(f"Warning: Version '{new_name}' already exists. Skipping creation.")
        else:
            eprint(f"Error: Failed to create new version. Status: {e.status_code}, Text: {e.text}")
            sys.exit(1)

    print(f"new_version_name={new_name}")

if __name__ == "__main__":
    main()
