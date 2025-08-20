#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for create_integration_ticket.py
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO

# Add the current directory to the path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from create_integration_ticket import (
    get_jira_instance, validate_release_ticket, create_integration_ticket,
    link_tickets, main
)
from jira.exceptions import JIRAError


class TestCreateIntegrationTicket(unittest.TestCase):

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
            get_jira_instance('https://sonarsource.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('create_integration_ticket.JIRA')
    def test_get_jira_instance_success_prod(self, mock_jira_class):
        """Test successful JIRA instance creation for production."""
        mock_jira = Mock()
        mock_jira_class.return_value = mock_jira

        jira_client = get_jira_instance('https://sonarsource.atlassian.net/')

        self.assertEqual(jira_client, mock_jira)
        mock_jira_class.assert_called_once_with(
            'https://sonarsource.atlassian.net/',
            basic_auth=('test', 'token'),
            get_server_info=True
        )

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('create_integration_ticket.JIRA')
    def test_get_jira_instance_success_sandbox(self, mock_jira_class):
        """Test successful JIRA instance creation for sandbox."""
        mock_jira = Mock()
        mock_jira_class.return_value = mock_jira

        jira_client = get_jira_instance('https://sonarsource-sandbox-608.atlassian.net/')

        self.assertEqual(jira_client, mock_jira)
        mock_jira_class.assert_called_once_with(
            'https://sonarsource-sandbox-608.atlassian.net/',
            basic_auth=('test', 'token'),
            get_server_info=True
        )

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('create_integration_ticket.JIRA')
    def test_get_jira_instance_auth_failure(self, mock_jira_class):
        """Test JIRA instance creation with authentication failure."""
        mock_jira_class.side_effect = JIRAError(status_code=401, text="Unauthorized")

        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://sonarsource.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('create_integration_ticket.JIRA')
    def test_get_jira_instance_unexpected_error(self, mock_jira_class):
        """Test JIRA instance creation with unexpected error."""
        mock_jira_class.side_effect = Exception("Unexpected error")

        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://sonarsource.atlassian.net/')
        self.assertEqual(cm.exception.code, 1)

    def test_validate_release_ticket_success(self):
        """Test successful release ticket validation."""
        mock_jira = Mock()
        mock_ticket = Mock()
        mock_ticket.key = 'REL-123'
        mock_ticket.fields.summary = 'Test Release Ticket'
        mock_jira.issue.return_value = mock_ticket

        result = validate_release_ticket(mock_jira, 'REL-123')

        self.assertEqual(result, mock_ticket)
        mock_jira.issue.assert_called_once_with('REL-123')

    def test_validate_release_ticket_not_found(self):
        """Test release ticket validation when ticket is not found."""
        mock_jira = Mock()
        mock_jira.issue.side_effect = JIRAError(status_code=404, text="Not Found")

        with self.assertRaises(SystemExit) as cm:
            validate_release_ticket(mock_jira, 'REL-999')
        self.assertEqual(cm.exception.code, 1)

    def test_validate_release_ticket_other_error(self):
        """Test release ticket validation with other JIRA error."""
        mock_jira = Mock()
        mock_jira.issue.side_effect = JIRAError(status_code=403, text="Forbidden")

        with self.assertRaises(SystemExit) as cm:
            validate_release_ticket(mock_jira, 'REL-123')
        self.assertEqual(cm.exception.code, 1)

    def test_validate_release_ticket_unexpected_error(self):
        """Test release ticket validation with unexpected error."""
        mock_jira = Mock()
        mock_jira.issue.side_effect = Exception("Unexpected error")

        with self.assertRaises(SystemExit) as cm:
            validate_release_ticket(mock_jira, 'REL-123')
        self.assertEqual(cm.exception.code, 1)

    def test_create_integration_ticket_with_task_type(self):
        """Test creating integration ticket with Task issue type."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        # Mock issue types with Task available
        mock_jira.createmeta.return_value = {
            'projects': [{
                'issuetypes': [
                    {'name': 'Bug'},
                    {'name': 'Task'},
                    {'name': 'Story'}
                ]
            }]
        }

        mock_ticket = Mock()
        mock_ticket.key = 'INT-123'
        mock_jira.create_issue.return_value = mock_ticket

        # Mock args
        args = Mock()
        args.target_jira_project = 'INT'
        args.ticket_summary = 'Integration ticket for release'

        result = create_integration_ticket(mock_jira, args)

        self.assertEqual(result, mock_ticket)
        mock_jira.create_issue.assert_called_once()

        # Verify the issue creation call
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['project'], 'INT')
        self.assertEqual(call_args['issuetype'], {'name': 'Task'})
        self.assertEqual(call_args['summary'], 'Integration ticket for release')

    # noinspection DuplicatedCode
    def test_create_integration_ticket_with_improvement_type(self):
        """Test creating integration ticket with Improvement issue type when Task is not available."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        # Mock issue types with only Improvement available (no Bug)
        mock_jira.createmeta.return_value = {
            'projects': [{
                'issuetypes': [
                    {'name': 'Bug'},
                    {'name': 'Improvement'},
                ]
            }]
        }

        mock_ticket = Mock()
        mock_ticket.key = 'INT-124'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'INT'
        args.ticket_summary = 'Integration ticket for release'

        result = create_integration_ticket(mock_jira, args)

        self.assertEqual(result, mock_ticket)

        # Verify the issue creation call - should use Improvement
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['issuetype'], {'name': 'Improvement'})

    # noinspection DuplicatedCode
    def test_create_integration_ticket_with_first_available_type(self):
        """Test creating integration ticket with first available issue type."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        # Mock issue types with neither Task nor Story available
        mock_jira.createmeta.return_value = {
            'projects': [{
                'issuetypes': [
                    {'name': 'Bug'},
                    {'name': 'Epic'}
                ]
            }]
        }

        mock_ticket = Mock()
        mock_ticket.key = 'INT-125'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'INT'
        args.ticket_summary = 'Integration ticket for release'

        result = create_integration_ticket(mock_jira, args)

        self.assertEqual(result, mock_ticket)

        # Verify the issue creation call - should use first available (Bug)
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['issuetype'], {'name': 'Bug'})

    def test_create_integration_ticket_no_issue_types(self):
        """Test creating integration ticket when no issue types are available."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        # Mock empty issue types
        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': []}]
        }

        args = Mock()
        args.target_jira_project = 'INT'

        with self.assertRaises(SystemExit) as cm:
            create_integration_ticket(mock_jira, args)
        self.assertEqual(cm.exception.code, 1)

    def test_create_integration_ticket_project_access_error(self):
        """Test creating integration ticket when project access fails."""
        mock_jira = Mock()
        mock_jira.createmeta.side_effect = JIRAError(status_code=403, text="Forbidden")

        args = Mock()
        args.target_jira_project = 'INT'

        with self.assertRaises(SystemExit) as cm:
            create_integration_ticket(mock_jira, args)
        self.assertEqual(cm.exception.code, 1)

    # noinspection DuplicatedCode,PyUnusedLocal
    @patch('create_integration_ticket.eprint')
    def test_create_integration_ticket_creation_error(self, mock_eprint):
        """Test handling JIRA error during ticket creation."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Task'}]}]
        }

        mock_response = Mock()
        mock_response.text = 'Error details'
        mock_jira.create_issue.side_effect = JIRAError(status_code=400, response=mock_response)

        args = Mock()
        args.target_jira_project = 'INT'
        args.ticket_summary = 'Test ticket'

        with self.assertRaises(SystemExit) as cm:
            create_integration_ticket(mock_jira, args)
        self.assertEqual(cm.exception.code, 1)

    def test_link_tickets_success(self):
        """Test successful ticket linking."""
        mock_jira = Mock()
        mock_integration_ticket = Mock()
        mock_integration_ticket.key = 'INT-123'
        mock_release_ticket = Mock()
        mock_release_ticket.key = 'REL-456'

        link_tickets(mock_jira, mock_integration_ticket, mock_release_ticket, 'relates to')

        mock_jira.create_issue_link.assert_called_once_with(
            type='relates to',
            inwardIssue='INT-123',
            outwardIssue='REL-456'
        )

    def test_link_tickets_jira_error(self):
        """Test ticket linking with JIRA error (should not exit)."""
        mock_jira = Mock()
        mock_jira.create_issue_link.side_effect = JIRAError(status_code=400, text="Bad Request")

        mock_integration_ticket = Mock()
        mock_integration_ticket.key = 'INT-123'
        mock_release_ticket = Mock()
        mock_release_ticket.key = 'REL-456'

        # Should not raise SystemExit - linking failure is not fatal
        link_tickets(mock_jira, mock_integration_ticket, mock_release_ticket, 'relates to')

    def test_link_tickets_unexpected_error(self):
        """Test ticket linking with unexpected error (should not exit)."""
        mock_jira = Mock()
        mock_jira.create_issue_link.side_effect = Exception("Unexpected error")

        mock_integration_ticket = Mock()
        mock_integration_ticket.key = 'INT-123'
        mock_release_ticket = Mock()
        mock_release_ticket.key = 'REL-456'

        # Should not raise SystemExit - linking failure is not fatal
        link_tickets(mock_jira, mock_integration_ticket, mock_release_ticket, 'relates to')

    @patch('sys.argv', [
        'create_integration_ticket.py',
        '--ticket-summary', 'Integration for TestProject 1.0.0',
        '--release-ticket-key', 'REL-123',
        '--target-jira-project', 'INT',
        '--jira-url', 'https://sonarsource.atlassian.net/',
        '--link-type', 'relates to'
    ])
    @patch('create_integration_ticket.get_jira_instance')
    @patch('create_integration_ticket.validate_release_ticket')
    @patch('create_integration_ticket.create_integration_ticket')
    @patch('create_integration_ticket.link_tickets')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_successful_execution(self, mock_stderr, mock_link_tickets,
                                       mock_create_ticket, mock_validate_release_ticket, mock_get_jira):
        """Test successful execution through main function."""
        # Mock JIRA instance
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira

        # Mock release ticket validation
        mock_release_ticket = Mock()
        mock_release_ticket.key = 'REL-123'
        mock_validate_release_ticket.return_value = mock_release_ticket

        # Mock integration ticket creation
        mock_integration_ticket = Mock()
        mock_integration_ticket.key = 'INT-789'
        mock_integration_ticket.permalink.return_value = 'https://jira.com/INT-789'
        mock_create_ticket.return_value = mock_integration_ticket

        main()

        # Verify get_jira_instance was called with correct URL
        mock_get_jira.assert_called_once_with('https://sonarsource.atlassian.net/')

        # Verify validate_release_ticket was called
        mock_validate_release_ticket.assert_called_once_with(mock_jira, 'REL-123')

        # Verify create_integration_ticket was called
        mock_create_ticket.assert_called_once()
        call_args = mock_create_ticket.call_args[0]
        self.assertEqual(call_args[0], mock_jira)  # jira client
        args = call_args[1]  # args object
        self.assertEqual(args.ticket_summary, 'Integration for TestProject 1.0.0')
        self.assertEqual(args.release_ticket_key, 'REL-123')
        self.assertEqual(args.target_jira_project, 'INT')
        self.assertEqual(args.jira_url, 'https://sonarsource.atlassian.net/')
        self.assertEqual(args.link_type, 'relates to')

        # Verify link_tickets was called
        mock_link_tickets.assert_called_once_with(
            mock_jira, mock_integration_ticket, mock_release_ticket, 'relates to'
        )

        # Verify output contains success message
        stderr_output = mock_stderr.getvalue()
        self.assertIn('🎉 Successfully created integration ticket!', stderr_output)
        self.assertIn('Ticket Key: INT-789', stderr_output)
        self.assertIn('Linked to: REL-123', stderr_output)

    # noinspection PyUnusedLocal
    @patch('sys.argv', [
        'create_integration_ticket.py',
        '--ticket-summary', 'Minimal integration ticket',
        '--release-ticket-key', 'REL-456',
        '--target-jira-project', 'TEST',
        '--jira-url', 'https://sonarsource-sandbox-608.atlassian.net/'
    ])
    @patch('create_integration_ticket.get_jira_instance')
    @patch('create_integration_ticket.validate_release_ticket')
    @patch('create_integration_ticket.create_integration_ticket')
    @patch('create_integration_ticket.link_tickets')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_with_minimal_parameters(self, mock_stderr, mock_link_tickets,
                                          mock_create_ticket, mock_validate_ticket, mock_get_jira):
        """Test main function with minimal required parameters."""
        # Mock JIRA instance
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira

        # Mock release ticket validation
        mock_release_ticket = Mock()
        mock_release_ticket.key = 'REL-456'
        mock_validate_ticket.return_value = mock_release_ticket

        # Mock integration ticket creation
        mock_integration_ticket = Mock()
        mock_integration_ticket.key = 'TEST-100'
        mock_integration_ticket.permalink.return_value = 'https://sandbox.jira.com/TEST-100'
        mock_create_ticket.return_value = mock_integration_ticket

        main()

        # Verify get_jira_instance was called with sandbox URL
        mock_get_jira.assert_called_once_with('https://sonarsource-sandbox-608.atlassian.net/')

        # Verify parameters were parsed correctly with defaults
        call_args = mock_create_ticket.call_args[0]
        args = call_args[1]  # args object
        self.assertEqual(args.ticket_summary, 'Minimal integration ticket')
        self.assertEqual(args.release_ticket_key, 'REL-456')
        self.assertEqual(args.target_jira_project, 'TEST')
        self.assertEqual(args.jira_url, 'https://sonarsource-sandbox-608.atlassian.net/')
        self.assertEqual(args.link_type, 'relates to')  # default

        # Verify link_tickets was called with default link type
        mock_link_tickets.assert_called_once_with(
            mock_jira, mock_integration_ticket, mock_release_ticket, 'relates to'
        )
