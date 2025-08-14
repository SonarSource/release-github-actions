#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for create_jira_version.py
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO

# Add the current directory to the path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from create_jira_version import get_jira_instance, main
from jira.exceptions import JIRAError


class TestCreateJiraVersion(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_env = {
            'JIRA_USER': 'test_user',
            'JIRA_TOKEN': 'test_token',
            'JIRA_PROD_URL': 'https://prod.jira.com',
            'JIRA_SANDBOX_URL': 'https://sandbox.jira.com'
        }

    @patch.dict(os.environ, {})
    def test_get_jira_instance_missing_credentials(self):
        """Test that get_jira_instance exits when credentials are missing."""
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance()
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token', 'JIRA_PROD_URL': 'https://prod.com'})
    @patch('create_jira_version.JIRA')
    def test_get_jira_instance_success(self, mock_jira_class):
        """Test successful JIRA instance creation."""
        mock_jira = Mock()
        mock_jira.server_info.return_value = {}
        mock_jira_class.return_value = mock_jira

        result = get_jira_instance()

        self.assertEqual(result, mock_jira)
        mock_jira_class.assert_called_once_with('https://prod.com', basic_auth=('test', 'token'))
        mock_jira.server_info.assert_called_once()

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token', 'JIRA_SANDBOX_URL': 'https://sandbox.com'})
    @patch('create_jira_version.JIRA')
    def test_get_jira_instance_sandbox(self, mock_jira_class):
        """Test JIRA instance creation with sandbox URL."""
        mock_jira = Mock()
        mock_jira.server_info.return_value = {}
        mock_jira_class.return_value = mock_jira

        result = get_jira_instance(use_sandbox=True)

        self.assertEqual(result, mock_jira)
        mock_jira_class.assert_called_once_with('https://sandbox.com', basic_auth=('test', 'token'))

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token', 'JIRA_PROD_URL': 'https://prod.com'})
    @patch('create_jira_version.JIRA')
    def test_get_jira_instance_auth_failure(self, mock_jira_class):
        """Test JIRA instance creation with authentication failure."""
        mock_jira_class.side_effect = JIRAError(status_code=401, text="Unauthorized")

        with self.assertRaises(SystemExit) as cm:
            get_jira_instance()
        self.assertEqual(cm.exception.code, 1)

    @patch('sys.argv', ['create_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0'])
    @patch('create_jira_version.get_jira_instance')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_successful_version_creation(self, mock_stderr, mock_stdout, mock_get_jira):
        """Test successful version creation."""
        # Mock JIRA instance and version
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.id = '12345'
        mock_version.name = '1.0.0'
        mock_jira.create_version.return_value = mock_version
        mock_get_jira.return_value = mock_jira

        main()

        # Verify the version was created with correct parameters
        mock_jira.create_version.assert_called_once_with(name='1.0.0', project='TEST')

        # Verify output
        stdout_output = mock_stdout.getvalue()
        self.assertIn('new_version_id=12345', stdout_output)
        self.assertIn('new_version_name=1.0.0', stdout_output)

        stderr_output = mock_stderr.getvalue()
        self.assertIn("Try to create new version '1.0.0'", stderr_output)
        self.assertIn("✅ Successfully created new version '1.0.0'", stderr_output)

    @patch('sys.argv', ['create_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0'])
    @patch('create_jira_version.get_jira_instance')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_version_already_exists(self, mock_stderr, mock_stdout, mock_get_jira):
        """Test handling when version already exists."""
        # Mock JIRA instance
        mock_jira = Mock()

        # Mock the create_version to raise JIRAError for existing version
        mock_jira.create_version.side_effect = JIRAError(
            status_code=400,
            text="A version with this name already exists in this project."
        )

        # Mock project and existing version
        mock_project = Mock()
        mock_existing_version = Mock()
        mock_existing_version.id = '67890'
        mock_existing_version.name = '1.0.0'
        mock_project.versions = [mock_existing_version]
        mock_jira.project.return_value = mock_project

        mock_get_jira.return_value = mock_jira

        main()

        # Verify the version creation was attempted
        mock_jira.create_version.assert_called_once_with(name='1.0.0', project='TEST')

        # Verify project was fetched to get existing version
        mock_jira.project.assert_called_once_with('TEST')

        # Verify output
        stdout_output = mock_stdout.getvalue()
        self.assertIn('new_version_id=67890', stdout_output)
        self.assertIn('new_version_name=1.0.0', stdout_output)

        stderr_output = mock_stderr.getvalue()
        self.assertIn("Warning: Version '1.0.0' already exists. Skipping creation.", stderr_output)

    @patch('sys.argv', ['create_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0'])
    @patch('create_jira_version.get_jira_instance')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_version_exists_but_not_found(self, mock_stderr, mock_get_jira):
        """Test handling when version exists but cannot be found in project versions."""
        # Mock JIRA instance
        mock_jira = Mock()

        # Mock the create_version to raise JIRAError for existing version
        mock_jira.create_version.side_effect = JIRAError(
            status_code=400,
            text="A version with this name already exists in this project."
        )

        # Mock project with no matching versions
        mock_project = Mock()
        mock_other_version = Mock()
        mock_other_version.name = '2.0.0'
        mock_project.versions = [mock_other_version]
        mock_jira.project.return_value = mock_project

        mock_get_jira.return_value = mock_jira

        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)

        stderr_output = mock_stderr.getvalue()
        self.assertIn("Error: Could not find existing version '1.0.0' in project.", stderr_output)

    @patch('sys.argv', ['create_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0'])
    @patch('create_jira_version.get_jira_instance')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_other_jira_error(self, mock_stderr, mock_get_jira):
        """Test handling of other JIRA errors."""
        # Mock JIRA instance
        mock_jira = Mock()

        # Mock the create_version to raise a different JIRAError
        mock_jira.create_version.side_effect = JIRAError(
            status_code=500,
            text="Internal server error"
        )

        mock_get_jira.return_value = mock_jira

        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)

        stderr_output = mock_stderr.getvalue()
        self.assertIn("Error: Failed to create new version. Status: 500, Text: Internal server error", stderr_output)

    @patch('sys.argv', ['create_jira_version.py', '--project-key', 'TEST', '--version-name', '1.0.0', '--use-sandbox'])
    @patch('create_jira_version.get_jira_instance')
    def test_main_with_sandbox_flag(self, mock_get_jira):
        """Test that sandbox flag is passed correctly."""
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.id = '12345'
        mock_version.name = '1.0.0'
        mock_jira.create_version.return_value = mock_version
        mock_get_jira.return_value = mock_jira

        main()

        # Verify get_jira_instance was called with use_sandbox=True
        mock_get_jira.assert_called_once_with(True)


if __name__ == '__main__':
    unittest.main()
