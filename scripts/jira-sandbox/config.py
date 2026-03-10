#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Constants for the Jira sandbox test helpers.
"""

import datetime

SANDBOX_URL = "https://sonarsource-sandbox-608.atlassian.net/"

# Project keys
SONARIAC_PROJECT_KEY = "SONARIAC"
REL_PROJECT_KEY = "REL"

# Test version naming: 99.<MMDD>.<HHMM>
# Major 99 is well above real versions and clearly identifies test data.
# Patch encodes HHMM so it is always non-zero after midnight.
def make_test_version_name() -> str:
    now = datetime.datetime.now()
    mmdd = now.strftime("%m%d").lstrip("0") or "1"  # e.g. "310" for March 10
    hhmm = now.strftime("%H%M").lstrip("0") or "1"  # e.g. "1430" for 14:30
    return f"99.{mmdd}.{hhmm}"


def make_next_version_name(current_version: str) -> str:
    """Increments the patch component of a version string by 1."""
    parts = current_version.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


# Default issue type priority order for release notes
ISSUE_TYPE_ORDER = [
    "Feature",
    "New Feature",
    "False Positive",
    "False Negative",
    "Bug",
    "Improvement",
    "Security",
    "Maintenance",
]
