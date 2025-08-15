#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for create_release_ticket.py
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO

# Add the current directory to the path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from create_release_ticket import get_jira_instance, create_release_ticket, main
from jira.exceptions import JIRAError


class TestCreateReleaseTicket(unittest.TestCase):

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
    @patch('create_release_ticket.JIRA')
    def test_get_jira_instance_success(self, mock_jira_class):
        """Test successful JIRA instance creation."""
        mock_jira = Mock()
        mock_jira_class.return_value = mock_jira

        result = get_jira_instance('https://prod.com')

        self.assertEqual(result, mock_jira)
        mock_jira_class.assert_called_once_with('https://prod.com', basic_auth=('test', 'token'), get_server_info=True)

    @patch.dict(os.environ, {'JIRA_USER': 'test', 'JIRA_TOKEN': 'token'})
    @patch('create_release_ticket.JIRA')
    def test_get_jira_instance_auth_failure(self, mock_jira_class):
        """Test JIRA instance creation with authentication failure."""
        mock_jira_class.side_effect = JIRAError(status_code=401, text="Unauthorized")

        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('https://prod.com')
        self.assertEqual(cm.exception.code, 1)

    def test_create_release_ticket_with_all_fields(self):
        """Test creating release ticket with all fields."""
        mock_jira = Mock()
        mock_ticket = Mock()
        mock_ticket.key = 'REL-123'
        mock_ticket.permalink.return_value = 'https://jira.com/REL-123'
        mock_jira.create_issue.return_value = mock_ticket

        # Mock args
        args = Mock()
        args.project_name = 'TestProject'
        args.version = '1.2.3'
        args.short_description = 'Test release'
        args.sq_compatibility = '2025.1'
        args.documentation_status = 'Ready'
        args.rule_props_changed = 'Yes'
        args.sonarlint_changelog = 'Test changelog'
        args.targeted_product = '11.0'

        release_url = 'https://jira.com/release/notes'

        result = create_release_ticket(mock_jira, args, release_url)

        self.assertEqual(result, mock_ticket)
        mock_jira.create_issue.assert_called_once()
        
        # Verify the issue creation call
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['project'], 'REL')
        self.assertEqual(call_args['issuetype'], 'Ask for release')
        self.assertEqual(call_args['summary'], 'TestProject 1.2.3')
        self.assertEqual(call_args['customfield_10146'], 'Test release')  # SHORT_DESCRIPTION
        self.assertEqual(call_args['customfield_10148'], '2025.1')  # SQ_COMPATIBILITY
        self.assertEqual(call_args['customfield_10145'], release_url)  # LINK_TO_RELEASE_NOTES
        self.assertEqual(call_args['customfield_10147'], 'Ready')  # DOCUMENTATION_STATUS
        self.assertEqual(call_args['customfield_11263'], {'value': 'Yes'})  # RULE_PROPS_CHANGED
        self.assertEqual(call_args['customfield_11264'], 'Test changelog')  # SONARLINT_CHANGELOG
        self.assertEqual(call_args['customfield_10163'], {'value': '11.0'})  # TARGETED_PRODUCT

    def test_create_release_ticket_without_optional_fields(self):
        """Test creating release ticket without optional fields."""
        mock_jira = Mock()
        mock_ticket = Mock()
        mock_ticket.key = 'REL-124'
        mock_ticket.permalink.return_value = 'https://jira.com/REL-124'
        mock_jira.create_issue.return_value = mock_ticket

        # Mock args
        args = Mock()
        args.project_name = 'TestProject'
        args.version = '1.2.3'
        args.short_description = 'Test release'
        args.sq_compatibility = '2025.1'
        args.documentation_status = 'N/A'
        args.rule_props_changed = 'No'
        args.sonarlint_changelog = ''
        args.targeted_product = None

        release_url = 'https://jira.com/release/notes'

        result = create_release_ticket(mock_jira, args, release_url)

        self.assertEqual(result, mock_ticket)
        mock_jira.create_issue.assert_called_once()
        
        # Verify the issue creation call - should not include targeted_product
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertNotIn('customfield_10163', call_args)  # TARGETED_PRODUCT should not be set

    # noinspection DuplicatedCode,PyUnusedLocal
    @patch('create_release_ticket.eprint')
    def test_create_release_ticket_jira_error(self, mock_eprint):
        """Test handling JIRA error during ticket creation."""
        mock_jira = Mock()
        mock_response = Mock()
        mock_response.text = 'Error details'
        mock_jira.create_issue.side_effect = JIRAError(status_code=400, response=mock_response)

        args = Mock()
        args.project_name = 'TestProject'
        args.version = '1.2.3'
        args.short_description = 'Test release'
        args.sq_compatibility = '2025.1'
        args.documentation_status = 'N/A'
        args.rule_props_changed = 'No'
        args.sonarlint_changelog = ''
        args.targeted_product = None

        with self.assertRaises(SystemExit) as cm:
            create_release_ticket(mock_jira, args, 'https://release.url')
        
        self.assertEqual(cm.exception.code, 1)

    @patch('sys.argv', [
        'create_release_ticket.py',
        '--project-key', 'TEST',
        '--project-name', 'Test Project',
        '--version', '1.0.0',
        '--short-description', 'Test release',
        '--sq-compatibility', '2025.1',
        '--jira-url', 'https://test.jira.com',
        '--jira-release-url', 'https://jira.com/release/notes'
    ])
    @patch('create_release_ticket.get_jira_instance')
    @patch('create_release_ticket.create_release_ticket')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_successful_ticket_creation(self, mock_stderr, mock_stdout, mock_create_ticket, mock_get_jira):
        """Test successful ticket creation through main function."""
        # Mock JIRA instance and ticket
        mock_jira = Mock()
        mock_ticket = Mock()
        mock_ticket.key = 'REL-456'
        mock_ticket.permalink.return_value = 'https://jira.com/REL-456'
        mock_get_jira.return_value = mock_jira
        mock_create_ticket.return_value = mock_ticket

        main()

        # Verify get_jira_instance was called with correct URL
        mock_get_jira.assert_called_once_with('https://test.jira.com')

        # Verify create_release_ticket was called
        mock_create_ticket.assert_called_once()
        call_args = mock_create_ticket.call_args
        self.assertEqual(call_args[0][0], mock_jira)  # jira client
        self.assertEqual(call_args[0][2], 'https://jira.com/release/notes')  # release URL

        # Verify output
        stdout_output = mock_stdout.getvalue()
        self.assertIn('ticket_key=REL-456', stdout_output)
        self.assertIn('ticket_url=https://jira.com/REL-456', stdout_output)

        stderr_output = mock_stderr.getvalue()
        self.assertIn('Using release URL: https://jira.com/release/notes', stderr_output)
        self.assertIn('🎉 Successfully created release ticket!', stderr_output)

    # noinspection PyUnusedLocal
    @patch('sys.argv', [
        'create_release_ticket.py',
        '--project-key', 'TEST',
        '--project-name', 'Test Project',
        '--version', '1.0.0',
        '--short-description', 'Test release',
        '--sq-compatibility', '2025.1',
        '--targeted-product', '11.0',
        '--jira-url', 'https://sandbox.jira.com',
        '--jira-release-url', 'https://sandbox.jira.com/release/notes',
        '--documentation-status', 'Ready',
        '--rule-props-changed', 'Yes',
        '--sonarlint-changelog', 'Some changelog'
    ])
    @patch('create_release_ticket.get_jira_instance')
    @patch('create_release_ticket.create_release_ticket')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_with_all_parameters(self, mock_stderr, mock_stdout, mock_create_ticket, mock_get_jira):
        """Test main function with all parameters."""
        # Mock JIRA instance and ticket
        mock_jira = Mock()
        mock_ticket = Mock()
        mock_ticket.key = 'REL-789'
        mock_ticket.permalink.return_value = 'https://sandbox.jira.com/REL-789'
        mock_get_jira.return_value = mock_jira
        mock_create_ticket.return_value = mock_ticket

        main()

        # Verify get_jira_instance was called with sandbox URL
        mock_get_jira.assert_called_once_with('https://sandbox.jira.com')

        # Verify create_release_ticket was called with correct parameters
        mock_create_ticket.assert_called_once()
        call_args = mock_create_ticket.call_args
        args = call_args[0][1]  # args object
        self.assertEqual(args.project_key, 'TEST')
        self.assertEqual(args.project_name, 'Test Project')
        self.assertEqual(args.version, '1.0.0')
        self.assertEqual(args.short_description, 'Test release')
        self.assertEqual(args.sq_compatibility, '2025.1')
        self.assertEqual(args.targeted_product, '11.0')
        self.assertEqual(args.jira_url, 'https://sandbox.jira.com')
        self.assertEqual(args.jira_release_url, 'https://sandbox.jira.com/release/notes')
        self.assertEqual(args.documentation_status, 'Ready')
        self.assertEqual(args.rule_props_changed, 'Yes')
        self.assertEqual(args.sonarlint_changelog, 'Some changelog')

        stderr_output = mock_stderr.getvalue()
        self.assertIn('Using release URL: https://sandbox.jira.com/release/notes', stderr_output)


if __name__ == '__main__':
    unittest.main()
