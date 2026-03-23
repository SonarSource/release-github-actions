#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sends a Slack notification with a custom message or a list of failed jobs.
"""

import argparse
import os
import sys

import requests


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def require_env_token(name):
    token = os.environ.get(name)
    if not token:
        eprint(f"Error: {name} environment variable must be set.")
        sys.exit(1)
    return token


def normalize_channel(channel):
    """Ensures channel name starts with '#'."""
    if not channel.startswith('#'):
        return f'#{channel}'
    return channel


def send_slack_notification(slack_token, channel, project_name, icon, color, message):
    """
    Sends a Slack notification.

    Args:
        slack_token: Slack API token
        channel: Slack channel to send the message to
        project_name: Name shown in the username field
        icon: Slack emoji icon (e.g. ':alert:')
        color: Attachment color (e.g. 'good', 'danger', or hex)
        message: Message text (mrkdwn)
    """
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "channel": channel,
        "username": f"{project_name} CI Notifier",
        "icon_emoji": icon,
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }
        ]
    }

    eprint(f"Sending Slack notification to {channel}...")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        eprint(f"Error: Failed to send Slack notification. Status: {response.status_code}")
        eprint(f"Response: {response.text}")
        sys.exit(1)

    result = response.json()
    if not result.get('ok'):
        eprint(f"Error: Slack API error: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    eprint("Slack notification sent successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Send a Slack notification.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--channel", required=True,
                        help="Slack channel to send the notification to.")
    parser.add_argument("--project-name", required=True,
                        help="Project name shown in the Slack username.")
    parser.add_argument("--icon", default=":alert:",
                        help="Slack emoji icon.")
    parser.add_argument("--color", default="danger",
                        help="Attachment color (e.g. good, danger, warning, or hex).")
    parser.add_argument("--message", required=True,
                        help="Message text (mrkdwn format).")

    args = parser.parse_args()
    slack_token = require_env_token('SLACK_TOKEN')

    send_slack_notification(
        slack_token=slack_token,
        channel=normalize_channel(args.channel),
        project_name=args.project_name,
        icon=args.icon,
        color=args.color,
        message=args.message,
    )


if __name__ == "__main__":
    main()
