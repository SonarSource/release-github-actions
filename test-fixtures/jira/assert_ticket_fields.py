#!/usr/bin/env python3
"""
Re-reads a Jira ticket and asserts its Edition, Team and Fix versions (NONE = unset, ANY = set).

Usage:
    python assert_ticket_fields.py --use-sandbox true --ticket-key SONAR-101 \
        --team f1da89c9-3712-4d15-b194-a4b24406e3e4 --edition "Community Build & Server" \
        --fix-versions ANY
    python assert_ticket_fields.py --use-sandbox true --ticket-key GHA-102 \
        --team NONE --edition NONE --fix-versions NONE
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))
from jira_common import CUSTOM_FIELDS
from jira_client import get_jira_instance, eprint

UNSET = 'NONE'
ANY = 'ANY'


def actual(fields, field_id, key):
    """Both fields read back as objects — Team carries 'id', Edition 'value'."""
    value = fields.get(field_id)
    return value.get(key) if isinstance(value, dict) else value


def actual_fix_versions(fields):
    """fixVersions reads back as a list of objects, each carrying 'name'."""
    return {v['name'] for v in fields.get('fixVersions', [])}


def check(expected_arg, got, parse_expected, empty):
    """Compares one field: NONE = must be empty, ANY = must be set, else exact match."""
    if expected_arg == UNSET:
        ok, expected = got == empty, empty
    elif expected_arg == ANY:
        ok, expected = got != empty, f'<{ANY}>'
    else:
        expected = parse_expected(expected_arg)
        ok = got == expected
    return ok, expected


def main():
    parser = argparse.ArgumentParser(description="Assert Edition/Team/Fix versions on a Jira ticket.")
    parser.add_argument("--use-sandbox", default="false")
    parser.add_argument("--ticket-key", required=True)
    parser.add_argument("--team", required=True, help=f"Expected team UUID, or {UNSET}.")
    parser.add_argument("--edition", required=True, help=f"Expected Edition value, or {UNSET}.")
    parser.add_argument("--fix-versions", required=True,
                         help=f"Comma-separated expected Fix versions names, {UNSET}, or {ANY}.")
    args = parser.parse_args()

    fields = get_jira_instance(args.use_sandbox).issue(args.ticket_key).raw['fields']

    failed = False
    for name, expected_arg, got, parse_expected, empty in [
        ('team', args.team, actual(fields, CUSTOM_FIELDS['TEAM'], 'id'), lambda v: v, None),
        ('edition', args.edition, actual(fields, CUSTOM_FIELDS['EDITION'], 'value'), lambda v: v, None),
        ('fixVersions', args.fix_versions, actual_fix_versions(fields), lambda v: set(v.split(',')), set()),
    ]:
        ok, expected = check(expected_arg, got, parse_expected, empty)
        if ok:
            eprint(f"✅ {args.ticket_key} {name}: {got!r}")
        else:
            eprint(f"❌ {args.ticket_key} {name}: expected {expected!r}, got {got!r}")
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
