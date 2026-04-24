#!/usr/bin/env python3
"""Unit tests for cleanup.py"""

import json
import tempfile
import unittest
from unittest.mock import Mock, patch, call
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cleanup import delete_issues, delete_version, main


class TestDeleteIssues(unittest.TestCase):
    """Tests for delete_issues."""

    def test_deletes_all_issues(self):
        """Should call delete() on each issue."""
        mock_jira = Mock()
        mock_issue1 = Mock()
        mock_issue2 = Mock()
        mock_jira.issue.side_effect = [mock_issue1, mock_issue2]

        delete_issues(mock_jira, ['SONARIAC-100', 'SONARIAC-101'])

        mock_issue1.delete.assert_called_once()
        mock_issue2.delete.assert_called_once()

    def test_ignores_missing_issues(self):
        """Should not fail when an issue does not exist (404)."""
        from jira.exceptions import JIRAError
        mock_jira = Mock()
        mock_jira.issue.side_effect = JIRAError(status_code=404, text="Not found")

        # Should not raise
        delete_issues(mock_jira, ['SONARIAC-999'])

    def test_ignores_other_jira_errors(self):
        """Should not fail on other Jira errors — cleanup must be idempotent."""
        from jira.exceptions import JIRAError
        mock_jira = Mock()
        mock_jira.issue.side_effect = JIRAError(status_code=403, text="Forbidden")

        # Should not raise
        delete_issues(mock_jira, ['SONARIAC-100'])

    def test_empty_list_is_noop(self):
        """Should handle an empty issue list gracefully."""
        mock_jira = Mock()
        delete_issues(mock_jira, [])
        mock_jira.issue.assert_not_called()


class TestDeleteVersion(unittest.TestCase):
    """Tests for delete_version."""

    def test_deletes_version_by_id(self):
        """Should fetch the version and delete it."""
        mock_jira = Mock()
        mock_version = Mock()
        mock_jira.version.return_value = mock_version

        delete_version(mock_jira, '12345')

        mock_jira.version.assert_called_once_with('12345')
        mock_version.delete.assert_called_once()

    def test_ignores_missing_version(self):
        """Should not fail when version does not exist."""
        from jira.exceptions import JIRAError
        mock_jira = Mock()
        mock_jira.version.side_effect = JIRAError(status_code=404, text="Not found")

        # Should not raise
        delete_version(mock_jira, '99999')

    def test_ignores_other_errors(self):
        """Should not fail on unexpected errors — cleanup must be idempotent."""
        mock_jira = Mock()
        mock_jira.version.side_effect = Exception("Unexpected error")

        # Should not raise
        delete_version(mock_jira, '12345')


class TestMain(unittest.TestCase):
    """Tests for the main function."""

    @patch('cleanup.get_jira_instance')
    @patch('sys.argv', [
        'cleanup.py',
        '--jira-url', 'https://sandbox.atlassian.net/',
        '--version-id', '12345',
        '--issue-keys', 'SONARIAC-100,SONARIAC-101,SONARIAC-102'
    ])
    def test_main_with_inline_args(self, mock_get_jira):
        """Main should parse inline arguments and clean up."""
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira
        mock_version = Mock()
        mock_jira.version.return_value = mock_version
        mock_issue = Mock()
        mock_jira.issue.return_value = mock_issue

        main()

        mock_get_jira.assert_called_once_with('https://sandbox.atlassian.net/')
        # Should have fetched 3 issues and 1 version
        self.assertEqual(mock_jira.issue.call_count, 3)
        mock_jira.version.assert_called_once_with('12345')

    @patch('cleanup.get_jira_instance')
    def test_main_with_state_file(self, mock_get_jira):
        """Main should read state from a JSON file."""
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira
        mock_version = Mock()
        mock_jira.version.return_value = mock_version
        mock_issue = Mock()
        mock_jira.issue.return_value = mock_issue

        state = {
            "version_id": "67890",
            "version_name": "99.42",
            "issue_keys": ["PROJ-1", "PROJ-2"]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(state, f)
            state_file = f.name

        try:
            with patch('sys.argv', [
                'cleanup.py',
                '--jira-url', 'https://sandbox.atlassian.net/',
                '--state-file', state_file
            ]):
                main()

            self.assertEqual(mock_jira.issue.call_count, 2)
            mock_jira.version.assert_called_once_with('67890')
        finally:
            os.unlink(state_file)

    @patch('cleanup.get_jira_instance')
    @patch('sys.argv', [
        'cleanup.py',
        '--jira-url', 'https://sandbox.atlassian.net/',
        '--version-id', '12345',
        '--issue-keys', ''
    ])
    def test_main_with_empty_issue_keys(self, mock_get_jira):
        """Main should handle empty issue keys gracefully."""
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira
        mock_version = Mock()
        mock_jira.version.return_value = mock_version

        main()

        mock_jira.issue.assert_not_called()
        mock_jira.version.assert_called_once_with('12345')

    @patch('cleanup.get_jira_instance')
    @patch('sys.argv', [
        'cleanup.py',
        '--jira-url', 'https://sandbox.atlassian.net/',
        '--version-id', '12345',
        '--issue-keys', 'SONARIAC-100'
    ])
    def test_main_always_exits_zero(self, mock_get_jira):
        """Main should always exit successfully (idempotent cleanup)."""
        from jira.exceptions import JIRAError
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira
        mock_jira.issue.side_effect = JIRAError(status_code=404, text="Not found")
        mock_jira.version.side_effect = JIRAError(status_code=404, text="Not found")

        # Should not raise
        main()

    @patch('cleanup.get_jira_instance')
    @patch('sys.argv', [
        'cleanup.py',
        '--jira-url', 'https://sandbox.atlassian.net/',
        '--state-file', '/nonexistent/path/state.json'
    ])
    def test_main_handles_missing_state_file(self, mock_get_jira):
        """Main should not crash when state file does not exist."""
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira

        # Should not raise — logs warning and continues
        main()

        # No issues or versions to delete
        mock_jira.issue.assert_not_called()
        mock_jira.version.assert_not_called()


if __name__ == '__main__':
    unittest.main()
