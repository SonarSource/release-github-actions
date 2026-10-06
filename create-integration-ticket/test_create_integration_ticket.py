#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for create_integration_ticket.py
"""

import unittest
import requests
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO

# Add the current directory to the path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from create_integration_ticket import (
    validate_release_ticket, create_integration_ticket,
    link_tickets, main, version_sort_key, find_lowest_version, resolve_fix_versions,
    fetch_shipped_versions, list_tag_refs, parse_shipped_versions, fetch_open_versions,
    exclude_shipped_versions
)
from jira_common import CUSTOM_FIELDS
from jira.exceptions import JIRAError


def make_version(name, released=False, archived=False):
    version = Mock()
    version.name = name
    version.released = released
    version.archived = archived
    return version


class TestCreateIntegrationTicket(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_env = {
            'JIRA_USER': 'test_user',
            'JIRA_TOKEN': 'test_token'
        }

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

    def test_create_integration_ticket_with_maintenance_type(self):
        """Test creating integration ticket with Maintenance issue type."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        # Mock issue types with Maintenance available
        mock_jira.createmeta.return_value = {
            'projects': [{
                'issuetypes': [
                    {'name': 'Bug'},
                    {'name': 'Maintenance'},
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
        args.ticket_description = None

        result = create_integration_ticket(mock_jira, args)

        self.assertEqual(result, mock_ticket)
        mock_jira.create_issue.assert_called_once()

        # Verify the issue creation call
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['project'], 'INT')
        self.assertEqual(call_args['issuetype'], {'name': 'Maintenance'})
        self.assertEqual(call_args['summary'], 'Integration ticket for release')
        self.assertNotIn('description', call_args)  # No description provided

    def test_create_integration_ticket_with_description(self):
        """Test creating integration ticket with description."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        # Mock issue types with Maintenance available
        mock_jira.createmeta.return_value = {
            'projects': [{
                'issuetypes': [
                    {'name': 'Maintenance'}
                ]
            }]
        }

        mock_ticket = Mock()
        mock_ticket.key = 'INT-123'
        mock_jira.create_issue.return_value = mock_ticket

        # Mock args with description
        args = Mock()
        args.target_jira_project = 'INT'
        args.ticket_summary = 'Integration ticket for release'
        args.ticket_description = 'This is a detailed description of the integration ticket'

        result = create_integration_ticket(mock_jira, args)

        self.assertEqual(result, mock_ticket)
        mock_jira.create_issue.assert_called_once()

        # Verify the issue creation call does NOT include description
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['project'], 'INT')
        self.assertEqual(call_args['issuetype'], {'name': 'Maintenance'})
        self.assertEqual(call_args['summary'], 'Integration ticket for release')
        self.assertNotIn('description', call_args)
        
        # Verify the description was set via update
        mock_ticket.update.assert_called_once_with(fields={'description': 'This is a detailed description of the integration ticket'})

    @patch('create_integration_ticket.eprint')
    def test_create_integration_ticket_description_update_fails(self, mock_eprint):
        """Test creating integration ticket when description update fails."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }

        mock_ticket = Mock()
        mock_ticket.key = 'INT-123'
        mock_jira.create_issue.return_value = mock_ticket
        
        # Mock description update failure
        mock_response = Mock()
        mock_response.text = 'Description field update failed'
        mock_ticket.update.side_effect = JIRAError(status_code=400, response=mock_response)

        args = Mock()
        args.target_jira_project = 'INT'
        args.ticket_summary = 'Integration ticket for release'
        args.ticket_description = 'This description will fail to set'

        result = create_integration_ticket(mock_jira, args)

        # Should still return the ticket even if description update failed
        self.assertEqual(result, mock_ticket)
        mock_jira.create_issue.assert_called_once()
        mock_ticket.update.assert_called_once_with(fields={'description': 'This description will fail to set'})

    # noinspection DuplicatedCode
    def test_create_integration_ticket_with_feature_type(self):
        """Test creating integration ticket with Feature issue type when Maintenance is not available."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        # Mock issue types with only Feature available (no Bug)
        mock_jira.createmeta.return_value = {
            'projects': [{
                'issuetypes': [
                    {'name': 'Bug'},
                    {'name': 'Feature'},
                ]
            }]
        }

        mock_ticket = Mock()
        mock_ticket.key = 'INT-124'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'INT'
        args.ticket_summary = 'Integration ticket for release'
        args.ticket_description = None

        result = create_integration_ticket(mock_jira, args)

        self.assertEqual(result, mock_ticket)

        # Verify the issue creation call - should use Feature
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['issuetype'], {'name': 'Feature'})

    # noinspection DuplicatedCode
    def test_create_integration_ticket_with_task_type(self):
        """Test creating integration ticket with Task issue type when Maintenance and Feature is not available."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        # Mock issue types with Task and Improvement available (no Bug)
        mock_jira.createmeta.return_value = {
            'projects': [{
                'issuetypes': [
                    {'name': 'Bug'},
                    {'name': 'Task'},
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
        args.ticket_description = None

        result = create_integration_ticket(mock_jira, args)

        self.assertEqual(result, mock_ticket)

        # Verify the issue creation call - should use Feature
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['issuetype'], {'name': 'Task'})

        # noinspection DuplicatedCode
    def test_create_integration_ticket_with_improvement_type(self):
        """Test creating integration ticket with Improvement issue type when Maintenance, Feature and Task is not available."""
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
        args.ticket_description = None

        result = create_integration_ticket(mock_jira, args)

        self.assertEqual(result, mock_ticket)

        # Verify the issue creation call - should use Feature
        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['issuetype'], {'name': 'Improvement'})

    # noinspection DuplicatedCode
    def test_create_integration_ticket_with_first_available_type(self):
        """Test creating integration ticket with first available issue type."""
        mock_jira = Mock()
        mock_project = Mock()
        mock_jira.project.return_value = mock_project

        # Mock issue types with neither Maintenance, Feature, Task, Improvement available
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
        args.ticket_description = None

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
        args.ticket_description = None

        with self.assertRaises(SystemExit) as cm:
            create_integration_ticket(mock_jira, args)
        self.assertEqual(cm.exception.code, 1)

    def test_create_integration_ticket_project_access_error(self):
        """Test creating integration ticket when project access fails."""
        mock_jira = Mock()
        mock_jira.createmeta.side_effect = JIRAError(status_code=403, text="Forbidden")

        args = Mock()
        args.target_jira_project = 'INT'
        args.ticket_description = None

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
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }

        mock_response = Mock()
        mock_response.text = 'Error details'
        mock_jira.create_issue.side_effect = JIRAError(status_code=400, response=mock_response)

        args = Mock()
        args.target_jira_project = 'INT'
        args.ticket_summary = 'Test ticket'
        args.ticket_description = None

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
        '--use-sandbox', 'false',
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

        # Verify get_jira_instance was called with correct flag
        mock_get_jira.assert_called_once_with('false')

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
        self.assertEqual(args.use_sandbox, 'false')
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
        '--use-sandbox', 'true'
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

        # Verify get_jira_instance was called with sandbox flag
        mock_get_jira.assert_called_once_with('true')

        # Verify parameters were parsed correctly with defaults
        call_args = mock_create_ticket.call_args[0]
        args = call_args[1]  # args object
        self.assertEqual(args.ticket_summary, 'Minimal integration ticket')
        self.assertEqual(args.release_ticket_key, 'REL-456')
        self.assertEqual(args.target_jira_project, 'TEST')
        self.assertEqual(args.use_sandbox, 'true')
        self.assertEqual(args.link_type, 'relates to')  # default

        # Verify link_tickets was called with default link type
        mock_link_tickets.assert_called_once_with(
            mock_jira, mock_integration_ticket, mock_release_ticket, 'relates to'
        )

    @patch('sys.argv', [
        'create_integration_ticket.py',
        '--ticket-summary', 'Integration ticket with description',
        '--ticket-description', 'This ticket has a detailed description',
        '--release-ticket-key', 'REL-789',
        '--target-jira-project', 'DESC',
        '--use-sandbox', 'false',
        '--link-type', 'depends on',
        '--edition', 'Community Build & Server',
        '--team', 'f1da89c9-3712-4d15-b194-a4b24406e3e4'
    ])
    @patch('create_integration_ticket.get_jira_instance')
    @patch('create_integration_ticket.validate_release_ticket')
    @patch('create_integration_ticket.create_integration_ticket')
    @patch('create_integration_ticket.link_tickets')
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_with_description(self, mock_stderr, mock_link_tickets,
                                   mock_create_ticket, mock_validate_release_ticket, mock_get_jira):
        """Test main function with description parameter."""
        # Mock JIRA instance
        mock_jira = Mock()
        mock_get_jira.return_value = mock_jira

        # Mock release ticket validation
        mock_release_ticket = Mock()
        mock_release_ticket.key = 'REL-789'
        mock_validate_release_ticket.return_value = mock_release_ticket

        # Mock integration ticket creation
        mock_integration_ticket = Mock()
        mock_integration_ticket.key = 'DESC-101'
        mock_integration_ticket.permalink.return_value = 'https://jira.com/DESC-101'
        mock_create_ticket.return_value = mock_integration_ticket

        main()

        # Verify get_jira_instance was called with correct flag
        mock_get_jira.assert_called_once_with('false')

        # Verify validate_release_ticket was called
        mock_validate_release_ticket.assert_called_once_with(mock_jira, 'REL-789')

        # Verify create_integration_ticket was called with description
        mock_create_ticket.assert_called_once()
        call_args = mock_create_ticket.call_args[0]
        self.assertEqual(call_args[0], mock_jira)  # jira client
        args = call_args[1]  # args object
        self.assertEqual(args.ticket_summary, 'Integration ticket with description')
        self.assertEqual(args.ticket_description, 'This ticket has a detailed description')
        self.assertEqual(args.release_ticket_key, 'REL-789')
        self.assertEqual(args.target_jira_project, 'DESC')
        self.assertEqual(args.use_sandbox, 'false')
        self.assertEqual(args.link_type, 'depends on')
        self.assertEqual(args.edition, 'Community Build & Server')
        self.assertEqual(args.team, 'f1da89c9-3712-4d15-b194-a4b24406e3e4')

        # Verify link_tickets was called
        mock_link_tickets.assert_called_once_with(
            mock_jira, mock_integration_ticket, mock_release_ticket, 'depends on'
        )


    def test_create_integration_ticket_with_parent_epic(self):
        """Test creating integration ticket with a parent epic key sets fields.parent.key."""
        mock_jira = Mock()
        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }
        mock_ticket = Mock()
        mock_ticket.key = 'SQS-42'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'SQS'
        args.ticket_summary = 'Update sonar-security to 1.0.0'
        args.ticket_description = None
        args.parent_epic = 'SONARSEC-100'

        create_integration_ticket(mock_jira, args)

        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['parent'], {'key': 'SONARSEC-100'})

    def test_create_integration_ticket_without_parent_epic(self):
        """Test creating integration ticket without parent epic sets no parent field."""
        mock_jira = Mock()
        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }
        mock_ticket = Mock()
        mock_ticket.key = 'SQS-43'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'SQS'
        args.ticket_summary = 'Update sonar-security to 1.0.0'
        args.ticket_description = None
        args.parent_epic = None

        create_integration_ticket(mock_jira, args)

        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertNotIn('parent', call_args)

    def test_create_integration_ticket_edition_and_team_combinations(self):
        """Edition and team are set independently of one another: neither is gated on the
        other's presence, and both an empty string and a genuinely absent (None) argparse
        value — what `${VAR:+--flag "$VAR"}` produces when the workflow input is unset — must
        be treated as 'do not send this field'."""
        cases = [
            ('with both', 'Community Build & Server', 'f1da89c9-3712-4d15-b194-a4b24406e3e4', True, True),
            ('edition only', 'Community Build & Server', '', True, False),
            ('team only', '', 'f1da89c9-3712-4d15-b194-a4b24406e3e4', False, True),
            ('neither, None', None, None, False, False),
        ]
        for label, edition, team, expect_edition, expect_team in cases:
            with self.subTest(label):
                mock_jira = Mock()
                mock_jira.createmeta.return_value = {
                    'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
                }
                mock_jira.project_versions.return_value = []
                mock_ticket = Mock()
                mock_ticket.key = 'SQS-44'
                mock_jira.create_issue.return_value = mock_ticket

                args = Mock()
                args.target_jira_project = 'SQS'
                args.ticket_summary = 'Update sonar-security to 1.0.0'
                args.ticket_description = None
                args.parent_epic = None
                args.edition = edition
                args.team = team

                create_integration_ticket(mock_jira, args)

                call_args = mock_jira.create_issue.call_args[1]['fields']
                if expect_edition:
                    self.assertEqual(call_args[CUSTOM_FIELDS['EDITION']], {'value': edition})
                else:
                    self.assertNotIn(CUSTOM_FIELDS['EDITION'], call_args)
                if expect_team:
                    self.assertEqual(call_args[CUSTOM_FIELDS['TEAM']], team)
                else:
                    self.assertNotIn(CUSTOM_FIELDS['TEAM'], call_args)

    def test_version_sort_key_ordering(self):
        """'major.minor' versions sort numerically, not lexicographically (so '26.10' > '26.9')."""
        names = ['26.11', '26.9', '26.10']
        self.assertEqual(sorted(names, key=version_sort_key), ['26.9', '26.10', '26.11'])

    def test_find_lowest_version_picks_lowest(self):
        versions = [
            make_version('sqcb-26.11'),
            make_version('sqcb-26.9'),
            make_version('sqcb-26.10'),
        ]
        self.assertEqual(find_lowest_version(versions, 'sqcb-'), 'sqcb-26.9')

    def test_find_lowest_version_filters_by_prefix(self):
        versions = [make_version('sqs-2026.5'), make_version('2026.4')]
        self.assertIsNone(find_lowest_version(versions, 'sqcb-'))

    def test_find_lowest_version_no_candidates(self):
        self.assertIsNone(find_lowest_version([], 'sqcb-'))

    def test_find_lowest_version_skips_bugfix_versions(self):
        """Bugfix versions ('major.minor.patch') are ignored."""
        versions = [make_version('sqs-2025.4.9'), make_version('sqs-2025.5')]
        self.assertEqual(find_lowest_version(versions, 'sqs-'), 'sqs-2025.5')

    def test_find_lowest_version_skips_non_matching_format(self):
        versions = [make_version('sqcb-26.10-RC1'), make_version('sqcb-26.11')]
        self.assertEqual(find_lowest_version(versions, 'sqcb-'), 'sqcb-26.11')

    def test_resolve_fix_versions_community_build(self):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [
            make_version('sqcb-26.10'), make_version('sqcb-26.9'), make_version('sqs-2026.5'),
        ]
        self.assertEqual(resolve_fix_versions(mock_jira, 'SONAR', 'Community Build', None), ['sqcb-26.9'])

    def test_resolve_fix_versions_server(self):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [
            make_version('sqcb-26.9'), make_version('sqs-2026.6'), make_version('sqs-2026.5'),
        ]
        self.assertEqual(resolve_fix_versions(mock_jira, 'SONAR', 'Server', None), ['sqs-2026.5'])

    def test_resolve_fix_versions_community_build_and_server_orders_sqcb_first(self):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [
            make_version('sqs-2026.5'), make_version('sqcb-26.9'),
        ]
        self.assertEqual(
            resolve_fix_versions(mock_jira, 'SONAR', 'Community Build & Server', None),
            ['sqcb-26.9', 'sqs-2026.5']
        )
        mock_jira.project_versions.assert_called_once_with('SONAR')

    def test_resolve_fix_versions_na_skips_lookup_entirely(self):
        mock_jira = Mock()
        self.assertEqual(resolve_fix_versions(mock_jira, 'SONAR', 'N/A', None), [])
        mock_jira.project_versions.assert_not_called()

    def test_resolve_fix_versions_unknown_edition(self):
        mock_jira = Mock()
        self.assertEqual(resolve_fix_versions(mock_jira, 'SONAR', 'Something Else', None), [])
        mock_jira.project_versions.assert_not_called()

    def test_resolve_fix_versions_no_matching_version(self):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [make_version('sqs-2026.5')]
        self.assertEqual(resolve_fix_versions(mock_jira, 'SONAR', 'Community Build', None), [])

    def test_resolve_fix_versions_skips_released_and_archived(self):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [
            make_version('sqcb-26.9', released=True),
            make_version('sqcb-26.10', archived=True),
            make_version('sqcb-26.11'),
        ]
        self.assertEqual(resolve_fix_versions(mock_jira, 'SONAR', 'Community Build', None), ['sqcb-26.11'])

    @patch('create_integration_ticket.eprint')
    def test_resolve_fix_versions_lookup_error_is_non_fatal(self, mock_eprint):
        mock_jira = Mock()
        mock_jira.project_versions.side_effect = JIRAError(status_code=500, text="Server Error")
        self.assertEqual(resolve_fix_versions(mock_jira, 'SONAR', 'Community Build', None), [])
        warnings = ' '.join(call.args[0] for call in mock_eprint.call_args_list)
        self.assertIn('Failed to fetch versions', warnings)
        self.assertIn("Skipping automatic 'Fix versions' assignment", warnings)

    def test_find_lowest_version_accepts_single_digit_major(self):
        """A single-digit major (e.g. '9.1') must not be rejected by the name pattern."""
        versions = [make_version('sqcb-9.1'), make_version('sqcb-26.9')]
        self.assertEqual(find_lowest_version(versions, 'sqcb-'), 'sqcb-9.1')

    def test_find_lowest_version_accepts_three_digit_minor(self):
        """A three-digit minor like '2026.100' is accepted."""
        versions = [make_version('sqs-2026.100'), make_version('sqs-2026.99')]
        self.assertEqual(find_lowest_version(versions, 'sqs-'), 'sqs-2026.99')

    def test_find_lowest_version_rejects_prefix_collision(self):
        """Names with extra text after the prefix (e.g. 'sqcb-lts-26.9') are ignored."""
        versions = [make_version('sqcb-lts-26.9'), make_version('sqs-next'), make_version('sqcb-26.10')]
        self.assertEqual(find_lowest_version(versions, 'sqcb-'), 'sqcb-26.10')
        self.assertIsNone(find_lowest_version(versions, 'sqs-'))

    @patch.dict(os.environ, {'GITHUB_TOKEN': ''})
    def test_create_integration_ticket_sets_fix_versions_for_edition(self):
        """Community Build & Server pulls both an sqcb- and an sqs- fix version onto the ticket."""
        mock_jira = Mock()
        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }
        mock_jira.project_versions.return_value = [
            make_version('sqcb-26.9'), make_version('sqs-2026.5'),
        ]
        mock_ticket = Mock()
        mock_ticket.key = 'SQS-50'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'SONAR'
        args.ticket_summary = 'Update sonar-security to 1.0.0'
        args.ticket_description = None
        args.parent_epic = None
        args.edition = 'Community Build & Server'
        args.team = None

        create_integration_ticket(mock_jira, args)

        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args['fixVersions'], [{'name': 'sqcb-26.9'}, {'name': 'sqs-2026.5'}])

    @patch.dict(os.environ, {'GITHUB_TOKEN': ''})
    def test_create_integration_ticket_sets_edition_team_and_fix_versions_together(self):
        """Edition, team and fix versions coexist in a single create_issue payload."""
        mock_jira = Mock()
        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }
        mock_jira.project_versions.return_value = [
            make_version('sqcb-26.9'), make_version('sqs-2026.5'),
        ]
        mock_ticket = Mock()
        mock_ticket.key = 'SQS-54'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'SONAR'
        args.ticket_summary = 'Update sonar-security to 1.0.0'
        args.ticket_description = None
        args.parent_epic = None
        args.edition = 'Community Build & Server'
        args.team = 'f1da89c9-3712-4d15-b194-a4b24406e3e4'

        create_integration_ticket(mock_jira, args)

        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertEqual(call_args[CUSTOM_FIELDS['EDITION']], {'value': 'Community Build & Server'})
        self.assertEqual(call_args[CUSTOM_FIELDS['TEAM']], 'f1da89c9-3712-4d15-b194-a4b24406e3e4')
        self.assertEqual(call_args['fixVersions'], [{'name': 'sqcb-26.9'}, {'name': 'sqs-2026.5'}])

    def test_create_integration_ticket_na_edition_sets_no_fix_versions(self):
        mock_jira = Mock()
        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }
        mock_ticket = Mock()
        mock_ticket.key = 'SQS-51'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'SONAR'
        args.ticket_summary = 'Update sonar-security to 1.0.0'
        args.ticket_description = None
        args.parent_epic = None
        args.edition = 'N/A'
        args.team = None

        create_integration_ticket(mock_jira, args)

        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertNotIn('fixVersions', call_args)
        mock_jira.project_versions.assert_not_called()

    def test_create_integration_ticket_no_edition_sets_no_fix_versions(self):
        mock_jira = Mock()
        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }
        mock_ticket = Mock()
        mock_ticket.key = 'SQS-52'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'SONAR'
        args.ticket_summary = 'Update sonar-security to 1.0.0'
        args.ticket_description = None
        args.parent_epic = None
        args.edition = None
        args.team = None

        create_integration_ticket(mock_jira, args)

        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertNotIn('fixVersions', call_args)
        mock_jira.project_versions.assert_not_called()

    def test_create_integration_ticket_no_matching_version_sets_no_fix_versions(self):
        mock_jira = Mock()
        mock_jira.createmeta.return_value = {
            'projects': [{'issuetypes': [{'name': 'Maintenance'}]}]
        }
        mock_jira.project_versions.return_value = []
        mock_ticket = Mock()
        mock_ticket.key = 'SQS-53'
        mock_jira.create_issue.return_value = mock_ticket

        args = Mock()
        args.target_jira_project = 'SONAR'
        args.ticket_summary = 'Update sonar-security to 1.0.0'
        args.ticket_description = None
        args.parent_epic = None
        args.edition = 'Community Build'
        args.team = None

        create_integration_ticket(mock_jira, args)

        call_args = mock_jira.create_issue.call_args[1]['fields']
        self.assertNotIn('fixVersions', call_args)

    def test_resolve_fix_versions_skips_versions_already_tagged(self):
        """An open Jira version with a sonar-enterprise tag is already shipped, so the next one wins."""
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [make_version('sqcb-26.9'), make_version('sqcb-26.10')]
        with patch('create_integration_ticket.fetch_shipped_versions', return_value={'sqcb-26.9'}):
            self.assertEqual(
                resolve_fix_versions(mock_jira, 'SONAR', 'Community Build', 'token'), ['sqcb-26.10']
            )

    def test_resolve_fix_versions_filters_each_prefix_by_its_own_tags(self):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [
            make_version('sqcb-26.9'), make_version('sqcb-26.10'),
            make_version('sqs-2026.5'), make_version('sqs-2026.6'),
        ]
        shipped = {'sqcb-': {'sqcb-26.9'}, 'sqs-': set()}
        with patch('create_integration_ticket.fetch_shipped_versions',
                   side_effect=lambda token, prefix: shipped[prefix]):
            self.assertEqual(
                resolve_fix_versions(mock_jira, 'SONAR', 'Community Build & Server', 'token'),
                ['sqcb-26.10', 'sqs-2026.5']
            )

    def test_resolve_fix_versions_all_candidates_tagged_yields_none(self):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [make_version('sqs-2026.5')]
        with patch('create_integration_ticket.fetch_shipped_versions', return_value={'sqs-2026.5'}):
            self.assertEqual(resolve_fix_versions(mock_jira, 'SONAR', 'Server', 'token'), [])

    def test_resolve_fix_versions_tag_lookup_failure_falls_back_to_jira(self):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [make_version('sqcb-26.9'), make_version('sqcb-26.10')]
        with patch('create_integration_ticket.fetch_shipped_versions', return_value=None):
            self.assertEqual(
                resolve_fix_versions(mock_jira, 'SONAR', 'Community Build', 'token'), ['sqcb-26.9']
            )

    @patch('create_integration_ticket.eprint')
    def test_resolve_fix_versions_without_token_warns_and_skips_tag_lookup(self, mock_eprint):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [make_version('sqcb-26.9')]
        with patch('create_integration_ticket.fetch_shipped_versions') as mock_fetch:
            self.assertEqual(resolve_fix_versions(mock_jira, 'SONAR', 'Community Build', None), ['sqcb-26.9'])
        mock_fetch.assert_not_called()
        warnings = ' '.join(call.args[0] for call in mock_eprint.call_args_list)
        self.assertIn('No GITHUB_TOKEN', warnings)

    def test_resolve_fix_versions_na_makes_no_tag_lookup(self):
        with patch('create_integration_ticket.fetch_shipped_versions') as mock_fetch:
            self.assertEqual(resolve_fix_versions(Mock(), 'SONAR', 'N/A', 'token'), [])
        mock_fetch.assert_not_called()

    @patch('create_integration_ticket.eprint')
    def test_resolve_fix_versions_without_token_warns_once_for_all_prefixes(self, mock_eprint):
        mock_jira = Mock()
        mock_jira.project_versions.return_value = [make_version('sqcb-26.9'), make_version('sqs-2026.5')]
        resolve_fix_versions(mock_jira, 'SONAR', 'Community Build & Server', None)
        warnings = [c for c in mock_eprint.call_args_list if 'No GITHUB_TOKEN' in c.args[0]]
        self.assertEqual(len(warnings), 1)

    def test_parse_shipped_versions_maps_tags_to_jira_versions(self):
        """Bugfix and build-number tag segments collapse onto the 'major.minor' Jira version."""
        refs = [
            'refs/tags/sqs-2026.5.0.132233',
            'refs/tags/sqs-2026.5.2.132813',
            'refs/tags/sqs-2026.4.1.126914',
            'refs/tags/sqs-2026.6',
        ]
        self.assertEqual(parse_shipped_versions(refs, 'sqs-'), {'sqs-2026.5', 'sqs-2026.4'})

    def test_parse_shipped_versions_ignores_other_prefixes_and_malformed_refs(self):
        refs = ['refs/tags/sqsx-2026.5.0.1', 'refs/tags/sqs-foo', 'refs/tags/sqcb-26.9.0.1']
        self.assertEqual(parse_shipped_versions(refs, 'sqs-'), set())

    def test_parse_shipped_versions_empty(self):
        self.assertEqual(parse_shipped_versions([], 'sqs-'), set())

    @patch('create_integration_ticket.requests.get')
    def test_list_tag_refs_sends_token_and_returns_ref_names(self, mock_get):
        response = Mock(links={})
        response.json.return_value = [{'ref': 'refs/tags/sqs-2026.5.0.1'}]
        mock_get.return_value = response
        self.assertEqual(list_tag_refs('token', 'sqs-'), ['refs/tags/sqs-2026.5.0.1'])
        self.assertEqual(mock_get.call_args.kwargs['headers']['Authorization'], 'Bearer token')
        self.assertTrue(mock_get.call_args.args[0].endswith('/tags/sqs-'))

    @patch('create_integration_ticket.requests.get')
    def test_list_tag_refs_follows_pagination(self, mock_get):
        page1 = Mock(links={'next': {'url': 'https://api.github.com/next'}})
        page1.json.return_value = [{'ref': 'refs/tags/sqs-2025.1.0.1'}]
        page2 = Mock(links={})
        page2.json.return_value = [{'ref': 'refs/tags/sqs-2026.5.0.2'}]
        mock_get.side_effect = [page1, page2]
        self.assertEqual(
            list_tag_refs('token', 'sqs-'), ['refs/tags/sqs-2025.1.0.1', 'refs/tags/sqs-2026.5.0.2']
        )
        self.assertEqual(mock_get.call_args.args[0], 'https://api.github.com/next')

    @patch('create_integration_ticket.requests.get')
    def test_list_tag_refs_raises_on_http_error(self, mock_get):
        mock_get.return_value.raise_for_status.side_effect = requests.HTTPError('404 Not Found')
        with self.assertRaises(requests.HTTPError):
            list_tag_refs('token', 'sqs-')

    def test_fetch_shipped_versions_combines_listing_and_parsing(self):
        with patch('create_integration_ticket.list_tag_refs', return_value=['refs/tags/sqs-2026.5.0.1']):
            self.assertEqual(fetch_shipped_versions('token', 'sqs-'), {'sqs-2026.5'})

    @patch('create_integration_ticket.eprint')
    def test_fetch_shipped_versions_http_error_returns_none(self, mock_eprint):
        with patch('create_integration_ticket.list_tag_refs', side_effect=requests.HTTPError('404 Not Found')):
            self.assertIsNone(fetch_shipped_versions('token', 'sqs-'))
        self.assertIn('Failed to list sonar-enterprise', mock_eprint.call_args.args[0])

    def test_fetch_open_versions_filters_released_and_archived(self):
        mock_jira = Mock()
        open_version = make_version('sqs-2026.6')
        mock_jira.project_versions.return_value = [
            make_version('sqs-2026.4', released=True), make_version('sqs-2026.5', archived=True), open_version,
        ]
        self.assertEqual(fetch_open_versions(mock_jira, 'SONAR'), [open_version])

    @patch('create_integration_ticket.eprint')
    def test_fetch_open_versions_returns_none_on_jira_error(self, mock_eprint):
        mock_jira = Mock()
        mock_jira.project_versions.side_effect = JIRAError(status_code=500)
        self.assertIsNone(fetch_open_versions(mock_jira, 'SONAR'))

    def test_exclude_shipped_versions_removes_tagged(self):
        tagged, untagged = make_version('sqs-2026.5'), make_version('sqs-2026.6')
        with patch('create_integration_ticket.fetch_shipped_versions', return_value={'sqs-2026.5'}):
            self.assertEqual(exclude_shipped_versions([tagged, untagged], 'token', 'sqs-'), [untagged])

    def test_exclude_shipped_versions_unchanged_when_lookup_fails_or_empty(self):
        versions = [make_version('sqs-2026.5')]
        for shipped in (None, set()):
            with patch('create_integration_ticket.fetch_shipped_versions', return_value=shipped):
                self.assertEqual(exclude_shipped_versions(versions, 'token', 'sqs-'), versions)


if __name__ == '__main__':
    unittest.main()
