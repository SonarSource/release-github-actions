#!/usr/bin/env python3
"""Unit tests for setup.py"""

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import Mock, patch, call

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from setup import create_test_version, create_test_issues, main, write_state
from config import ISSUE_TYPES


class TestCreateTestVersion(unittest.TestCase):
    """Tests for create_test_version."""

    def test_creates_version_with_correct_name(self):
        """Should create a version named 99.<run_id>."""
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.id = '12345'
        mock_version.name = '99.42'
        mock_jira.create_version.return_value = mock_version

        result = create_test_version(mock_jira, 'SONARIAC', '42')

        mock_jira.create_version.assert_called_once_with(
            name='99.42', project='SONARIAC'
        )
        self.assertEqual(result.id, '12345')
        self.assertEqual(result.name, '99.42')

    def test_raises_on_jira_error(self):
        """Should propagate JIRAError when version creation fails."""
        from jira.exceptions import JIRAError
        mock_jira = Mock()
        mock_jira.create_version.side_effect = JIRAError(
            status_code=400, text="Bad request"
        )

        with self.assertRaises(JIRAError):
            create_test_version(mock_jira, 'SONARIAC', '42')


class TestCreateTestIssues(unittest.TestCase):
    """Tests for create_test_issues."""

    def test_creates_three_issues(self):
        """Should create one issue per ISSUE_TYPE."""
        mock_jira = Mock()
        mock_issues = []
        for i, issue_type in enumerate(ISSUE_TYPES):
            mock_issue = Mock()
            mock_issue.key = f'SONARIAC-{100 + i}'
            mock_issues.append(mock_issue)
        mock_jira.create_issue.side_effect = mock_issues

        mock_version = Mock()
        mock_version.name = '99.42'

        result = create_test_issues(mock_jira, 'SONARIAC', mock_version, '42')

        self.assertEqual(len(result), len(ISSUE_TYPES))
        self.assertEqual(mock_jira.create_issue.call_count, len(ISSUE_TYPES))

    def test_calls_on_issue_created_after_each_issue(self):
        """Should invoke the callback after each successful issue creation."""
        mock_jira = Mock()
        mock_issues = []
        for i in range(len(ISSUE_TYPES)):
            mock_issue = Mock()
            mock_issue.key = f'SONARIAC-{100 + i}'
            mock_issues.append(mock_issue)
        mock_jira.create_issue.side_effect = mock_issues

        mock_version = Mock()
        mock_version.name = '99.42'

        callback_issues = []
        create_test_issues(mock_jira, 'SONARIAC', mock_version, '42',
                           on_issue_created=lambda issue: callback_issues.append(issue.key))

        self.assertEqual(len(callback_issues), len(ISSUE_TYPES))

        # Verify each issue was created with correct fields
        for i, issue_type in enumerate(ISSUE_TYPES):
            call_args = mock_jira.create_issue.call_args_list[i]
            fields = call_args[1]['fields']
            self.assertEqual(fields['project'], 'SONARIAC')
            self.assertEqual(fields['issuetype']['name'], issue_type)
            self.assertIn('42', fields['summary'])
            self.assertEqual(fields['fixVersions'], [{'name': '99.42'}])

    def test_issue_summaries_include_type_and_run_id(self):
        """Each issue summary should include the issue type and run ID."""
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.key = 'SONARIAC-100'
        mock_jira.create_issue.return_value = mock_issue

        mock_version = Mock()
        mock_version.name = '99.42'

        create_test_issues(mock_jira, 'SONARIAC', mock_version, '42')

        for i, issue_type in enumerate(ISSUE_TYPES):
            call_args = mock_jira.create_issue.call_args_list[i]
            summary = call_args[1]['fields']['summary']
            self.assertIn(issue_type, summary)
            self.assertIn('42', summary)


