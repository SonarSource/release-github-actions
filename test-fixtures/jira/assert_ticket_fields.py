#!/usr/bin/env python3
"""
Re-reads a Jira ticket and asserts its Edition, Team and Fix versions.

Usage:
    python assert_ticket_fields.py --use-sandbox true --ticket-key SONAR-101 \
        --team f1da89c9-3712-4d15-b194-a4b24406e3e4 --edition "Community Build & Server" \
        --fix-version-prefixes sqcb-,sqs-
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


def check_fix_version_prefixes(expected_arg, got):
    """Requires exactly one version per prefix and no unrelated versions."""
    prefixes = expected_arg.split(',')
    expected = {f'{prefix}*' for prefix in prefixes}
    ok = (
        all(prefixes)
        and len(got) == len(prefixes)
        and all(sum(name.startswith(prefix) for name in got) == 1 for prefix in prefixes)
        and all(any(name.startswith(prefix) for prefix in prefixes) for name in got)
    )
    return ok, expected


def main():
    parser = argparse.ArgumentParser(description="Assert Edition/Team/Fix versions on a Jira ticket.")
    parser.add_argument("--use-sandbox", default="false")
    parser.add_argument("--ticket-key", required=True)
    parser.add_argument("--team", required=True, help=f"Expected team UUID, or {UNSET}.")
    parser.add_argument("--edition", required=True, help=f"Expected Edition value, or {UNSET}.")
    fix_versions = parser.add_mutually_exclusive_group(required=True)
    fix_versions.add_argument("--fix-versions",
                              help=f"Comma-separated expected Fix versions names, {UNSET}, or {ANY}.")
    fix_versions.add_argument("--fix-version-prefixes",
                              help="Comma-separated prefixes; require exactly one Fix version per prefix.")
    args = parser.parse_args()

    fields = get_jira_instance(args.use_sandbox).issue(args.ticket_key).raw['fields']

    values = {
        'team': actual(fields, CUSTOM_FIELDS['TEAM'], 'id'),
        'edition': actual(fields, CUSTOM_FIELDS['EDITION'], 'value'),
        'fixVersions': actual_fix_versions(fields),
    }
    checks = {
        'team': check(args.team, values['team'], str, None),
        'edition': check(args.edition, values['edition'], str, None),
        'fixVersions': (
            check_fix_version_prefixes(args.fix_version_prefixes, values['fixVersions'])
            if args.fix_version_prefixes is not None
            else check(args.fix_versions, values['fixVersions'], lambda v: set(v.split(',')), set())
        ),
    }
    failed = False
    for name, (ok, expected) in checks.items():
        got = values[name]
        if ok:
            eprint(f"✅ {args.ticket_key} {name}: {got!r}")
        else:
            eprint(f"❌ {args.ticket_key} {name}: expected {expected!r}, got {got!r}")
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
