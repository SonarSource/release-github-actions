#!/usr/bin/env python3
"""Unit tests for jira_client.py"""

import unittest
from unittest.mock import Mock, patch
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jira_client import get_jira_instance, eprint


class TestEprint(unittest.TestCase):
    """Tests for the eprint helper."""

    @patch('sys.stderr')
    def test_eprint_writes_to_stderr(self, mock_stderr):
        eprint("hello")
        mock_stderr.write.assert_called()


class TestGetJiraInstance(unittest.TestCase):
    """Tests for get_jira_instance."""

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_credentials_raises(self):
        """Should raise SystemExit when JIRA_USER and JIRA_TOKEN are not set."""
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://test.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'user'}, clear=True)
    def test_missing_token_raises(self):
        """Should raise SystemExit when JIRA_TOKEN is not set."""
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://test.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_TOKEN': 'token'}, clear=True)
    def test_missing_user_raises(self):
        """Should raise SystemExit when JIRA_USER is not set."""
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://test.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'test_user', 'JIRA_TOKEN': 'test_token'})
    @patch('jira_client.JIRA')
    def test_successful_connection(self, mock_jira_class):
        """Should return a connected JIRA client."""
        mock_jira = Mock()
        mock_jira.server_info.return_value = {}
        mock_jira_class.return_value = mock_jira

        result = get_jira_instance('https://test.atlassian.net/')

        self.assertEqual(result, mock_jira)
        mock_jira_class.assert_called_once_with(
            'https://test.atlassian.net/',
            basic_auth=('test_user', 'test_token')
        )
        mock_jira.server_info.assert_called_once()

    @patch.dict(os.environ, {'JIRA_USER': 'test_user', 'JIRA_TOKEN': 'bad_token'})
    @patch('jira_client.JIRA')
    def test_auth_failure_raises(self, mock_jira_class):
        """Should raise SystemExit on authentication failure."""
        from jira.exceptions import JIRAError
        mock_jira_class.side_effect = JIRAError(status_code=401, text="Unauthorized")

        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://test.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'test_user', 'JIRA_TOKEN': 'test_token'})
    @patch('jira_client.JIRA')
    def test_unexpected_error_raises(self, mock_jira_class):
        """Should raise SystemExit on unexpected errors."""
        mock_jira_class.side_effect = Exception("Connection refused")

        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://test.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
