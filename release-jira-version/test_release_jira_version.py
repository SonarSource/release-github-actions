#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for release_jira_version.py
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO

# Add the current directory to the path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from release_jira_version import get_jira_instance, main
from jira.exceptions import JIRAError


class TestReleaseJiraVersion(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_env = {
            'JIRA_USER': 'test_user',
            'JIRA_TOKEN': 'test_token'
        }

    @patch.dict(os.environ, {})
    def test_get_jira_instance_missing_credentials(self):
        """Test that get_jira_instance exits when credentials are missing."""
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://test.jira.com')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('release_jira_version.JIRA')
    def test_get_jira_instance_success(self, mock_jira_class):
        """Test successful JIRA instance creation."""
        mock_jira = Mock()
        mock_jira.server_info.return_value = {}
        mock_jira_class.return_value = mock_jira

        result = get_jira_instance('https://prod.com')

        self.assertEqual(result, mock_jira)
        mock_jira_class.assert_called_once_with('https://prod.com', basic_auth=('test', 'token'))
        mock_jira.server_info.assert_called_once()

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('release_jira_version.JIRA')
    def test_get_jira_instance_different_url(self, mock_jira_class):
        """Test JIRA instance creation with different URL."""
        mock_jira = Mock()
        mock_jira.server_info.return_value = {}
        mock_jira_class.return_value = mock_jira

        result = get_jira_instance('https://sandbox.com')

        self.assertEqual(result, mock_jira)
        mock_jira_class.assert_called_once_with('https://sandbox.com', basic_auth=('test', 'token'))

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('release_jira_version.JIRA')
    def test_get_jira_instance_auth_failure(self, mock_jira_class):
        """Test JIRA instance creation with authentication failure."""
        mock_jira_class.side_effect = JIRAError(status_code=401, text="Unauthorized")

        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://prod.com')
        self.assertEqual(cm.exception.code, 1)

    @patch('sys.argv', ['release_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0', '--jira-url', 'https://test.jira.com'])
    @patch('release_jira_version.get_jira_instance')
    @patch('sys.stderr', new_callable=StringIO)
    @patch('release_jira_version.datetime')
    def test_main_successful_version_release(self, mock_datetime, mock_stderr, mock_get_jira):
        """Test successful version release."""
        # Mock datetime
        mock_date = Mock()
        mock_date.today.return_value.strftime.return_value = '2025-08-15'
        mock_datetime.date = mock_date

        # Mock JIRA instance and version
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.name = '1.0.0'
        mock_version.released = False
        mock_version.update = Mock()

        # Mock project with the version
        mock_project = Mock()
        mock_project.versions = [mock_version]
        mock_jira.project.return_value = mock_project
        mock_get_jira.return_value = mock_jira

        main()

        # Verify get_jira_instance was called with the URL
        mock_get_jira.assert_called_once_with('https://test.jira.com')

        # Verify the project was fetched
        mock_jira.project.assert_called_once_with('TEST')

        # Verify the version was updated with release info
        mock_version.update.assert_called_once_with(released=True, releaseDate='2025-08-15')

        # Verify output
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Searching for version '1.0.0' in project 'TEST'", stderr_output)
        self.assertIn("Found version '1.0.0'. Releasing it now...", stderr_output)
        self.assertIn("✅ Successfully released version '1.0.0'.", stderr_output)

    @patch('sys.argv', ['release_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0', '--jira-url', 'https://test.jira.com'])
    @patch('release_jira_version.get_jira_instance')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_version_already_released(self, mock_stderr, mock_get_jira):
        """Test handling when version is already released."""
        # Mock JIRA instance and version
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.name = '1.0.0'
        mock_version.released = True

        # Mock project with the version
        mock_project = Mock()
        mock_project.versions = [mock_version]
        mock_jira.project.return_value = mock_project
        mock_get_jira.return_value = mock_jira

        main()

        # Verify the project was fetched
        mock_jira.project.assert_called_once_with('TEST')

        # Verify the version update was not called
        mock_version.update.assert_not_called()

        # Verify output
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Warning: Version '1.0.0' is already released. Skipping release step.", stderr_output)

    @patch('sys.argv', ['release_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0', '--jira-url', 'https://test.jira.com'])
    @patch('release_jira_version.get_jira_instance')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_version_not_found(self, mock_stderr, mock_get_jira):
        """Test handling when version is not found in project."""
        # Mock JIRA instance
        mock_jira = Mock()

        # Mock project with different versions
        mock_other_version = Mock()
        mock_other_version.name = '2.0.0'
        mock_project = Mock()
        mock_project.versions = [mock_other_version]
        mock_jira.project.return_value = mock_project
        mock_get_jira.return_value = mock_jira

        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)

        # Verify the project was fetched
        mock_jira.project.assert_called_once_with('TEST')

        # Verify output
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Error: Version '1.0.0' not found in project 'TEST'.", stderr_output)

    @patch('sys.argv', ['release_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0', '--jira-url', 'https://test.jira.com'])
    @patch('release_jira_version.get_jira_instance')
    @patch('sys.stderr', new_callable=StringIO)
    @patch('release_jira_version.datetime')
    def test_main_release_failure(self, mock_datetime, mock_stderr, mock_get_jira):
        """Test handling of JIRA errors during version release."""
        # Mock datetime
        mock_date = Mock()
        mock_date.today.return_value.strftime.return_value = '2025-08-15'
        mock_datetime.date = mock_date

        # Mock JIRA instance and version
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.name = '1.0.0'
        mock_version.released = False
        mock_version.update.side_effect = JIRAError(
            status_code=403,
            text="Forbidden: Insufficient permissions"
        )

        # Mock project with the version
        mock_project = Mock()
        mock_project.versions = [mock_version]
        mock_jira.project.return_value = mock_project
        mock_get_jira.return_value = mock_jira

        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)

        # Verify the version update was attempted
        mock_version.update.assert_called_once_with(released=True, releaseDate='2025-08-15')

        # Verify output
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Error: Failed to release version. Status: 403, Text: Forbidden: Insufficient permissions", stderr_output)

    @patch('sys.argv', ['release_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0', '--jira-url', 'https://sandbox.jira.com'])
    @patch('release_jira_version.get_jira_instance')
    def test_main_with_different_jira_url(self, mock_get_jira):
        """Test that different JIRA URL is passed correctly."""
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.name = '1.0.0'
        mock_version.released = True

        # Mock project with the version
        mock_project = Mock()
        mock_project.versions = [mock_version]
        mock_jira.project.return_value = mock_project
        mock_get_jira.return_value = mock_jira

        main()

        # Verify get_jira_instance was called with the sandbox URL
        mock_get_jira.assert_called_once_with('https://sandbox.jira.com')

    @patch('sys.argv', ['release_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0', '--jira-url', 'https://test.jira.com'])
    @patch('release_jira_version.get_jira_instance')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_project_fetch_failure(self, mock_stderr, mock_get_jira):
        """Test handling when project cannot be fetched."""
        # Mock JIRA instance
        mock_jira = Mock()
        mock_jira.project.side_effect = JIRAError(
            status_code=404,
            text="Project not found"
        )
        mock_get_jira.return_value = mock_jira

        with self.assertRaises(JIRAError):
            main()

        # Verify the project fetch was attempted
        mock_jira.project.assert_called_once_with('TEST')

    @patch('sys.argv', ['release_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0', '--jira-url', 'https://test.jira.com'])
    @patch('release_jira_version.get_jira_instance')
    @patch('sys.stderr', new_callable=StringIO)
    @patch('release_jira_version.datetime')
    def test_main_multiple_versions_with_same_name(self, mock_datetime, mock_stderr, mock_get_jira):
        """Test handling when multiple versions have the same name (edge case)."""
        # Mock datetime
        mock_date = Mock()
        mock_date.today.return_value.strftime.return_value = '2025-08-15'
        mock_datetime.date = mock_date

        # Mock JIRA instance and versions
        mock_jira = Mock()
        mock_version1 = Mock()
        mock_version1.name = '1.0.0'
        mock_version1.released = False
        mock_version1.update = Mock()

        mock_version2 = Mock()
        mock_version2.name = '1.0.0'
        mock_version2.released = True

        # Mock project with multiple versions (first one should be selected)
        mock_project = Mock()
        mock_project.versions = [mock_version1, mock_version2]
        mock_jira.project.return_value = mock_project
        mock_get_jira.return_value = mock_jira

        main()

        # Verify the first version was updated (first match is used)
        mock_version1.update.assert_called_once_with(released=True, releaseDate='2025-08-15')
        mock_version2.update.assert_not_called()


if __name__ == '__main__':
    unittest.main()
