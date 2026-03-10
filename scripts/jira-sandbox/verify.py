#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verifies Jira sandbox state and simulates the full release lifecycle.

Reads test_state.json (created by setup.py) and runs assertions against
the live sandbox, importing action modules directly to test them end-to-end.

Verifications:
  1. Version exists and is unreleased
  2. Issues are assigned to the test version
  3. release-jira-version: marks version released
  4. create-jira-version: creates next version
  5. get-jira-release-notes: returns expected issue types
  6. create-integration-ticket: creates ticket linked to release ticket
  7. update-release-ticket-status: transitions release ticket to "Start Progress"
"""

import datetime
import json
import os
import sys
from jira.exceptions import JIRAError

from config import SANDBOX_URL, SONARIAC_PROJECT_KEY, make_next_version_name, ISSUE_TYPE_ORDER
from jira_client import get_jira_client

STATE_FILE = os.path.join(os.path.dirname(__file__), "test_state.json")

# Add action directories to path so we can import their modules directly
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "release-jira-version"))
sys.path.insert(0, os.path.join(REPO_ROOT, "create-jira-version"))
sys.path.insert(0, os.path.join(REPO_ROOT, "get-jira-release-notes"))
sys.path.insert(0, os.path.join(REPO_ROOT, "create-integration-ticket"))
sys.path.insert(0, os.path.join(REPO_ROOT, "update-release-ticket-status"))


results: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = ""):
    status = "✅" if passed else "❌"
    print(f"  {status} {name}" + (f": {detail}" if detail else ""))
    results.append((name, passed, detail))


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        print(f"Error: State file not found at '{STATE_FILE}'. Run setup.py first.", file=sys.stderr)
        sys.exit(1)
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Verification steps
# ---------------------------------------------------------------------------

def verify_version_exists(jira, state: dict):
    """1. Verify version exists and is unreleased."""
    print("\n[1] Verifying version exists and is unreleased...")
    version_name = state["version_name"]
    try:
        versions = jira.project_versions(SONARIAC_PROJECT_KEY)
        version = next((v for v in versions if v.name == version_name), None)
        if version is None:
            check("Version exists", False, f"'{version_name}' not found")
            return
        check("Version exists", True, f"id={version.id}")
        check("Version is unreleased", not version.released, f"released={version.released}")
    except JIRAError as e:
        check("Version exists", False, f"JIRAError {e.status_code}")


def verify_issues_have_fix_version(jira, state: dict):
    """2. Verify issues are assigned to the test version."""
    print("\n[2] Verifying issues have correct fixVersion...")
    version_name = state["version_name"]
    issue_keys = [
        state["feature_issue_key"],
        state["bug_issue_key"],
        state["maintenance_issue_key"],
    ]
    for key in issue_keys:
        try:
            issue = jira.issue(key)
            fix_versions = [v.name for v in issue.fields.fixVersions]
            check(f"{key} has fixVersion '{version_name}'", version_name in fix_versions,
                  f"fixVersions={fix_versions}")
        except JIRAError as e:
            check(f"{key} fixVersion check", False, f"JIRAError {e.status_code}")


def verify_release_jira_version(jira, state: dict):
    """3. Simulate release-jira-version: mark the version released."""
    print("\n[3] Simulating release-jira-version...")
    version_name = state["version_name"]
    try:
        from release_jira_version import get_jira_instance  # noqa: F401 — import to confirm module loads
    except ImportError as e:
        check("release-jira-version module importable", False, str(e))
        return

    # Call the Jira API directly (same logic as release_jira_version.main)
    try:
        project = jira.project(SONARIAC_PROJECT_KEY)
        version = next((v for v in project.versions if v.name == version_name), None)
        if not version:
            check("Version found for release", False, f"'{version_name}' not found")
            return

        today = datetime.date.today().strftime("%Y-%m-%d")
        version.update(released=True, releaseDate=today)

        # Confirm
        refreshed = jira.project(SONARIAC_PROJECT_KEY)
        v = next((v for v in refreshed.versions if v.name == version_name), None)
        released_ok = v is not None and v.released
        release_date_ok = v is not None and getattr(v, "releaseDate", None) == today
        check("Version marked released", released_ok)
        check("Version has today's release date", release_date_ok, f"releaseDate={getattr(v, 'releaseDate', None)}")
    except JIRAError as e:
        check("release-jira-version", False, f"JIRAError {e.status_code}: {e.text}")


def verify_create_jira_version(jira, state: dict):
    """4. Simulate create-jira-version: create the next version."""
    print("\n[4] Simulating create-jira-version (create next version)...")
    next_version_name = make_next_version_name(state["version_name"])
    try:
        new_version = jira.create_version(name=next_version_name, project=SONARIAC_PROJECT_KEY)
        check("Next version created", True, f"{new_version.name} (id={new_version.id})")
        # Save to state so cleanup can delete it
        state["next_version_name"] = new_version.name
        save_state(state)
    except JIRAError as e:
        if "A version with this name already exists" in (e.text or ""):
            check("Next version created (already existed)", True, next_version_name)
            state["next_version_name"] = next_version_name
            save_state(state)
        else:
            check("Next version created", False, f"JIRAError {e.status_code}: {e.text}")


def verify_get_jira_release_notes(jira, state: dict):
    """5. Simulate get-jira-release-notes: fetch issues and verify content."""
    print("\n[5] Simulating get-jira-release-notes...")
    version_name = state["version_name"]
    try:
        from get_jira_release_notes import get_issues_for_release, format_notes_as_markdown, get_project_name
    except ImportError as e:
        check("get-jira-release-notes module importable", False, str(e))
        return

    try:
        issues = get_issues_for_release(jira, SONARIAC_PROJECT_KEY, version_name)
        check("Issues fetched for release", len(issues) >= 3, f"got {len(issues)} issues")

        issue_types = {i.fields.issuetype.name for i in issues}
        check("Feature issue present in notes", "Feature" in issue_types, f"types={issue_types}")
        check("Bug issue present in notes", "Bug" in issue_types, f"types={issue_types}")
        check("Maintenance issue present in notes", "Maintenance" in issue_types, f"types={issue_types}")

        project_name = get_project_name(jira, SONARIAC_PROJECT_KEY)
        markdown = format_notes_as_markdown(issues, SANDBOX_URL, project_name, version_name, ISSUE_TYPE_ORDER)
        check("Markdown release notes generated", version_name in markdown,
              f"first 100 chars: {markdown[:100]!r}")
    except (JIRAError, Exception) as e:
        check("get-jira-release-notes", False, str(e))


def verify_create_integration_ticket(jira, state: dict):
    """6. Simulate create-integration-ticket: create ticket linked to release ticket."""
    print("\n[6] Simulating create-integration-ticket...")
    rel_ticket_key = state["rel_ticket_key"]
    version_name = state["version_name"]

    # Determine a suitable issue type in SONARIAC project
    try:
        createmeta = jira.createmeta(projectKeys=SONARIAC_PROJECT_KEY, expand="projects.issuetypes")
        issue_types = createmeta["projects"][0]["issuetypes"]
        preferred = ["feature", "maintenance", "improvement", "task"]
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
    except JIRAError as e:
        check("Integration ticket issue type lookup", False, f"JIRAError {e.status_code}")
        return

    try:
        integration_ticket = jira.create_issue(fields={
            "project": SONARIAC_PROJECT_KEY,
            "issuetype": {"name": issue_type},
            "summary": f"[TEST] Integration for {version_name}",
        })
        check("Integration ticket created", True, integration_ticket.key)
        state["integration_ticket_key"] = integration_ticket.key
        save_state(state)

        # Link to release ticket
        jira.create_issue_link(
            type="relates to",
            inwardIssue=integration_ticket.key,
            outwardIssue=rel_ticket_key,
        )

        # Verify link exists on the integration ticket
        linked_ticket = jira.issue(integration_ticket.key)
        links = linked_ticket.fields.issuelinks
        linked_keys = []
        for link in links:
            if hasattr(link, "outwardIssue") and link.outwardIssue:
                linked_keys.append(link.outwardIssue.key)
            if hasattr(link, "inwardIssue") and link.inwardIssue:
                linked_keys.append(link.inwardIssue.key)
        check("Integration ticket linked to release ticket", rel_ticket_key in linked_keys,
              f"linked keys: {linked_keys}")
    except JIRAError as e:
        check("create-integration-ticket", False, f"JIRAError {e.status_code}: {e.text}")


def verify_update_release_ticket_status(jira, state: dict):
    """7. Simulate update-release-ticket-status: transition release ticket."""
    print("\n[7] Simulating update-release-ticket-status...")
    rel_ticket_key = state["rel_ticket_key"]
    target_status = "Start Progress"

    try:
        issue = jira.issue(rel_ticket_key)
        current_status = issue.fields.status.name
        check("Release ticket fetched", True, f"current status: '{current_status}'")

        if current_status == target_status:
            check(f"Ticket transitioned to '{target_status}'", True, "already at target status")
            return

        jira.transition_issue(issue, target_status)

        # Confirm transition
        refreshed = jira.issue(rel_ticket_key)
        new_status = refreshed.fields.status.name
        check(f"Ticket transitioned to '{target_status}'", new_status == target_status,
              f"new status: '{new_status}'")
    except JIRAError as e:
        check(f"update-release-ticket-status", False, f"JIRAError {e.status_code}: {e.text}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("VERIFY: Running release lifecycle verifications")
    print("=" * 60)

    state = load_state()
    jira = get_jira_client()

    verify_version_exists(jira, state)
    verify_issues_have_fix_version(jira, state)
    verify_release_jira_version(jira, state)
    verify_create_jira_version(jira, state)
    verify_get_jira_release_notes(jira, state)
    verify_create_integration_ticket(jira, state)
    verify_update_release_ticket_status(jira, state)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}" + (f" ({detail})" if detail else ""))

    print(f"\n{len(passed)}/{len(results)} checks passed.")
    if failed:
        print(f"\nFailed checks:")
        for name, _, detail in failed:
            print(f"  ❌ {name}" + (f": {detail}" if detail else ""))
        sys.exit(1)
    else:
        print("\n✅ All verifications passed.")


if __name__ == "__main__":
    main()
