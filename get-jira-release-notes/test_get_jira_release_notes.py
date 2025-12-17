#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for get_jira_release_notes.py
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO

# Add the current directory to the path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from get_jira_release_notes import (
    get_jira_instance,
    get_project_name,
    get_version_id,
    get_issues_for_release,
    format_notes_as_markdown,
    format_notes_as_jira_markup,
    generate_release_notes_url,
    main
)
from jira.exceptions import JIRAError


class TestGetJiraReleaseNotes(unittest.TestCase):

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

    # noinspection DuplicatedCode
    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('get_jira_release_notes.JIRA')
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
    @patch('get_jira_release_notes.JIRA')
    def test_get_jira_instance_auth_failure(self, mock_jira_class):
        """Test JIRA instance creation with authentication failure."""
        mock_jira_class.side_effect = JIRAError(status_code=401, text="Unauthorized")

        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://prod.com')
        self.assertEqual(cm.exception.code, 1)

    def test_get_project_name_success(self):
        """Test successful project name retrieval."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_jira.project.return_value = mock_project

        result = get_project_name(mock_jira, 'TEST')

        self.assertEqual(result, "Test Project")
        mock_jira.project.assert_called_once_with('TEST')

    def test_get_project_name_failure(self):
        """Test project name retrieval with project not found."""
        mock_jira = Mock()
        mock_jira.project.side_effect = JIRAError(status_code=404, text="Project not found")

        with self.assertRaises(SystemExit) as cm:
            get_project_name(mock_jira, 'NONEXISTENT')
        self.assertEqual(cm.exception.code, 1)

    def test_get_version_id_success(self):
        """Test successful version ID retrieval."""
        mock_jira = Mock()
        mock_version1 = Mock()
        mock_version1.name = "1.0.0"
        mock_version1.id = "10001"
        mock_version2 = Mock()
        mock_version2.name = "1.1.0"
        mock_version2.id = "10002"
        mock_jira.project_versions.return_value = [mock_version1, mock_version2]

        result = get_version_id(mock_jira, 'TEST', '1.1.0')

        self.assertEqual(result, "10002")
        mock_jira.project_versions.assert_called_once_with('TEST')

    def test_get_version_id_not_found(self):
        """Test version ID retrieval when version not found."""
        mock_jira = Mock()
        mock_version = Mock()
        mock_version.name = "1.0.0"
        mock_version.id = "10001"
        mock_jira.project_versions.return_value = [mock_version]

        with self.assertRaises(SystemExit) as cm:
            get_version_id(mock_jira, 'TEST', '2.0.0')
        self.assertEqual(cm.exception.code, 1)

    def test_get_version_id_project_not_found(self):
        """Test version ID retrieval with project not found."""
        mock_jira = Mock()
        mock_jira.project_versions.side_effect = JIRAError(status_code=404, text="Project not found")

        with self.assertRaises(SystemExit) as cm:
            get_version_id(mock_jira, 'NONEXISTENT', '1.0.0')
        self.assertEqual(cm.exception.code, 1)

    def test_get_issues_for_release_success(self):
        """Test successful issues retrieval."""
        mock_jira = Mock()
        mock_issue1 = Mock()
        mock_issue1.key = "TEST-1"
        mock_issue2 = Mock()
        mock_issue2.key = "TEST-2"
        mock_jira.search_issues.return_value = [mock_issue1, mock_issue2]

        result = get_issues_for_release(mock_jira, 'TEST', '1.0.0')

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].key, "TEST-1")
        self.assertEqual(result[1].key, "TEST-2")
        expected_jql = 'project = "TEST" AND fixVersion = "1.0.0" ORDER BY issuetype ASC, key ASC'
        mock_jira.search_issues.assert_called_once_with(expected_jql, maxResults=False)

    def test_get_issues_for_release_failure(self):
        """Test issues retrieval with JIRA error."""
        mock_jira = Mock()
        mock_jira.search_issues.side_effect = JIRAError(status_code=400, text="Bad request")

        with self.assertRaises(SystemExit) as cm:
            get_issues_for_release(mock_jira, 'TEST', '1.0.0')
        self.assertEqual(cm.exception.code, 1)

    def test_format_notes_as_markdown_empty_issues(self):
        """Test Markdown formatting with no issues."""
        result = format_notes_as_markdown([], 'https://jira.com', 'Test Project', '1.0.0', [])

        expected = "# Release notes - Test Project - 1.0.0\n\nNo issues found for this release."
        self.assertEqual(result, expected)

    def test_format_notes_as_markdown_with_issues(self):
        """Test Markdown formatting with issues."""
        mock_issue1 = Mock()
        mock_issue1.key = "TEST-1"
        mock_issue1.fields.summary = "Fix bug in login"
        mock_issue1.fields.issuetype.name = "Bug"

        mock_issue2 = Mock()
        mock_issue2.key = "TEST-2"
        mock_issue2.fields.summary = "Add new feature"
        mock_issue2.fields.issuetype.name = "New Feature"

        issues = [mock_issue1, mock_issue2]
        category_order = ["New Feature", "Bug"]

        result = format_notes_as_markdown(issues, 'https://jira.com', 'Test Project', '1.0.0', category_order)

        expected_lines = [
            "# Release notes - Test Project - 1.0.0",
            "",
            "### New Feature",
            "[TEST-2](https://jira.com/browse/TEST-2) Add new feature",
            "",
            "### Bug",
            "[TEST-1](https://jira.com/browse/TEST-1) Fix bug in login",
            ""
        ]
        expected = "\n".join(expected_lines)
        self.assertEqual(result, expected)

    def test_format_notes_as_markdown_jira_url_trailing_slash(self):
        """Test Markdown formatting handles trailing slashes in URL."""
        mock_issue = Mock()
        mock_issue.key = "TEST-1"
        mock_issue.fields.summary = "Test issue"
        mock_issue.fields.issuetype.name = "Bug"

        result = format_notes_as_markdown([mock_issue], 'https://jira.com/', 'Test Project', '1.0.0', ["Bug"])

        self.assertIn("[TEST-1](https://jira.com/browse/TEST-1)", result)

    def test_generate_release_notes_url(self):
        """Test release notes URL generation."""
        url = generate_release_notes_url('https://jira.com', 'TEST', '10001')
        expected = 'https://jira.com/projects/TEST/versions/10001/tab/release-report-all-issues'
        self.assertEqual(url, expected)

    def test_generate_release_notes_url_trailing_slash(self):
        """Test release notes URL generation with trailing slash."""
        url = generate_release_notes_url('https://jira.com/', 'TEST', '10001')
        expected = 'https://jira.com/projects/TEST/versions/10001/tab/release-report-all-issues'
        self.assertEqual(url, expected)

    # noinspection PyUnusedLocal
    @patch('sys.argv', [
        'get_jira_release_notes.py',
        '--project-key', 'TEST',
        '--version-name', '1.0.0',
        '--jira-url', 'https://test.jira.com'
    ])
    @patch('get_jira_release_notes.get_jira_instance')
    @patch('get_jira_release_notes.get_version_id')
    @patch('get_jira_release_notes.get_project_name')
    @patch('get_jira_release_notes.get_issues_for_release')
    @patch('get_jira_release_notes.format_notes_as_markdown')
    @patch('get_jira_release_notes.format_notes_as_jira_markup')
    @patch('get_jira_release_notes.generate_release_notes_url')
    @patch('sys.stderr', new_callable=StringIO)
    @patch('builtins.print')
    def test_main_success(self, mock_print, mock_stderr, mock_generate_url, mock_format_jira_markup, mock_format_notes,
                          mock_get_issues, mock_get_project_name, mock_get_version_id, mock_get_jira):
        """Test successful main function execution."""
        # Setup mocks
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira
        mock_get_version_id.return_value = "10001"
        mock_get_project_name.return_value = "Test Project"
        mock_get_issues.return_value = []
        mock_format_notes.return_value = "# Release notes - Test Project - 1.0.0\n\nNo issues found."
        mock_format_jira_markup.return_value = "h1. Release notes - Test Project - 1.0.0\n\nNo issues found."
        mock_generate_url.return_value = "https://test.jira.com/projects/TEST/versions/10001/tab/release-report-all-issues"

        main()

        # Verify all functions were called correctly
        mock_get_jira.assert_called_once_with('https://test.jira.com')
        mock_get_version_id.assert_called_once_with(mock_jira, 'TEST', '1.0.0')
        mock_generate_url.assert_called_once_with('https://test.jira.com', 'TEST', '10001')
        mock_get_project_name.assert_called_once_with(mock_jira, 'TEST')
        mock_get_issues.assert_called_once_with(mock_jira, 'TEST', '1.0.0')

        # Verify both format functions were called
        mock_format_notes.assert_called_once()
        mock_format_jira_markup.assert_called_once()

        # Verify expected output format
        print_calls = mock_print.call_args_list
        self.assertEqual(len(print_calls), 9)  # URL + ID + markdown start/content/end + jira start/content/end
        # Check the main outputs
        self.assertEqual(print_calls[1][0][0], "jira-release-url=https://test.jira.com/projects/TEST/versions/10001/tab/release-report-all-issues")
        self.assertEqual(print_calls[2][0][0], "jira-release-id=10001")
        self.assertEqual(print_calls[3][0][0], "release-notes<<EOF")
        self.assertEqual(print_calls[4][0][0], "# Release notes - Test Project - 1.0.0\n\nNo issues found.")
        self.assertEqual(print_calls[5][0][0], "EOF")
        self.assertEqual(print_calls[6][0][0], "jira-release-notes<<EOF")
        self.assertEqual(print_calls[7][0][0], "h1. Release notes - Test Project - 1.0.0\n\nNo issues found.")
        self.assertEqual(print_calls[8][0][0], "EOF")

    @patch('sys.argv', [
        'get_jira_release_notes.py',
        '--project-key', 'TEST',
        '--version-name', '1.0.0',
        '--issue-types', 'Bug,New Feature',
        '--jira-url', 'https://test.jira.com'
    ])
    @patch('get_jira_release_notes.get_jira_instance')
    @patch('get_jira_release_notes.get_version_id')
    @patch('get_jira_release_notes.get_project_name')
    @patch('get_jira_release_notes.get_issues_for_release')
    @patch('get_jira_release_notes.format_notes_as_markdown')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_custom_issue_types(self, mock_stderr, mock_format_notes, mock_get_issues,
                                    mock_get_project_name, mock_get_version_id, mock_get_jira):
        """Test main function with custom issue types."""
        # Setup mocks
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira
        mock_get_version_id.return_value = "10001"
        mock_get_project_name.return_value = "Test Project"
        mock_get_issues.return_value = []
        mock_format_notes.return_value = "# Release notes"

        main()

        # Verify custom issue types were passed to format_notes_as_markdown
        mock_format_notes.assert_called_once()
        args = mock_format_notes.call_args[0]
        category_order = args[4]  # Fifth argument is category_order
        self.assertEqual(category_order, ['Bug', 'New Feature'])

        # Verify stderr shows custom issue types
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Using custom issue type order: ['Bug', 'New Feature']", stderr_output)

    @patch('sys.argv', [
        'get_jira_release_notes.py',
        '--project-key', 'TEST',
        '--version-name', '1.0.0',
        '--jira-url', 'https://test.jira.com'
    ])
    @patch('get_jira_release_notes.get_jira_instance')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_default_issue_types(self, mock_stderr, mock_get_jira):
        """Test main function with default issue types."""
        # Setup mocks to cause early exit after checking issue types
        mock_get_jira.side_effect = SystemExit(0)

        with self.assertRaises(SystemExit):
            main()

        # Verify stderr shows default issue types
        stderr_output = mock_stderr.getvalue()
        expected_default = ["New Feature", "False Positive", "False Negative", "Bug", "Improvement"]
        self.assertIn(f"Using default issue type order: {expected_default}", stderr_output)

    @patch('sys.argv', [
        'get_jira_release_notes.py',
        '--project-key', 'TEST',
        '--version-name', '1.0.0',
        '--jira-url', 'https://test.jira.com'
    ])
    @patch('get_jira_release_notes.get_jira_instance')
    def test_main_jira_connection_failure(self, mock_get_jira):
        """Test main function with JIRA connection failure."""
        mock_get_jira.side_effect = SystemExit(1)

        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)

    @patch('sys.argv', [
        'get_jira_release_notes.py',
        '--project-key', 'TEST',
        '--version-name', '1.0.0',
        '--jira-url', 'https://test.jira.com'
    ])
    @patch('get_jira_release_notes.get_jira_instance')
    @patch('get_jira_release_notes.get_version_id')
    def test_main_version_not_found(self, mock_get_version_id, mock_get_jira):
        """Test main function when version is not found."""
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira
        mock_get_version_id.side_effect = SystemExit(1)

        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)

    def test_format_notes_as_markdown_mixed_issue_types(self):
        """Test Markdown formatting with mixed issue types and category ordering."""
        # Create mock issues with different types
        mock_issue1 = Mock()
        mock_issue1.key = "TEST-1"
        mock_issue1.fields.summary = "Fix critical bug"
        mock_issue1.fields.issuetype.name = "Bug"

        mock_issue2 = Mock()
        mock_issue2.key = "TEST-2"
        mock_issue2.fields.summary = "Add dashboard feature"
        mock_issue2.fields.issuetype.name = "New Feature"

        mock_issue3 = Mock()
        mock_issue3.key = "TEST-3"
        mock_issue3.fields.summary = "Improve performance"
        mock_issue3.fields.issuetype.name = "Improvement"

        mock_issue4 = Mock()
        mock_issue4.key = "TEST-4"
        mock_issue4.fields.summary = "Another bug fix"
        mock_issue4.fields.issuetype.name = "Bug"

        issues = [mock_issue1, mock_issue2, mock_issue3, mock_issue4]
        category_order = ["New Feature", "Bug", "Improvement"]

        result = format_notes_as_markdown(issues, 'https://jira.com', 'Test Project', '1.0.0', category_order)

        # Verify the structure and ordering
        self.assertIn("# Release notes - Test Project - 1.0.0", result)
        self.assertIn("### New Feature", result)
        self.assertIn("### Bug", result)
        self.assertIn("### Improvement", result)

        # Verify issues appear in correct sections
        self.assertIn("[TEST-2](https://jira.com/browse/TEST-2) Add dashboard feature", result)
        self.assertIn("[TEST-1](https://jira.com/browse/TEST-1) Fix critical bug", result)
        self.assertIn("[TEST-4](https://jira.com/browse/TEST-4) Another bug fix", result)
        self.assertIn("[TEST-3](https://jira.com/browse/TEST-3) Improve performance", result)

        # Verify New Feature section comes before Bug section
        new_feature_pos = result.find("### New Feature")
        bug_pos = result.find("### Bug")
        improvement_pos = result.find("### Improvement")
        self.assertLess(new_feature_pos, bug_pos)
        self.assertLess(bug_pos, improvement_pos)

    def test_format_notes_as_jira_markup_empty_issues(self):
        """Test Jira markup formatting with no issues."""
        result = format_notes_as_jira_markup([], 'https://jira.com', 'Test Project', '1.0.0', [])

        expected = "h1. Release notes - Test Project - 1.0.0\n\nNo issues found for this release."
        self.assertEqual(result, expected)

    def test_format_notes_as_jira_markup_with_issues(self):
        """Test Jira markup formatting with issues."""
        mock_issue1 = Mock()
        mock_issue1.key = "TEST-1"
        mock_issue1.fields.summary = "Fix bug in login"
        mock_issue1.fields.issuetype.name = "Bug"

        mock_issue2 = Mock()
        mock_issue2.key = "TEST-2"
        mock_issue2.fields.summary = "Add new feature"
        mock_issue2.fields.issuetype.name = "New Feature"

        issues = [mock_issue1, mock_issue2]
        category_order = ["New Feature", "Bug"]

        result = format_notes_as_jira_markup(issues, 'https://jira.com', 'Test Project', '1.0.0', category_order)

        expected_lines = [
            "h1. Release notes - Test Project - 1.0.0",
            "",
            "h3. New Feature",
            "[TEST-2|https://jira.com/browse/TEST-2] Add new feature",
            "",
            "h3. Bug",
            "[TEST-1|https://jira.com/browse/TEST-1] Fix bug in login",
            ""
        ]
        expected = "\n".join(expected_lines)
        self.assertEqual(result, expected)

    def test_format_notes_as_jira_markup_jira_url_trailing_slash(self):
        """Test Jira markup formatting handles trailing slashes in URL."""
        mock_issue = Mock()
        mock_issue.key = "TEST-1"
        mock_issue.fields.summary = "Test issue"
        mock_issue.fields.issuetype.name = "Bug"

        result = format_notes_as_jira_markup([mock_issue], 'https://jira.com/', 'Test Project', '1.0.0', ["Bug"])

        self.assertIn("[TEST-1|https://jira.com/browse/TEST-1]", result)


if __name__ == '__main__':
    unittest.main()