class TestMain(unittest.TestCase):
    """Tests for the main function."""

    @patch('setup.write_state')
    @patch('setup.get_jira_instance')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', [
        'setup.py',
        '--project-key', 'SONARIAC',
        '--run-id', '42',
        '--jira-url', 'https://sandbox.atlassian.net/'
    ])
    def test_main_outputs_json(self, mock_stdout, mock_get_jira, mock_write_state):
        """Main should print valid JSON with version_id, version_name, issue_keys."""
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.id = '12345'
        mock_version.name = '99.42'
        mock_jira.create_version.return_value = mock_version

        mock_issues = []
        for i in range(len(ISSUE_TYPES)):
            mock_issue = Mock()
            mock_issue.key = f'SONARIAC-{100 + i}'
            mock_issues.append(mock_issue)
        mock_jira.create_issue.side_effect = mock_issues

        mock_get_jira.return_value = mock_jira

        main()

        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(output['version_id'], '12345')
        self.assertEqual(output['version_name'], '99.42')
        self.assertEqual(len(output['issue_keys']), len(ISSUE_TYPES))
        for key in output['issue_keys']:
            self.assertTrue(key.startswith('SONARIAC-'))

    @patch('setup.write_state')
    @patch('setup.get_jira_instance')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', [
        'setup.py',
        '--project-key', 'SONARIAC',
        '--run-id', '42',
        '--jira-url', 'https://sandbox.atlassian.net/'
    ])
    def test_main_writes_partial_state_before_issues(self, mock_stdout, mock_get_jira, mock_write_state):
        """Main should write state incrementally: once with empty keys, then after each issue."""
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.id = '12345'
        mock_version.name = '99.42'
        mock_jira.create_version.return_value = mock_version

        mock_issues = []
        for i in range(len(ISSUE_TYPES)):
            mock_issue = Mock()
            mock_issue.key = f'SONARIAC-{100 + i}'
            mock_issues.append(mock_issue)
        mock_jira.create_issue.side_effect = mock_issues

        mock_get_jira.return_value = mock_jira

        # Capture each call's state snapshot (the dict is mutated in-place)
        snapshots = []
        mock_write_state.side_effect = lambda s, _f: snapshots.append(list(s['issue_keys']))

        main()

        # First write: version created, no issues yet
        self.assertEqual(snapshots[0], [])

        # Subsequent writes: one issue added per call
        for i in range(1, len(ISSUE_TYPES) + 1):
            self.assertEqual(len(snapshots[i]), i)

    @patch('setup.write_state')
    @patch('setup.get_jira_instance')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', [
        'setup.py',
        '--project-key', 'TESTPROJ',
        '--run-id', '999',
        '--jira-url', 'https://sandbox.atlassian.net/'
    ])
    def test_main_uses_provided_project_key(self, mock_stdout, mock_get_jira, mock_write_state):
        """Main should use the project key from arguments."""
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.id = '67890'
        mock_version.name = '99.999'
        mock_jira.create_version.return_value = mock_version

        mock_issue = Mock()
        mock_issue.key = 'TESTPROJ-1'
        mock_jira.create_issue.return_value = mock_issue

        mock_get_jira.return_value = mock_jira

        main()

        mock_jira.create_version.assert_called_once_with(
            name='99.999', project='TESTPROJ'
        )


    @patch('setup.write_state')
    @patch('setup.get_jira_instance')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_uses_custom_state_file(self, mock_stdout, mock_get_jira, mock_write_state):
        """Main should pass --state-file path to write_state."""
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.id = '12345'
        mock_version.name = '99.42'
        mock_jira.create_version.return_value = mock_version
        mock_issue = Mock()
        mock_issue.key = 'SONARIAC-100'
        mock_jira.create_issue.return_value = mock_issue
        mock_get_jira.return_value = mock_jira

        custom_path = '/tmp/custom-state.json'
        with patch('sys.argv', [
            'setup.py',
            '--project-key', 'SONARIAC',
            '--run-id', '42',
            '--jira-url', 'https://sandbox.atlassian.net/',
            '--state-file', custom_path,
        ]):
            main()

        for call_args in mock_write_state.call_args_list:
            self.assertEqual(call_args[0][1], custom_path)


class TestWriteState(unittest.TestCase):
    """Tests for write_state."""

    def test_writes_state_to_file(self):
        """write_state should serialize state as JSON to the given path."""
        state = {"version_id": "123", "version_name": "99.42", "issue_keys": ["PROJ-1"]}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        self.addCleanup(os.remove, state_file)

        write_state(state, state_file)

        with open(state_file) as f:
            loaded = json.load(f)
        self.assertEqual(loaded, state)


if __name__ == '__main__':
    unittest.main()
