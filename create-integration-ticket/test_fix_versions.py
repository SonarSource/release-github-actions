#!/usr/bin/env python3
"""Behavior and HTTP contract tests for automatic integration ticket fix versions."""

import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from create_integration_ticket import (
    SONAR_ENTERPRISE_TAGS_URL,
    create_integration_ticket,
    list_tag_refs,
    parse_shipped_versions,
    resolve_fix_versions,
)
from jira_common import CUSTOM_FIELDS
from jira.exceptions import JIRAError


def make_version(name, released=False, archived=False):
    return SimpleNamespace(name=name, released=released, archived=archived)


@patch.dict(os.environ, {'GITHUB_TOKEN': ''})
class TestFixVersions(unittest.TestCase):
    def setUp(self):
        self.jira = Mock()
        self.jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }
        self.jira.create_issue.return_value.key = 'SONAR-123'
        self.args = SimpleNamespace(
            target_jira_project='SONAR', ticket_summary='Update sonar-security to 1.0.0',
            ticket_description=None, parent_epic=None, edition='Community Build & Server',
            team='f1da89c9-3712-4d15-b194-a4b24406e3e4',
        )

    def test_resolve_fix_versions_selects_open_versions_by_edition(self):
        self.jira.project_versions.return_value = [
            make_version('sqcb-26.11'), make_version('sqcb-26.10'), make_version('sqcb-26.9'),
            make_version('sqs-2026.6'), make_version('sqs-2026.5'),
            make_version('sqcb-26.8', released=True), make_version('sqcb-26.7', archived=True),
            make_version('sqs-2026.3', released=True), make_version('sqs-2026.4', archived=True),
        ]
        cases = [
            ('Community Build', ['sqcb-26.9']),
            ('Server', ['sqs-2026.5']),
            ('Community Build & Server', ['sqcb-26.9', 'sqs-2026.5']),
            ('N/A', []),
            ('Something Else', []),
        ]
        for edition, expected in cases:
            with self.subTest(edition=edition), patch('create_integration_ticket.requests.get') as get:
                self.jira.reset_mock()
                self.assertEqual(resolve_fix_versions(self.jira, 'SONAR', edition, None), expected)
                if expected:
                    self.jira.project_versions.assert_called_once_with('SONAR')
                else:
                    self.jira.project_versions.assert_not_called()
                get.assert_not_called()

    def test_resolve_fix_versions_accepts_only_matching_major_minor_names(self):
        cases = [
            ('Community Build', ['sqcb-9.1', 'sqcb-26.9'], ['sqcb-9.1']),
            ('Server', ['sqs-2026.100', 'sqs-2026.99'], ['sqs-2026.99']),
            ('Server', ['sqs-2025.4.9', 'sqs-2025.5'], ['sqs-2025.5']),
            ('Community Build', ['sqcb-26.10-RC1', 'sqcb-26.11-M1', 'sqcb-26.12'], ['sqcb-26.12']),
            ('Community Build', ['sqcb-lts-26.9', 'sqs-next', 'sqcb-26.10'], ['sqcb-26.10']),
            ('Community Build', ['sqs-2026.5', '2026.4'], []),
            ('Server', ['sqs-next'], []),
            ('Server', [], []),
        ]
        for edition, names, expected in cases:
            with self.subTest(edition=edition, names=names):
                self.jira.project_versions.return_value = [make_version(name) for name in names]
                self.assertEqual(resolve_fix_versions(self.jira, 'SONAR', edition, None), expected)

    def test_resolve_fix_versions_filters_each_prefix_by_its_own_tags(self):
        self.jira.project_versions.return_value = [
            make_version('sqcb-26.10'), make_version('sqcb-26.9'),
            make_version('sqs-2026.6'), make_version('sqs-2026.5'),
        ]
        cases = [
            ({'sqcb-': {'sqcb-26.9'}, 'sqs-': {'sqs-2026.5'}}, ['sqcb-26.10', 'sqs-2026.6']),
            ({'sqcb-': {'sqcb-26.9'}, 'sqs-': set()}, ['sqcb-26.10', 'sqs-2026.5']),
            ({'sqcb-': set(), 'sqs-': set()}, ['sqcb-26.9', 'sqs-2026.5']),
            ({'sqcb-': {'sqcb-24.12'}, 'sqs-': {'sqs-2025.1'}}, ['sqcb-26.9', 'sqs-2026.5']),
            ({'sqcb-': {'sqcb-26.9', 'sqcb-26.10'}, 'sqs-': {'sqs-2026.5', 'sqs-2026.6'}}, []),
            ({'sqcb-': {'sqcb-26.9', 'sqcb-26.10'}, 'sqs-': set()}, ['sqs-2026.5']),
            ({'sqcb-': None, 'sqs-': {'sqs-2026.5'}}, ['sqcb-26.9', 'sqs-2026.6']),
        ]
        for shipped, expected in cases:
            with self.subTest(shipped=shipped), patch(
                'create_integration_ticket.fetch_shipped_versions',
                side_effect=lambda token, prefix: shipped[prefix],
            ):
                self.assertEqual(
                    resolve_fix_versions(self.jira, 'SONAR', self.args.edition, 'token'), expected
                )

    def test_create_ticket_without_token_sets_edition_team_and_jira_fix_versions(self):
        self.jira.project_versions.return_value = [make_version('sqcb-26.9'), make_version('sqs-2026.5')]
        with patch('create_integration_ticket.requests.get') as get, patch('create_integration_ticket.eprint') as log:
            ticket = create_integration_ticket(self.jira, self.args)
        self.assertEqual(ticket, self.jira.create_issue.return_value)
        self.jira.create_issue.assert_called_once_with(fields={
            'project': 'SONAR', 'issuetype': {'name': 'Maintenance'}, 'summary': self.args.ticket_summary,
            CUSTOM_FIELDS['EDITION']: {'value': self.args.edition}, CUSTOM_FIELDS['TEAM']: self.args.team,
            'fixVersions': [{'name': 'sqcb-26.9'}, {'name': 'sqs-2026.5'}],
        })
        get.assert_not_called()
        self.assertTrue(any('No GITHUB_TOKEN' in message.args[0] for message in log.call_args_list))

    def test_create_ticket_uses_environment_token_to_skip_tagged_versions(self):
        self.jira.project_versions.return_value = [
            make_version('sqcb-26.9'), make_version('sqcb-26.10'),
            make_version('sqs-2026.5'), make_version('sqs-2026.6'),
        ]
        sqcb = Mock(links={})
        sqcb.json.return_value = [{'ref': 'refs/tags/sqcb-26.9.0.123'}]
        sqs = Mock(links={})
        sqs.json.return_value = [{'ref': 'refs/tags/sqs-2026.5.2.456'}]
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'test-token'}), patch(
            'create_integration_ticket.requests.get', side_effect=[sqcb, sqs]
        ) as get:
            ticket = create_integration_ticket(self.jira, self.args)
        self.assertEqual(ticket, self.jira.create_issue.return_value)
        self.jira.create_issue.assert_called_once_with(fields={
            'project': 'SONAR', 'issuetype': {'name': 'Maintenance'}, 'summary': self.args.ticket_summary,
            CUSTOM_FIELDS['EDITION']: {'value': self.args.edition}, CUSTOM_FIELDS['TEAM']: self.args.team,
            'fixVersions': [{'name': 'sqcb-26.10'}, {'name': 'sqs-2026.6'}],
        })
        self.assertEqual(get.call_count, 2)
        for prefix, request in zip(('sqcb-', 'sqs-'), get.call_args_list):
            self.assertEqual(request.args, (SONAR_ENTERPRISE_TAGS_URL + prefix,))
            self.assertEqual(request.kwargs['headers']['Authorization'], 'Bearer test-token')
        sqcb.raise_for_status.assert_called_once()
        sqs.raise_for_status.assert_called_once()

    def test_create_ticket_omits_fix_versions_when_edition_or_candidates_are_absent(self):
        cases = [
            ('N/A', ['sqcb-26.9', 'sqs-2026.5']),
            (None, ['sqcb-26.9']),
            ('', ['sqs-2026.5']),
            ('Community Build', []),
            ('Community Build', ['sqs-2026.5']),
        ]
        for edition, names in cases:
            with self.subTest(edition=edition, names=names), patch('create_integration_ticket.requests.get') as get:
                self.jira.reset_mock()
                self.jira.project_versions.return_value = [make_version(name) for name in names]
                self.args.edition = edition
                self.assertEqual(create_integration_ticket(self.jira, self.args), self.jira.create_issue.return_value)
                self.jira.create_issue.assert_called_once()
                fields = self.jira.create_issue.call_args.kwargs['fields']
                self.assertNotIn('fixVersions', fields)
                if edition:
                    self.assertEqual(fields[CUSTOM_FIELDS['EDITION']], {'value': edition})
                else:
                    self.assertNotIn(CUSTOM_FIELDS['EDITION'], fields)
                if edition in ('N/A', None, ''):
                    self.jira.project_versions.assert_not_called()
                get.assert_not_called()

    def test_create_ticket_survives_jira_version_lookup_failures(self):
        errors = [
            JIRAError(status_code=500, text='Server Error'),
            requests.ConnectionError('Connection failed'), requests.Timeout('Read timed out'),
            ValueError('Invalid Jira JSON'),
        ]
        for error in errors:
            with self.subTest(error=error), patch.dict(os.environ, {'GITHUB_TOKEN': 'test-token'}), patch(
                'create_integration_ticket.requests.get'
            ) as get, patch('create_integration_ticket.eprint') as log:
                self.jira.reset_mock()
                self.jira.project_versions.side_effect = error
                self.assertEqual(create_integration_ticket(self.jira, self.args), self.jira.create_issue.return_value)
                self.jira.create_issue.assert_called_once()
                fields = self.jira.create_issue.call_args.kwargs['fields']
                self.assertNotIn('fixVersions', fields)
                self.assertEqual(fields[CUSTOM_FIELDS['EDITION']], {'value': self.args.edition})
                self.assertEqual(fields[CUSTOM_FIELDS['TEAM']], self.args.team)
                get.assert_not_called()
                self.assertTrue(any('Failed to fetch versions' in message.args[0] for message in log.call_args_list))

    def test_create_ticket_falls_back_to_jira_versions_on_github_lookup_failure(self):
        self.args.edition = 'Server'
        self.jira.project_versions.return_value = [make_version('sqs-2026.6'), make_version('sqs-2026.5')]
        first_page = Mock(links={'next': {'url': 'https://api.github.com/next'}})
        first_page.json.return_value = [{'ref': 'refs/tags/sqs-2026.5.0.123'}]
        last_page = Mock(links={})
        last_page.raise_for_status.side_effect = requests.HTTPError('503 Unavailable')
        cases = [
            ('HTTP error', {'raise_for_status.side_effect': requests.HTTPError('404 Not Found')}, None),
            ('connection error', {}, requests.ConnectionError('Connection failed')),
            ('timeout', {}, requests.Timeout('Read timed out')),
            ('invalid JSON', {'json.side_effect': ValueError('Invalid JSON')}, None),
            ('missing ref', {'json.return_value': [{'name': 'x'}]}, None),
            ('error object', {'json.return_value': {'message': 'Not Found'}}, None),
            ('invalid ref type', {'json.return_value': [{'ref': None}]}, None),
            ('later page failure', {}, [first_page, last_page]),
        ]
        for label, response_config, request_error in cases:
            with self.subTest(label=label), patch.dict(os.environ, {'GITHUB_TOKEN': 'test-token'}), patch(
                'create_integration_ticket.requests.get',
                return_value=Mock(links={}, **response_config), side_effect=request_error,
            ), patch('create_integration_ticket.eprint') as log:
                self.jira.reset_mock()
                self.assertEqual(create_integration_ticket(self.jira, self.args), self.jira.create_issue.return_value)
                self.jira.create_issue.assert_called_once()
                self.assertEqual(
                    self.jira.create_issue.call_args.kwargs['fields']['fixVersions'], [{'name': 'sqs-2026.5'}]
                )
                self.assertTrue(
                    any('Failed to list sonar-enterprise' in message.args[0] for message in log.call_args_list)
                )

    def test_list_tag_refs_follows_pagination_with_authentication_and_timeout(self):
        next_url = SONAR_ENTERPRISE_TAGS_URL + 'sqs-?page=2'
        first_page = Mock(links={'next': {'url': next_url}})
        first_page.json.return_value = [{'ref': 'refs/tags/sqs-2025.1.0.123'}]
        last_page = Mock(links={})
        last_page.json.return_value = [{'ref': 'refs/tags/sqs-2026.5.0.456'}]
        with patch('create_integration_ticket.requests.get', side_effect=[first_page, last_page]) as get:
            self.assertEqual(list_tag_refs('test-token', 'sqs-'), [
                'refs/tags/sqs-2025.1.0.123', 'refs/tags/sqs-2026.5.0.456',
            ])
        headers = {'Authorization': 'Bearer test-token', 'Accept': 'application/vnd.github+json'}
        self.assertEqual(get.call_args_list, [
            call(SONAR_ENTERPRISE_TAGS_URL + 'sqs-', headers=headers, params={'per_page': 100}, timeout=30),
            call(next_url, headers=headers, params=None, timeout=30),
        ])
        first_page.raise_for_status.assert_called_once()
        last_page.raise_for_status.assert_called_once()

    def test_parse_shipped_versions_maps_only_matching_tags_to_major_minor_names(self):
        refs = [
            'refs/tags/sqs-2026.5.0.132233', 'refs/tags/sqs-2026.5.2.132813',
            'refs/tags/sqs-2026.4.1.126914', 'refs/tags/sqs-2026.6',
            'refs/tags/sqcb-26.9.0.123', 'refs/tags/sqcb-26.10.1.456',
            'refs/tags/sqsx-2026.5.0.1', 'refs/tags/sqs-foo',
        ]
        cases = [
            ('sqs-', refs, {'sqs-2026.5', 'sqs-2026.4'}),
            ('sqcb-', refs, {'sqcb-26.9', 'sqcb-26.10'}),
            ('sqs-', [], set()),
            ('sqs-', ['refs/tags/sqsx-2026.5.0.1', 'refs/tags/sqs-foo', 'refs/tags/sqcb-26.9.0.1'], set()),
        ]
        for prefix, tags, expected in cases:
            with self.subTest(prefix=prefix, tags=tags):
                self.assertEqual(parse_shipped_versions(tags, prefix), expected)


if __name__ == '__main__':
    unittest.main()
