#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lock_branch.py
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the current directory to the path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lock_branch import (
    get_github_token, get_branch_protection, is_branch_locked,
    update_branch_lock, build_protection_payload
)


class TestLockBranch(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_get_github_token_missing(self):
        """Test that missing token causes exit."""
        with self.assertRaises(SystemExit) as cm:
            get_github_token()
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'})
    def test_get_github_token_success(self):
        """Test successful token retrieval."""
        token = get_github_token()
        self.assertEqual(token, 'test_token')

    def test_is_branch_locked_true(self):
        """Test detecting locked branch."""
        protection = {'lock_branch': {'enabled': True}}
        self.assertTrue(is_branch_locked(protection))

    def test_is_branch_locked_false(self):
        """Test detecting unlocked branch."""
        protection = {'lock_branch': {'enabled': False}}
        self.assertFalse(is_branch_locked(protection))

    def test_is_branch_locked_none(self):
        """Test when protection is None."""
        self.assertFalse(is_branch_locked(None))

    def test_is_branch_locked_no_lock_branch(self):
        """Test when lock_branch key missing."""
        protection = {'enforce_admins': {'enabled': True}}
        self.assertFalse(is_branch_locked(protection))

    def test_build_protection_payload_none(self):
        """Test building payload when no existing protection."""
        payload = build_protection_payload(None, True)
        self.assertTrue(payload['lock_branch'])
        self.assertIsNone(payload['required_status_checks'])
        self.assertFalse(payload['enforce_admins'])
        self.assertIsNone(payload['required_pull_request_reviews'])
        self.assertIsNone(payload['restrictions'])

    def test_build_protection_payload_unlock(self):
        """Test building payload for unlock operation."""
        payload = build_protection_payload(None, False)
        self.assertFalse(payload['lock_branch'])

    def test_build_protection_payload_preserve_settings(self):
        """Test that existing settings are preserved."""
        current = {
            'enforce_admins': {'enabled': True},
            'required_status_checks': {
                'strict': True,
                'contexts': ['ci/test', 'ci/build']
            },
            'required_pull_request_reviews': {
                'dismiss_stale_reviews': True,
                'require_code_owner_reviews': True,
                'required_approving_review_count': 2
            },
            'restrictions': None,
            'lock_branch': {'enabled': False}
        }

        payload = build_protection_payload(current, True)

        self.assertTrue(payload['lock_branch'])
        self.assertTrue(payload['enforce_admins'])
        self.assertTrue(payload['required_status_checks']['strict'])
        self.assertEqual(payload['required_status_checks']['contexts'], ['ci/test', 'ci/build'])
        self.assertTrue(payload['required_pull_request_reviews']['dismiss_stale_reviews'])
        self.assertTrue(payload['required_pull_request_reviews']['require_code_owner_reviews'])
        self.assertEqual(payload['required_pull_request_reviews']['required_approving_review_count'], 2)
        self.assertIsNone(payload['restrictions'])

    def test_build_protection_payload_with_restrictions(self):
        """Test building payload with restrictions."""
        current = {
            'enforce_admins': {'enabled': False},
            'required_status_checks': None,
            'required_pull_request_reviews': None,
            'restrictions': {
                'users': [{'login': 'user1'}, {'login': 'user2'}],
                'teams': [{'slug': 'team1'}],
                'apps': [{'slug': 'app1'}]
            },
            'lock_branch': {'enabled': False}
        }

        payload = build_protection_payload(current, True)

        self.assertTrue(payload['lock_branch'])
        self.assertEqual(payload['restrictions']['users'], ['user1', 'user2'])
        self.assertEqual(payload['restrictions']['teams'], ['team1'])
        self.assertEqual(payload['restrictions']['apps'], ['app1'])

    @patch('lock_branch.requests.get')
    def test_get_branch_protection_success(self, mock_get):
        """Test successful branch protection retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'lock_branch': {'enabled': True}}
        mock_get.return_value = mock_response

        result = get_branch_protection('token', 'owner/repo', 'main')

        self.assertTrue(result['lock_branch']['enabled'])
        mock_get.assert_called_once()
        # Verify the URL is correct
        call_args = mock_get.call_args
        self.assertIn('owner/repo', call_args[0][0])
        self.assertIn('main', call_args[0][0])

    @patch('lock_branch.requests.get')
    def test_get_branch_protection_not_found(self, mock_get):
        """Test branch protection not found returns None."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = get_branch_protection('token', 'owner/repo', 'main')

        self.assertIsNone(result)

    @patch('lock_branch.requests.get')
    def test_get_branch_protection_error(self, mock_get):
        """Test branch protection API error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = 'Forbidden'
        mock_get.return_value = mock_response

        with self.assertRaises(SystemExit) as cm:
            get_branch_protection('token', 'owner/repo', 'main')
        self.assertEqual(cm.exception.code, 1)

    @patch('lock_branch.requests.put')
    def test_update_branch_lock_success(self, mock_put):
        """Test successful branch lock update."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'lock_branch': {'enabled': True}}
        mock_put.return_value = mock_response

        current = {'lock_branch': {'enabled': False}, 'enforce_admins': {'enabled': False}}
        result = update_branch_lock('token', 'owner/repo', 'main', True, current)

        self.assertTrue(result['lock_branch']['enabled'])
        mock_put.assert_called_once()

    @patch('lock_branch.requests.put')
    def test_update_branch_lock_created(self, mock_put):
        """Test branch lock update with 201 status."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'lock_branch': {'enabled': True}}
        mock_put.return_value = mock_response

        result = update_branch_lock('token', 'owner/repo', 'main', True, None)

        self.assertTrue(result['lock_branch']['enabled'])

    @patch('lock_branch.requests.put')
    def test_update_branch_lock_failure(self, mock_put):
        """Test branch lock update failure."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = 'Forbidden'
        mock_put.return_value = mock_response

        with self.assertRaises(SystemExit) as cm:
            update_branch_lock('token', 'owner/repo', 'main', True, None)
        self.assertEqual(cm.exception.code, 1)

    @patch('lock_branch.requests.put')
    def test_update_branch_lock_preserves_settings(self, mock_put):
        """Test that update preserves existing protection settings."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_put.return_value = mock_response

        current = {
            'enforce_admins': {'enabled': True},
            'required_status_checks': {
                'strict': True,
                'contexts': ['ci/test']
            },
            'required_pull_request_reviews': None,
            'restrictions': None,
            'lock_branch': {'enabled': False}
        }

        update_branch_lock('token', 'owner/repo', 'main', True, current)

        # Verify the payload sent to the API
        call_args = mock_put.call_args
        sent_payload = call_args[1]['json']
        self.assertTrue(sent_payload['lock_branch'])
        self.assertTrue(sent_payload['enforce_admins'])
        self.assertTrue(sent_payload['required_status_checks']['strict'])
        self.assertEqual(sent_payload['required_status_checks']['contexts'], ['ci/test'])


if __name__ == '__main__':
    unittest.main()
