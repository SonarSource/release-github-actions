#!/usr/bin/env python3
"""
Creates test fixtures in a Jira sandbox project.

Creates a version and sample issues linked to it via fixVersion.
Outputs a JSON object with created resource IDs for use by cleanup.py.

Usage:
    python setup.py --project-key SONARIAC --run-id 12345 --jira-url https://sandbox.atlassian.net/
"""

import argparse
import json
import os
import sys

from jira_client import get_jira_instance, eprint
from config import VERSION_PREFIX, ISSUE_TYPES

STATE_FILE = "/tmp/jira-fixtures.json"


def write_state(state):
    """Writes the current state to STATE_FILE so cleanup can run even on partial failure."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def create_test_version(jira, project_key, run_id):
    """Creates a test version named 99.<run_id> in the given project."""
    version_name = f"{VERSION_PREFIX}.{run_id}"
    eprint(f"Creating test version '{version_name}' in project '{project_key}'...")
    version = jira.create_version(name=version_name, project=project_key)
    eprint(f"Created version '{version.name}' (id={version.id})")
    return version


def create_test_issues(jira, project_key, version, run_id, on_issue_created=None):
    """Creates one test issue per issue type, linked to the version via fixVersion."""
    issues = []
    for issue_type in ISSUE_TYPES:
        fields = {
            'project': project_key,
            'issuetype': {'name': issue_type},
            'summary': f"Test {issue_type} for GHA run {run_id}",
            'fixVersions': [{'name': version.name}],
        }
        issue = jira.create_issue(fields=fields)
        eprint(f"Created {issue_type} issue: {issue.key}")
        issues.append(issue)
        if on_issue_created:
            on_issue_created(issue)
    return issues


def main():
    parser = argparse.ArgumentParser(description="Set up Jira test fixtures.")
    parser.add_argument("--project-key", required=True, help="Jira project key (e.g., SONARIAC).")
    parser.add_argument("--run-id", required=True, help="Unique run identifier for naming.")
    parser.add_argument("--jira-url", required=True, help="URL of the Jira instance.")
    args = parser.parse_args()

    jira = get_jira_instance(args.jira_url)

    version = create_test_version(jira, args.project_key, args.run_id)

    # Write partial state immediately so cleanup can delete the version even if issue creation fails.
    state = {"version_id": version.id, "version_name": version.name, "issue_keys": []}
    write_state(state)

    def on_issue_created(issue):
        state["issue_keys"].append(issue.key)
        write_state(state)

    issues = create_test_issues(jira, args.project_key, version, args.run_id, on_issue_created)

    print(json.dumps(state))


if __name__ == "__main__":
    main()
