#!/usr/bin/env python3
"""
Cleans up KTLO epic test fixtures created by setup_ktlo.py.

Usage:
    python cleanup_ktlo.py --jira-url https://sandbox.atlassian.net/ --state-file ~/.cache/jira-ktlo-fixtures.json
"""

import argparse
import json

from jira_client import get_jira_instance, eprint
from jira.exceptions import JIRAError


def delete_epics(jira, epic_keys):
    for key in epic_keys:
        try:
            issue = jira.issue(key)
            issue.delete()
            eprint(f"Deleted epic: {key}")
        except JIRAError as e:
            eprint(f"Warning: Could not delete epic {key} (status={e.status_code}). Skipping.")
        except Exception as e:
            eprint(f"Warning: Unexpected error deleting epic {key}: {e}. Skipping.")


def main():
    parser = argparse.ArgumentParser(description="Clean up KTLO epic test fixtures.")
    parser.add_argument("--jira-url", required=True)
    parser.add_argument("--state-file", required=True)
    args = parser.parse_args()

    jira = get_jira_instance(args.jira_url)

    try:
        with open(args.state_file) as f:
            state = json.load(f)
        epic_keys = state.get("epic_keys", [])
    except FileNotFoundError:
        eprint(f"Warning: State file {args.state_file} not found. Nothing to clean up.")
        return
    except json.JSONDecodeError:
        eprint(f"Warning: State file {args.state_file} is not valid JSON. Nothing to clean up.")
        return

    delete_epics(jira, epic_keys)
    eprint("KTLO fixture cleanup complete.")


if __name__ == "__main__":
    main()
