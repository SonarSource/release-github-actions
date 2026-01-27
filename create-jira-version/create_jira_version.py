#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script automates creating a version in Jira.
"""

import argparse
import os
import re
import sys
from jira import JIRA
from jira.exceptions import JIRAError


def normalize_version_name(version_name):
    """
    Normalizes a version name by removing .0 patch suffix.
    For example: 1.2.0 -> 1.2, but 1.2.4 stays as 1.2.4
    """
    # Match versions ending in .0 (e.g., 1.2.0, 10.20.0)
    match = re.match(r'^(.+)\.0$', version_name)
    if match:
        return match.group(1)
    return version_name


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


def find_existing_version(jira, project_key, version_name):
    """Finds and returns an existing version by name in a project."""
    project = jira.project(project_key)
    for version in project.versions:
        if version.name == version_name:
            return version
    return None


def handle_existing_version(jira, project_key, version_name):
    """Handles the case when a version already exists."""
    eprint(f"Warning: Version '{version_name}' already exists. Skipping creation.")
    existing_version = find_existing_version(jira, project_key, version_name)
    if existing_version:
        print(f"new_version_id={existing_version.id}")
        print(f"new_version_name={existing_version.name}")
    else:
        eprint(f"Error: Could not find existing version '{version_name}' in project.")
        sys.exit(1)


def main():
    """Main function to orchestrate the creation process."""
    parser = argparse.ArgumentParser(
        description="Releases a Jira version and creates the next one.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--project-key", required=True, help="The key of the Jira project (e.g., SONARIAC).")
    parser.add_argument("--version-name", required=True, help="The name for the next version.")
    parser.add_argument('--jira-url', required=True, help="URL of the Jira instance to use.")
    args = parser.parse_args()

    jira = get_jira_instance(args.jira_url)

    version_name = normalize_version_name(args.version_name)
    if version_name != args.version_name:
        eprint(f"Normalized version name from '{args.version_name}' to '{version_name}'")

    eprint(f"Try to create new version '{version_name}'")
    try:
        new_version = jira.create_version(name=version_name, project=args.project_key)
        eprint(f"✅ Successfully created new version '{new_version.name}'")

        print(f"new_version_id={new_version.id}")
        print(f"new_version_name={new_version.name}")

    except JIRAError as e:
        if "A version with this name already exists" in e.text:
            handle_existing_version(jira, args.project_key, version_name)
        else:
            eprint(f"Error: Failed to create new version. Status: {e.status_code}, Text: {e.text}")
            sys.exit(1)


if __name__ == "__main__":
    main()
