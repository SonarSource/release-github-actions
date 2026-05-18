#!/usr/bin/env python3
"""
Creates KTLO epic test fixtures in a Jira sandbox project for testing resolve-ktlo-epic.

Creates three scenarios:
  - one_match:       a single in-progress epic with "KTLO" in the summary
  - multi_match:     two in-progress epics with "KTLO" in the summary
  - no_match:        one in-progress epic WITHOUT "KTLO" in the summary

Usage:
    python setup_ktlo.py --project-key GHA --run-id 12345 --jira-url https://sandbox.atlassian.net/
"""

import argparse
import json
import os
import sys

from jira_client import get_jira_instance, eprint

STATE_FILE_DEFAULT = os.path.join(os.path.expanduser("~"), ".cache", "jira-ktlo-fixtures.json")


def create_epic(jira, project_key, summary):
    fields = {
        'project': project_key,
        'issuetype': {'name': 'Epic'},
        'summary': summary,
    }
    epic = jira.create_issue(fields=fields)
    eprint(f"Created epic: {epic.key} — {summary}")
    return epic


def transition_to_in_progress(jira, issue_key):
    transitions = jira.transitions(issue_key)
    for t in transitions:
        if t['name'].lower() in ('start', 'start progress', 'in progress'):
            jira.transition_issue(issue_key, t['id'])
            eprint(f"Transitioned {issue_key} to In Progress (transition: {t['name']})")
            return
    eprint(f"Warning: Could not find an 'In Progress' transition for {issue_key}. Available: {[t['name'] for t in transitions]}")


def main():
    parser = argparse.ArgumentParser(description="Set up KTLO epic test fixtures.")
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--jira-url", required=True)
    parser.add_argument("--state-file", default=STATE_FILE_DEFAULT)
    args = parser.parse_args()

    jira = get_jira_instance(args.jira_url)
    run_id = args.run_id
    project = args.project_key

    # Ensure state file directory exists with restrictive permissions
    state_dir = os.path.dirname(args.state_file)
    if state_dir and not os.path.exists(state_dir):
        os.makedirs(state_dir, mode=0o700)

    state = {"epic_keys": []}

    def add(epic):
        state["epic_keys"].append(epic.key)
        with open(args.state_file, "w") as f:
            json.dump(state, f)

    one_match = create_epic(jira, project, f"GHA KTLO test fixture {run_id} — one match")
    transition_to_in_progress(jira, one_match.key)
    add(one_match)

    multi_a = create_epic(jira, project, f"GHA KTLO test fixture {run_id} — multi A")
    transition_to_in_progress(jira, multi_a.key)
    add(multi_a)

    multi_b = create_epic(jira, project, f"GHA KTLO test fixture {run_id} — multi B")
    transition_to_in_progress(jira, multi_b.key)
    add(multi_b)

    no_match = create_epic(jira, project, f"GHA planning test fixture {run_id} — no KTLO keyword")
    transition_to_in_progress(jira, no_match.key)
    add(no_match)

    state.update({
        "one_match_key": one_match.key,
        "multi_a_key": multi_a.key,
        "multi_b_key": multi_b.key,
        "no_match_key": no_match.key,
    })
    with open(args.state_file, "w") as f:
        json.dump(state, f)

    print(json.dumps(state))


if __name__ == "__main__":
    main()
