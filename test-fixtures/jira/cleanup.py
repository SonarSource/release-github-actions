#!/usr/bin/env python3
"""
Cleans up Jira test fixtures created by setup.py.

Deletes issues and versions by ID. Idempotent: succeeds even if
resources have already been deleted or never existed.

Usage:
    python cleanup.py --use-sandbox true --version-id 12345 --issue-keys SONARIAC-100,SONARIAC-101
    python cleanup.py --use-sandbox true --state-file /tmp/setup-state.json
"""

import argparse
import json
import os
import sys

from jira_client import get_jira_instance, eprint, safe_path
from jira.exceptions import JIRAError


def delete_issues(jira, issue_keys):
    """Deletes issues by key. Ignores errors (idempotent), but warns loudly so a leak in the
    shared sandbox surfaces in the run's Annotations panel instead of scrolling past in the log."""
    for key in issue_keys:
        try:
            issue = jira.issue(key)
            issue.delete()
            eprint(f"Deleted issue: {key}")
        except JIRAError as e:
            eprint(f"::warning::Could not delete issue {key} (status={e.status_code}) — it may be left behind in the sandbox.")
        except Exception as e:
            eprint(f"::warning::Unexpected error deleting issue {key}: {e} — it may be left behind in the sandbox.")


def delete_version(jira, version_id):
    """Deletes a version by ID. Ignores errors (idempotent), but warns loudly so a leak in the
    shared sandbox surfaces in the run's Annotations panel instead of scrolling past in the log."""
    try:
        version = jira.version(version_id)
        version.delete()
        eprint(f"Deleted version: {version_id}")
    except JIRAError as e:
        eprint(f"::warning::Could not delete version {version_id} (status={e.status_code}) — it may be left behind in the sandbox.")
    except Exception as e:
        eprint(f"::warning::Unexpected error deleting version {version_id}: {e} — it may be left behind in the sandbox.")


def main():
    parser = argparse.ArgumentParser(description="Clean up Jira test fixtures.")
    parser.add_argument("--use-sandbox", default="false", help="Use Jira sandbox (true/false).")
    parser.add_argument("--version-id", help="ID of the version to delete.")
    parser.add_argument("--issue-keys", default="", help="Comma-separated issue keys to delete.")
    parser.add_argument("--state-file", help="Path to JSON state file from setup.py.")
    args = parser.parse_args()

    jira = get_jira_instance(args.use_sandbox)

    version_id = args.version_id
    issue_keys = [k for k in args.issue_keys.split(',') if k] if args.issue_keys else []

    if args.state_file:
        args.state_file = safe_path(args.state_file)
        try:
            with open(args.state_file) as f:
                state = json.load(f)
            version_id = state.get('version_id', version_id)
            issue_keys = state.get('issue_keys', issue_keys)
        except FileNotFoundError:
            eprint(f"Warning: State file {args.state_file} not found. Nothing to clean up from state.")
        except json.JSONDecodeError:
            eprint(f"Warning: State file {args.state_file} is not valid JSON. Nothing to clean up from state.")

    if issue_keys:
        delete_issues(jira, issue_keys)

    if version_id:
        delete_version(jira, version_id)

    eprint("Cleanup complete.")


if __name__ == "__main__":
    main()
