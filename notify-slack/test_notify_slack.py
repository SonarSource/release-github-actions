#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for notify_slack.py
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notify_slack import normalize_channel, send_slack_notification


class TestNormalizeChannel(unittest.TestCase):

    def test_adds_hash_when_missing(self):
        self.assertEqual(normalize_channel('releases'), '#releases')

    def test_keeps_existing_hash(self):
        self.assertEqual(normalize_channel('#releases'), '#releases')

    def test_channel_id_not_prefixed(self):
        # C = public/private channel, D = DM, G = group DM
        # 8 suffix chars (minimum)
        self.assertEqual(normalize_channel('C1234ABCD'), 'C1234ABCD')
        # 9 suffix chars (middle)
        self.assertEqual(normalize_channel('C1234ABCDE'), 'C1234ABCDE')
        self.assertEqual(normalize_channel('D0AB12XYZ9'), 'D0AB12XYZ9')
        self.assertEqual(normalize_channel('G9Z8Y7X6W5'), 'G9Z8Y7X6W5')
        # 10 suffix chars (maximum)
        self.assertEqual(normalize_channel('C1234ABCDEF'), 'C1234ABCDEF')


class TestSendSlackNotification(unittest.TestCase):

    def _mock_success(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        return mock_response

    @patch('notify_slack.requests.post')
    def test_posts_to_slack_api(self, mock_post):
        mock_post.return_value = self._mock_success()

        send_slack_notification(
            slack_token='xoxb-test',
            channel='#releases',
            project_name='my-project',
            icon=':memo:',
            color='good',
            message='PR is ready',
        )

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        self.assertEqual(url, 'https://slack.com/api/chat.postMessage')

    @patch('notify_slack.requests.post')
    def test_payload_fields(self, mock_post):
        mock_post.return_value = self._mock_success()

        send_slack_notification(
            slack_token='xoxb-test',
            channel='#releases',
            project_name='my-project',
            icon=':memo:',
            color='good',
            message='PR is ready',
        )

        payload = mock_post.call_args[1]['json']
        self.assertEqual(payload['channel'], '#releases')
        self.assertEqual(payload['icon_emoji'], ':memo:')
        self.assertIn('my-project', payload['username'])
        attachment = payload['attachments'][0]
        self.assertEqual(attachment['color'], 'good')
        self.assertEqual(attachment['blocks'][0]['text']['text'], 'PR is ready')

    @patch('notify_slack.requests.post')
    def test_http_error_exits(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        with self.assertRaises(SystemExit) as cm:
            send_slack_notification(
                slack_token='xoxb-test',
                channel='#releases',
                project_name='my-project',
                icon=':alert:',
                color='danger',
                message='Something failed',
            )
        self.assertEqual(cm.exception.code, 1)

    @patch('notify_slack.requests.post')
    def test_api_error_exits(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': False, 'error': 'channel_not_found'}
        mock_post.return_value = mock_response

        with self.assertRaises(SystemExit) as cm:
            send_slack_notification(
                slack_token='xoxb-test',
                channel='#nonexistent',
                project_name='my-project',
                icon=':alert:',
                color='danger',
                message='Something failed',
            )
        self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
