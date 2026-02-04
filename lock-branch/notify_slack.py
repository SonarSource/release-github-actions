#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script sends a Slack notification about a branch lock/unlock state change.
"""

import argparse
import sys
import requests

from utils import eprint, parse_bool, require_env_token


def get_slack_token():
    """Gets Slack token from environment."""
    return require_env_token('SLACK_TOKEN')


def normalize_channel(channel):
    """Ensures channel name starts with '#'."""
    if not channel.startswith('#'):
        return f'#{channel}'
    return channel


def send_slack_notification(slack_token, channel, branch, repository, freeze, run_url):
    """
    Sends a Slack notification about the branch lock state change.

    Args:
        slack_token: Slack API token
        channel: Slack channel to send the message to
        branch: Branch name that was locked/unlocked
        repository: Repository in format "owner/repo"
        freeze: True if branch was locked, False if unlocked
        run_url: URL to the GitHub Actions run
    """
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {slack_token}",
        "Content-Type": "application/json"
    }

    icon = ":ice_cube:" if freeze else ":sun_with_face:"
    action = "frozen" if freeze else "unfrozen"
    color = "warning" if freeze else "good"

    payload = {
        "channel": channel,
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{icon} Branch `{branch}` has been {action} in `{repository}`"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Run:* <{run_url}|View workflow run>"
                            }
                        ]
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
    """Main function to parse arguments and send Slack notification."""
    parser = argparse.ArgumentParser(
        description="Send a Slack notification about a branch lock/unlock state change.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--channel", required=True,
                        help="Slack channel to send the notification to.")
    parser.add_argument("--branch", required=True,
                        help="The branch name that was locked/unlocked.")
    parser.add_argument("--repository", required=True,
                        help="The repository in format 'owner/repo'.")
    parser.add_argument("--freeze", required=True,
                        help="Set to 'true' if branch was locked, 'false' if unlocked.")
    parser.add_argument("--run-url", required=True,
                        help="URL to the GitHub Actions run.")

    args = parser.parse_args()

    freeze = parse_bool(args.freeze)
    slack_token = get_slack_token()

    send_slack_notification(
        slack_token=slack_token,
        channel=normalize_channel(args.channel),
        branch=args.branch,
        repository=args.repository,
        freeze=freeze,
        run_url=args.run_url
    )


if __name__ == "__main__":
    main()
