#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for notify_slack.py
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notify_slack import (
    get_slack_token, normalize_channel, send_slack_notification
)


class TestNotifySlack(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_get_slack_token_missing(self):
        """Test that missing token causes exit."""
        with self.assertRaises(SystemExit) as cm:
            get_slack_token()
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'SLACK_TOKEN': 'xoxb-test-token'})
    def test_get_slack_token_success(self):
        """Test successful token retrieval."""
        token = get_slack_token()
        self.assertEqual(token, 'xoxb-test-token')

    def test_normalize_channel_without_hash(self):
        """Test normalizing channel without #."""
        self.assertEqual(normalize_channel('releases'), '#releases')

    def test_normalize_channel_with_hash(self):
        """Test normalizing channel that already has #."""
        self.assertEqual(normalize_channel('#releases'), '#releases')

    @patch('notify_slack.requests.post')
    def test_send_slack_notification_success(self, mock_post):
        """Test successful Slack notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response

        # Should not raise
        send_slack_notification(
            slack_token='xoxb-test',
            channel='#releases',
            branch='main',
            repository='owner/repo',
            freeze=True,
            run_url='https://github.com/owner/repo/actions/runs/123'
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], 'https://slack.com/api/chat.postMessage')
        payload = call_args[1]['json']
        self.assertEqual(payload['channel'], '#releases')

    @patch('notify_slack.requests.post')
    def test_send_slack_notification_freeze_message(self, mock_post):
        """Test Slack notification message for freeze."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response

        send_slack_notification(
            slack_token='xoxb-test',
            channel='#releases',
            branch='main',
            repository='owner/repo',
            freeze=True,
            run_url='https://github.com/owner/repo/actions/runs/123'
        )

        payload = mock_post.call_args[1]['json']
        message_text = payload['attachments'][0]['blocks'][0]['text']['text']
        self.assertIn(':lock:', message_text)
        self.assertIn('frozen', message_text)
        self.assertIn('main', message_text)
        self.assertEqual(payload['attachments'][0]['color'], 'warning')

    @patch('notify_slack.requests.post')
    def test_send_slack_notification_unfreeze_message(self, mock_post):
        """Test Slack notification message for unfreeze."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response

        send_slack_notification(
            slack_token='xoxb-test',
            channel='#releases',
            branch='develop',
            repository='owner/repo',
            freeze=False,
            run_url='https://github.com/owner/repo/actions/runs/456'
        )

        payload = mock_post.call_args[1]['json']
        message_text = payload['attachments'][0]['blocks'][0]['text']['text']
        self.assertIn(':unlock:', message_text)
        self.assertIn('unfrozen', message_text)
        self.assertIn('develop', message_text)
        self.assertEqual(payload['attachments'][0]['color'], 'good')

    @patch('notify_slack.requests.post')
    def test_send_slack_notification_http_error(self, mock_post):
        """Test Slack notification HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        with self.assertRaises(SystemExit) as cm:
            send_slack_notification(
                slack_token='xoxb-test',
                channel='#releases',
                branch='main',
                repository='owner/repo',
                freeze=True,
                run_url='https://github.com/owner/repo/actions/runs/123'
            )
        self.assertEqual(cm.exception.code, 1)

    @patch('notify_slack.requests.post')
    def test_send_slack_notification_api_error(self, mock_post):
        """Test Slack notification API error response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': False, 'error': 'channel_not_found'}
        mock_post.return_value = mock_response

        with self.assertRaises(SystemExit) as cm:
            send_slack_notification(
                slack_token='xoxb-test',
                channel='#nonexistent',
                branch='main',
                repository='owner/repo',
                freeze=True,
                run_url='https://github.com/owner/repo/actions/runs/123'
            )
        self.assertEqual(cm.exception.code, 1)

    @patch('notify_slack.requests.post')
    def test_send_slack_notification_run_url_in_context(self, mock_post):
        """Test that run URL is included in the notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response

        run_url = 'https://github.com/owner/repo/actions/runs/789'
        send_slack_notification(
            slack_token='xoxb-test',
            channel='#releases',
            branch='main',
            repository='owner/repo',
            freeze=True,
            run_url=run_url
        )

        payload = mock_post.call_args[1]['json']
        context_text = payload['attachments'][0]['blocks'][1]['elements'][0]['text']
        self.assertIn(run_url, context_text)


if __name__ == '__main__':
    unittest.main()
