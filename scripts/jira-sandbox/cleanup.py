#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cleans up Jira sandbox test fixtures created by setup.py.

Reads test_state.json and:
  1. Deletes all created issues (Feature, Bug, Maintenance, release ticket)
  2. Deletes the test Jira version (moves issues off version first)
  3. Removes test_state.json
"""

import json
import os
import sys
from jira.exceptions import JIRAError

from jira_client import get_jira_client

STATE_FILE = os.path.join(os.path.dirname(__file__), "test_state.json")


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        print(f"No state file found at '{STATE_FILE}'. Nothing to clean up.")
        sys.exit(0)
    with open(STATE_FILE) as f:
        return json.load(f)


def delete_issue(jira, key: str) -> bool:
    try:
        jira.issue(key).delete()
        print(f"  Deleted issue: {key}")
        return True
    except JIRAError as e:
        if e.status_code == 404:
            print(f"  Issue {key} not found (already deleted?)")
            return True
        print(f"  Warning: Failed to delete issue {key}. Status: {e.status_code}", file=sys.stderr)
        return False


def delete_version(jira, project_key: str, version_name: str) -> bool:
    """Finds and deletes a version by name, moving any remaining issues to 'unresolved'."""
    try:
        versions = jira.project_versions(project_key)
        version = next((v for v in versions if v.name == version_name), None)
        if not version:
            print(f"  Version '{version_name}' not found in '{project_key}' (already deleted?)")
            return True

        # Delete version; moveFixIssuesTo=None means issues become un-versioned
        version.delete(moveFixIssuesTo=None)
        print(f"  Deleted version: {version_name}")
        return True
    except JIRAError as e:
        print(f"  Warning: Failed to delete version '{version_name}'. Status: {e.status_code}: {e.text}",
              file=sys.stderr)
        return False


def main():
    print("=" * 60)
    print("CLEANUP: Removing Jira sandbox test fixtures")
    print("=" * 60)

    state = load_state()
    version_name = state["version_name"]
    project_key = state["sonariac_project_key"]

    jira = get_jira_client()

    issues_to_delete = [
        state.get("integration_ticket_key"),  # created by verify.py (may not exist)
        state.get("next_version_created"),     # next version issues (none created)
        state.get("feature_issue_key"),
        state.get("bug_issue_key"),
        state.get("maintenance_issue_key"),
        state.get("rel_ticket_key"),
    ]

    print("\nDeleting issues...")
    for key in issues_to_delete:
        if key:
            delete_issue(jira, key)

    print("\nDeleting Jira versions...")
    delete_version(jira, project_key, version_name)

    # Also clean up next version if verify.py created one
    next_version = state.get("next_version_name")
    if next_version:
        delete_version(jira, project_key, next_version)

    print("\nRemoving state file...")
    os.remove(STATE_FILE)
    print(f"  Removed: {STATE_FILE}")

    print("\n✅ Cleanup complete.")


if __name__ == "__main__":
    main()
