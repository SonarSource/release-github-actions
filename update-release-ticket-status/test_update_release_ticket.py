#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for update_release_ticket.py
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO

# Add the current directory to the path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_release_ticket import get_jira_instance, update_ticket_status, main
from jira.exceptions import JIRAError


class TestUpdateReleaseTicket(unittest.TestCase):

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
    @patch('update_release_ticket.JIRA')
    def test_get_jira_instance_success(self, mock_jira_class):
        """Test successful JIRA instance creation."""
        mock_jira = Mock()
        mock_jira_class.return_value = mock_jira

        result = get_jira_instance('https://prod.com')

        self.assertEqual(result, mock_jira)
        mock_jira_class.assert_called_once_with('https://prod.com', basic_auth=('test', 'token'), get_server_info=True)

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('update_release_ticket.JIRA')
    def test_get_jira_instance_auth_failure(self, mock_jira_class):
        """Test JIRA instance creation with authentication failure."""
        mock_jira_class.side_effect = JIRAError(status_code=401, text="Unauthorized")

        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://prod.com')
        self.assertEqual(cm.exception.code, 1)

    def test_update_ticket_status_success(self):
        """Test successful ticket status update."""
        mock_jira = Mock()
        mock_issue = Mock()
        mock_jira.issue.return_value = mock_issue

        # noinspection PyTypeChecker
        update_ticket_status(mock_jira, 'REL-123', 'Start Progress', None)

        mock_jira.issue.assert_called_once_with('REL-123')
        mock_jira.transition_issue.assert_called_once_with(mock_issue, 'Start Progress')
        mock_jira.assign_issue.assert_not_called()

    def test_update_ticket_status_with_assignee(self):
        """Test ticket status update with assignee change."""
        mock_jira = Mock()
        mock_issue = Mock()
        mock_jira.issue.return_value = mock_issue

        update_ticket_status(mock_jira, 'REL-123', 'Start Progress', 'test@example.com')

        mock_jira.issue.assert_called_once_with('REL-123')
        mock_jira.assign_issue.assert_called_once_with('REL-123', 'test@example.com')
        mock_jira.transition_issue.assert_called_once_with(mock_issue, 'Start Progress')

    def test_update_ticket_status_ticket_not_found(self):
        """Test handling of ticket not found error."""
        mock_jira = Mock()
        mock_jira.issue.side_effect = JIRAError(status_code=404, text="Not found")

        with self.assertRaises(SystemExit) as cm:
            # noinspection PyTypeChecker
            update_ticket_status(mock_jira, 'REL-999', 'Start Progress', None)
        self.assertEqual(cm.exception.code, 1)

    def test_update_ticket_status_assignee_error(self):
        """Test handling of assignee error."""
        mock_jira = Mock()
        mock_issue = Mock()
        mock_jira.issue.return_value = mock_issue
        mock_jira.assign_issue.side_effect = JIRAError(status_code=400, text="Invalid assignee")

        with self.assertRaises(SystemExit) as cm:
            update_ticket_status(mock_jira, 'REL-123', 'Start Progress', 'invalid@example.com')
        self.assertEqual(cm.exception.code, 1)

    # noinspection PyTypeChecker
    def test_update_ticket_status_transition_error(self):
        """Test handling of transition error."""
        mock_jira = Mock()
        mock_issue = Mock()
        mock_jira.issue.return_value = mock_issue
        mock_jira.transition_issue.side_effect = JIRAError(status_code=400, text="Invalid transition")

        with self.assertRaises(SystemExit) as cm:
            update_ticket_status(mock_jira, 'REL-123', 'Invalid Status', None)
        self.assertEqual(cm.exception.code, 1)

    # noinspection PyUnusedLocal
    @patch('sys.argv', [
        'update_release_ticket.py',
        '--ticket-key', 'REL-123',
        '--status', 'Start Progress',
        '--jira-url', 'https://test.jira.com'
    ])
    @patch('update_release_ticket.get_jira_instance')
    @patch('update_release_ticket.update_ticket_status')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_successful_update(self, mock_stderr, mock_stdout, mock_update_ticket, mock_get_jira):
        """Test successful ticket update through main function."""
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira

        main()

        # Verify get_jira_instance was called with correct URL
        mock_get_jira.assert_called_once_with('https://test.jira.com')

        # Verify update_ticket_status was called with correct parameters
        mock_update_ticket.assert_called_once_with(mock_jira, 'REL-123', 'Start Progress', None)

        # Verify success message in stderr
        stderr_output = mock_stderr.getvalue()
        self.assertIn('🎉 Successfully updated Jira ticket!', stderr_output)
        self.assertIn('Ticket Key: REL-123', stderr_output)
        self.assertIn('New Status: Start Progress', stderr_output)

    # noinspection PyUnusedLocal
    @patch('sys.argv', [
        'update_release_ticket.py',
        '--ticket-key', 'REL-456',
        '--status', 'Technical Release Done',
        '--assignee', 'user@example.com',
        '--jira-url', 'https://sandbox.jira.com'
    ])
    @patch('update_release_ticket.get_jira_instance')
    @patch('update_release_ticket.update_ticket_status')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_with_assignee(self, mock_stderr, mock_stdout, mock_update_ticket, mock_get_jira):
        """Test main function with assignee parameter."""
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira

        main()

        # Verify get_jira_instance was called with sandbox URL
        mock_get_jira.assert_called_once_with('https://sandbox.jira.com')

        # Verify update_ticket_status was called with assignee
        mock_update_ticket.assert_called_once_with(mock_jira, 'REL-456', 'Technical Release Done', 'user@example.com')

        # Verify success message includes assignee
        stderr_output = mock_stderr.getvalue()
        self.assertIn('🎉 Successfully updated Jira ticket!', stderr_output)
        self.assertIn('Ticket Key: REL-456', stderr_output)
        self.assertIn('New Status: Technical Release Done', stderr_output)
        self.assertIn('Assignee: user@example.com', stderr_output)

    @patch('sys.argv', [
        'update_release_ticket.py',
        '--ticket-key', 'REL-789',
        '--status', 'Invalid Status',
        '--jira-url', 'https://test.jira.com'
    ])
    def test_main_invalid_status(self):
        """Test main function with invalid status choice."""
        with self.assertRaises(SystemExit) as cm:
            main()
        # argparse exits with status 2 for invalid arguments
        self.assertEqual(cm.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
