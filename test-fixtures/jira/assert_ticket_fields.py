#!/usr/bin/env python3
"""
Asserts the Edition and Team fields on a Jira ticket, re-reading it from the server.

Re-reading rather than trusting the create call is the only way to catch a wrong custom field
ID, a wrong value shape, or a field silently dropped because it is not on the project's create
screen.

Both expectations are required, and NONE means "must be unset", so a run can never pass by
simply not asserting anything.

Usage:
    python assert_ticket_fields.py --use-sandbox true --ticket-key SONAR-101 \
        --team f1da89c9-3712-4d15-b194-a4b24406e3e4 --edition "Community Build & Server"
    python assert_ticket_fields.py --use-sandbox true --ticket-key GHA-102 \
        --team NONE --edition NONE
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))
from jira_common import CUSTOM_FIELDS
from jira_client import get_jira_instance, eprint

UNSET = 'NONE'


def actual(fields, field_id, key):
    """Both fields read back as objects — Team carries 'id', Edition 'value'."""
    value = fields.get(field_id)
    return value.get(key) if isinstance(value, dict) else value


def main():
    parser = argparse.ArgumentParser(description="Assert Edition/Team on a Jira ticket.")
    parser.add_argument("--use-sandbox", default="false")
    parser.add_argument("--ticket-key", required=True)
    parser.add_argument("--team", required=True, help=f"Expected team UUID, or {UNSET}.")
    parser.add_argument("--edition", required=True, help=f"Expected Edition value, or {UNSET}.")
    args = parser.parse_args()

    fields = get_jira_instance(args.use_sandbox).issue(args.ticket_key).raw['fields']

    failed = False
    for name, expected, got in [
        ('team', args.team, actual(fields, CUSTOM_FIELDS['TEAM'], 'id')),
        ('edition', args.edition, actual(fields, CUSTOM_FIELDS['EDITION'], 'value')),
    ]:
        expected = None if expected == UNSET else expected
        if got == expected:
            eprint(f"✅ {args.ticket_key} {name}: {got!r}")
        else:
            eprint(f"❌ {args.ticket_key} {name}: expected {expected!r}, got {got!r}")
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
