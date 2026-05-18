#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for resolve_ktlo_epic.py
"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from resolve_ktlo_epic import get_jira_instance, resolve_ktlo_epic, main
from jira.exceptions import JIRAError


def _make_epic(key, summary):
    epic = Mock()
    epic.key = key
    epic.fields.summary = summary
    return epic


class TestGetJiraInstance(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_credentials_exits(self):
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://sonarsource.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'user', 'JIRA_TOKEN': 'token'})
    @patch('resolve_ktlo_epic.JIRA')
    def test_success_returns_client(self, mock_jira_class):
        mock_client = Mock()
        mock_jira_class.return_value = mock_client
        result = get_jira_instance('https://sonarsource.atlassian.net/')
        self.assertEqual(result, mock_client)
        mock_jira_class.assert_called_once_with(
            'https://sonarsource.atlassian.net/',
            basic_auth=('user', 'token'),
            get_server_info=True,
        )

    @patch.dict(os.environ, {'JIRA_USER': 'user', 'JIRA_TOKEN': 'token'})
    @patch('resolve_ktlo_epic.JIRA')
    def test_auth_failure_exits(self, mock_jira_class):
        mock_jira_class.side_effect = JIRAError(status_code=401, text='Unauthorized')
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://sonarsource.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'user', 'JIRA_TOKEN': 'token'})
    @patch('resolve_ktlo_epic.JIRA')
    def test_unexpected_error_exits(self, mock_jira_class):
        mock_jira_class.side_effect = Exception('network error')
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://sonarsource.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)


class TestResolveKtloEpic(unittest.TestCase):

    def _jira_with_epics(self, epics):
        mock_jira = Mock()
        mock_jira.search_issues.return_value = epics
        return mock_jira

    def test_one_match_returns_key(self):
        epic = _make_epic('CPP-7858', 'CFamily 2026Q2 KTLO')
        jira = self._jira_with_epics([epic])
        result = resolve_ktlo_epic(jira, 'CPP', 'KTLO')
        self.assertEqual(result, 'CPP-7858')

    def test_zero_matches_returns_none_and_warns(self):
        jira = self._jira_with_epics([])
        with patch('resolve_ktlo_epic.eprint') as mock_eprint:
            result = resolve_ktlo_epic(jira, 'CPP', 'KTLO')
        self.assertIsNone(result)
        warning_messages = ' '.join(str(c) for c in mock_eprint.call_args_list)
        self.assertIn('Warning', warning_messages)

    def test_multiple_matches_returns_first_and_warns(self):
        epics = [
            _make_epic('CPP-100', 'CFamily KTLO Q1'),
            _make_epic('CPP-200', 'CFamily KTLO Q2'),
        ]
        jira = self._jira_with_epics(epics)
        with patch('resolve_ktlo_epic.eprint') as mock_eprint:
            result = resolve_ktlo_epic(jira, 'CPP', 'KTLO')
        self.assertEqual(result, 'CPP-100')
        warning_messages = ' '.join(str(c) for c in mock_eprint.call_args_list)
        self.assertIn('Warning', warning_messages)

    def test_epics_present_but_none_match_pattern_returns_none(self):
        epics = [
            _make_epic('CPP-999', 'CFamily Sprint Planning'),
            _make_epic('CPP-998', 'CFamily Roadmap 2026'),
        ]
        jira = self._jira_with_epics(epics)
        with patch('resolve_ktlo_epic.eprint') as mock_eprint:
            result = resolve_ktlo_epic(jira, 'CPP', 'KTLO')
        self.assertIsNone(result)

    def test_custom_regex_pattern_matches(self):
        epic = _make_epic('NET-3604', '.NET KTLO 2026 Q2')
        jira = self._jira_with_epics([epic])
        result = resolve_ktlo_epic(jira, 'NET', r'KTLO\s+\d{4}')
        self.assertEqual(result, 'NET-3604')

    def test_custom_regex_pattern_no_match(self):
        epic = _make_epic('NET-3604', '.NET KTLO 2026 Q2')
        jira = self._jira_with_epics([epic])
        with patch('resolve_ktlo_epic.eprint'):
            result = resolve_ktlo_epic(jira, 'NET', r'TLO-\d{4}')
        self.assertIsNone(result)

    def test_pattern_match_is_case_insensitive(self):
        epic = _make_epic('JS-1531', 'Web-Squad-2026-Q2-ktlo')
        jira = self._jira_with_epics([epic])
        result = resolve_ktlo_epic(jira, 'JS', 'KTLO')
        self.assertEqual(result, 'JS-1531')

    def test_jql_uses_correct_query(self):
        jira = self._jira_with_epics([])
        with patch('resolve_ktlo_epic.eprint'):
            resolve_ktlo_epic(jira, 'CPP', 'KTLO')
        call_args = jira.search_issues.call_args
        jql = call_args[0][0]
        self.assertIn('project = CPP', jql)
        self.assertIn('issuetype = Epic', jql)
        self.assertIn('statusCategory', jql)
        self.assertIn('In Progress', jql)


class TestMain(unittest.TestCase):

    @patch('sys.argv', [
        'resolve_ktlo_epic.py',
        '--jira-project', 'CPP',
        '--jira-url', 'https://sonarsource.atlassian.net/',
    ])
    @patch('resolve_ktlo_epic.get_jira_instance')
    @patch('resolve_ktlo_epic.resolve_ktlo_epic')
    def test_main_one_match_outputs_key(self, mock_resolve, mock_get_jira):
        mock_get_jira.return_value = Mock()
        mock_resolve.return_value = 'CPP-7858'
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
        self.assertIn('epic_key=CPP-7858', mock_stdout.getvalue())

    @patch('sys.argv', [
        'resolve_ktlo_epic.py',
        '--jira-project', 'CPP',
        '--jira-url', 'https://sonarsource.atlassian.net/',
    ])
    @patch('resolve_ktlo_epic.get_jira_instance')
    @patch('resolve_ktlo_epic.resolve_ktlo_epic')
    def test_main_no_match_outputs_empty_key(self, mock_resolve, mock_get_jira):
        mock_get_jira.return_value = Mock()
        mock_resolve.return_value = None
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            main()
        self.assertIn('epic_key=', mock_stdout.getvalue())
        self.assertNotIn('epic_key=CPP', mock_stdout.getvalue())

    @patch('sys.argv', [
        'resolve_ktlo_epic.py',
        '--jira-project', 'CPP',
        '--epic-name-pattern', r'KTLO\s+\d{4}',
        '--jira-url', 'https://sonarsource.atlassian.net/',
    ])
    @patch('resolve_ktlo_epic.get_jira_instance')
    @patch('resolve_ktlo_epic.resolve_ktlo_epic')
    def test_main_passes_custom_pattern(self, mock_resolve, mock_get_jira):
        mock_get_jira.return_value = Mock()
        mock_resolve.return_value = 'CPP-1'
        main()
        mock_resolve.assert_called_once_with(mock_get_jira.return_value, 'CPP', r'KTLO\s+\d{4}')

    @patch('sys.argv', [
        'resolve_ktlo_epic.py',
        '--jira-project', 'CPP',
        '--jira-url', 'https://sonarsource.atlassian.net/',
    ])
    @patch('resolve_ktlo_epic.get_jira_instance')
    @patch('resolve_ktlo_epic.resolve_ktlo_epic')
    def test_main_uses_default_pattern(self, mock_resolve, mock_get_jira):
        mock_get_jira.return_value = Mock()
        mock_resolve.return_value = None
        main()
        mock_resolve.assert_called_once_with(mock_get_jira.return_value, 'CPP', 'KTLO')


if __name__ == '__main__':
    unittest.main()
