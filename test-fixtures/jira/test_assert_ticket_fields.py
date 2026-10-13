#!/usr/bin/env python3
"""Tests for the Jira field assertions used by the sandbox workflow."""

import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from assert_ticket_fields import main
from jira_common import CUSTOM_FIELDS


class TestAssertTicketFields(unittest.TestCase):
    def setUp(self):
        self.fields = {
            CUSTOM_FIELDS['TEAM']: {'id': 'team-id'},
            CUSTOM_FIELDS['EDITION']: {'value': 'Community Build & Server'},
            'fixVersions': [],
        }
        self.jira = Mock()
        self.jira.issue.return_value.raw = {'fields': self.fields}
        self.argv = [
            'assert_ticket_fields.py', '--use-sandbox', 'true', '--ticket-key', 'SONAR-123',
            '--team', 'team-id', '--edition', 'Community Build & Server',
        ]

    def run_assertion(self, *fix_version_args):
        with patch('sys.argv', self.argv + list(fix_version_args)), patch(
            'assert_ticket_fields.get_jira_instance', return_value=self.jira
        ), patch('assert_ticket_fields.eprint'), patch('sys.stderr'), self.assertRaises(SystemExit) as result:
            main()
        return result.exception.code

    def test_requires_one_fix_version_per_prefix_and_no_other_versions(self):
        cases = [
            (['sqs-2026.5', 'sqcb-26.9'], 0),
            (['sqs-2026.5'], 1),
            (['unrelated-version'], 1),
            (['sqs-2026.5', 'sqs-2026.6'], 1),
            (['sqs-2026.5', 'sqcb-26.9', 'sqcb-26.10'], 1),
            (['sqs-2026.5', 'sqcb-26.9', 'unrelated-version'], 1),
            ([], 1),
        ]
        for names, expected_exit in cases:
            with self.subTest(names=names):
                self.fields['fixVersions'] = [{'name': name} for name in names]
                self.assertEqual(self.run_assertion('--fix-version-prefixes', 'sqcb-,sqs-'), expected_exit)

    def test_preserves_unset_any_and_exact_fix_version_expectations(self):
        cases = [
            ('NONE', [], 0),
            ('NONE', ['sqs-2026.5'], 1),
            ('ANY', ['sqs-2026.5'], 0),
            ('ANY', [], 1),
            ('sqcb-26.9,sqs-2026.5', ['sqs-2026.5', 'sqcb-26.9'], 0),
            ('sqcb-26.9,sqs-2026.5', ['sqs-2026.5'], 1),
        ]
        for expectation, names, expected_exit in cases:
            with self.subTest(expectation=expectation, names=names):
                self.fields['fixVersions'] = [{'name': name} for name in names]
                self.assertEqual(self.run_assertion('--fix-versions', expectation), expected_exit)

    def test_checks_team_and_edition_alongside_fix_versions(self):
        cases = [
            (CUSTOM_FIELDS['TEAM'], {'id': 'other-team'}),
            (CUSTOM_FIELDS['EDITION'], {'value': 'Server'}),
            (CUSTOM_FIELDS['TEAM'], None),
            (CUSTOM_FIELDS['EDITION'], None),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                fields = dict(self.fields)
                fields[field] = value
                self.jira.issue.return_value.raw = {'fields': fields}
                self.assertEqual(self.run_assertion('--fix-versions', 'NONE'), 1)
        self.jira.issue.return_value.raw = {'fields': {}}
        self.argv = [
            'assert_ticket_fields.py', '--ticket-key', 'SONAR-123', '--team', 'NONE', '--edition', 'NONE',
        ]
        self.assertEqual(self.run_assertion('--fix-versions', 'NONE'), 0)

    def test_requires_exactly_one_fix_version_expectation(self):
        for args in ((), ('--fix-versions', 'ANY', '--fix-version-prefixes', 'sqcb-,sqs-')):
            with self.subTest(args=args):
                self.assertEqual(self.run_assertion(*args), 2)
        self.jira.issue.assert_not_called()


if __name__ == '__main__':
    unittest.main()
