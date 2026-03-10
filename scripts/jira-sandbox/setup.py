#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sets up Jira sandbox test fixtures for a full release cycle.

Creates:
  - A Jira version in SONARIAC (e.g. 99.310.1430)
  - One Feature, one Bug, one Maintenance issue assigned to that version
  - A release ticket in REL project

Writes all created object keys/IDs to test_state.json for use by verify.py and cleanup.py.
"""

import json
import os
import sys
from jira.exceptions import JIRAError

from config import SANDBOX_URL, SONARIAC_PROJECT_KEY, REL_PROJECT_KEY, make_test_version_name
from jira_client import get_jira_client

STATE_FILE = os.path.join(os.path.dirname(__file__), "test_state.json")


def create_version(jira, version_name: str) -> str:
    """Creates a Jira version in SONARIAC and returns its ID."""
    print(f"Creating version '{version_name}' in project '{SONARIAC_PROJECT_KEY}'...")
    try:
        version = jira.create_version(name=version_name, project=SONARIAC_PROJECT_KEY)
        print(f"  Created version: {version.name} (id={version.id})")
        return version.id
    except JIRAError as e:
        print(f"Error: Failed to create version. Status: {e.status_code}, Text: {e.text}", file=sys.stderr)
        sys.exit(1)


def create_issue(jira, project_key: str, issue_type: str, summary: str, fix_version_name: str = None) -> str:
    """Creates a Jira issue and returns its key."""
    fields = {
        "project": project_key,
        "issuetype": {"name": issue_type},
        "summary": summary,
    }
    if fix_version_name:
        fields["fixVersions"] = [{"name": fix_version_name}]

    try:
        issue = jira.create_issue(fields=fields)
        print(f"  Created {issue_type} issue: {issue.key} — {summary}")
        return issue.key
    except JIRAError as e:
        print(f"Error: Failed to create issue. Status: {e.status_code}, Text: {e.text}", file=sys.stderr)
        sys.exit(1)


def create_rel_ticket(jira, version_name: str) -> str:
    """Creates a release ticket in the REL project and returns its key."""
    print(f"Creating release ticket in '{REL_PROJECT_KEY}'...")

    # Find a suitable issue type in the REL project
    try:
        createmeta = jira.createmeta(projectKeys=REL_PROJECT_KEY, expand="projects.issuetypes")
        issue_types = createmeta["projects"][0]["issuetypes"]
        preferred = ["ask for release", "task", "story", "feature", "maintenance"]
        issue_type = None
        for pref in preferred:
            for it in issue_types:
                if it["name"].lower() == pref:
                    issue_type = it["name"]
                    break
            if issue_type:
                break
        if not issue_type and issue_types:
            issue_type = issue_types[0]["name"]
        if not issue_type:
            print(f"Error: No issue types found for project '{REL_PROJECT_KEY}'", file=sys.stderr)
            sys.exit(1)
    except JIRAError as e:
        print(f"Error: Failed to fetch issue types for '{REL_PROJECT_KEY}'. Status: {e.status_code}", file=sys.stderr)
        sys.exit(1)

    fields = {
        "project": REL_PROJECT_KEY,
        "issuetype": {"name": issue_type},
        "summary": f"[TEST] SONARIAC {version_name} release",
    }
    try:
        ticket = jira.create_issue(fields=fields)
        print(f"  Created release ticket: {ticket.key} (type: {issue_type})")
        return ticket.key
    except JIRAError as e:
        print(f"Error: Failed to create release ticket. Status: {e.status_code}, Text: {e.text}", file=sys.stderr)
        sys.exit(1)


def main():
    print("=" * 60)
    print("SETUP: Creating Jira sandbox test fixtures")
    print("=" * 60)

    jira = get_jira_client()
    version_name = make_test_version_name()

    print(f"\nTest version name: {version_name}\n")

    # 1. Create version
    version_id = create_version(jira, version_name)

    # 2. Create issues assigned to the version
    print(f"\nCreating test issues in '{SONARIAC_PROJECT_KEY}'...")
    feature_key = create_issue(
        jira, SONARIAC_PROJECT_KEY, "Feature",
        f"[TEST] Feature for {version_name}",
        fix_version_name=version_name,
    )
    bug_key = create_issue(
        jira, SONARIAC_PROJECT_KEY, "Bug",
        f"[TEST] Bug fix for {version_name}",
        fix_version_name=version_name,
    )
    maintenance_key = create_issue(
        jira, SONARIAC_PROJECT_KEY, "Maintenance",
        f"[TEST] Maintenance for {version_name}",
        fix_version_name=version_name,
    )

    # 3. Create release ticket
    print()
    rel_ticket_key = create_rel_ticket(jira, version_name)

    # 4. Write state
    state = {
        "version_name": version_name,
        "version_id": version_id,
        "feature_issue_key": feature_key,
        "bug_issue_key": bug_key,
        "maintenance_issue_key": maintenance_key,
        "rel_ticket_key": rel_ticket_key,
        "sandbox_url": SANDBOX_URL,
        "sonariac_project_key": SONARIAC_PROJECT_KEY,
        "rel_project_key": REL_PROJECT_KEY,
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"\nState written to: {STATE_FILE}")

    print("\n✅ Setup complete.")
    print(f"   Version:         {version_name} (id={version_id})")
    print(f"   Feature issue:   {feature_key}")
    print(f"   Bug issue:       {bug_key}")
    print(f"   Maintenance:     {maintenance_key}")
    print(f"   Release ticket:  {rel_ticket_key}")


if __name__ == "__main__":
    main()
