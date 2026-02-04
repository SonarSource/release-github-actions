#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script locks or unlocks a GitHub branch by modifying the branch protection
lock_branch setting.
"""

import argparse
import sys
import requests

from utils import eprint, parse_bool, require_env_token


def get_github_token():
    """Gets GitHub token from environment."""
    return require_env_token('GITHUB_TOKEN')


def get_branch_protection(token, repository, branch):
    """
    Gets the current branch protection settings.

    Args:
        token: GitHub API token
        repository: Repository in format "owner/repo"
        branch: Branch name

    Returns:
        dict: The branch protection settings, or None if not found.
    """
    url = f"https://api.github.com/repos/{repository}/branches/{branch}/protection"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    eprint(f"Fetching branch protection for {repository}/{branch}...")
    response = requests.get(url, headers=headers)

    if response.status_code == 404:
        eprint(f"Warning: No branch protection found for branch '{branch}'.")
        return None
    elif response.status_code != 200:
        eprint(f"Error: Failed to get branch protection. Status: {response.status_code}")
        eprint(f"Response: {response.text}")
        sys.exit(1)

    return response.json()


def is_branch_locked(protection_settings):
    """
    Checks if the branch is currently locked.

    Args:
        protection_settings: The branch protection settings dict.

    Returns:
        bool: True if locked, False otherwise.
    """
    if protection_settings is None:
        return False

    lock_branch = protection_settings.get('lock_branch', {})
    return lock_branch.get('enabled', False)


def build_protection_payload(current_protection, lock):
    """
    Builds the branch protection payload, preserving existing settings.

    Args:
        current_protection: Current branch protection settings (can be None)
        lock: Whether to lock the branch

    Returns:
        dict: The payload for updating branch protection
    """
    if current_protection is None:
        # Create minimal protection with lock_branch and sensible defaults
        return {
            "required_status_checks": None,
            "enforce_admins": True,
            "required_pull_request_reviews": None,
            "restrictions": None,
            "lock_branch": lock,
            "required_linear_history": True,
            "allow_force_pushes": False,
            "allow_deletions": False,
            "block_creations": False,
            "required_conversation_resolution": False,
            "allow_fork_syncing": False
        }

    # Preserve existing settings while updating lock_branch
    payload = {
        "lock_branch": lock,
        "enforce_admins": current_protection.get('enforce_admins', {}).get('enabled', False),
    }

    # Handle required_status_checks
    status_checks = current_protection.get('required_status_checks')
    if status_checks:
        payload["required_status_checks"] = {
            "strict": status_checks.get('strict', False),
            "contexts": status_checks.get('contexts', [])
        }
    else:
        payload["required_status_checks"] = None

    # Handle required_pull_request_reviews
    pr_reviews = current_protection.get('required_pull_request_reviews')
    if pr_reviews:
        payload["required_pull_request_reviews"] = {
            "dismiss_stale_reviews": pr_reviews.get('dismiss_stale_reviews', False),
            "require_code_owner_reviews": pr_reviews.get('require_code_owner_reviews', False),
            "required_approving_review_count": pr_reviews.get('required_approving_review_count', 0)
        }
    else:
        payload["required_pull_request_reviews"] = None

    # Handle restrictions
    restrictions = current_protection.get('restrictions')
    if restrictions:
        payload["restrictions"] = {
            "users": [u['login'] for u in restrictions.get('users', [])],
            "teams": [t['slug'] for t in restrictions.get('teams', [])],
            "apps": [a['slug'] for a in restrictions.get('apps', [])]
        }
    else:
        payload["restrictions"] = None

    # Preserve optional boolean settings
    payload["required_linear_history"] = current_protection.get(
        'required_linear_history', {}).get('enabled', False)
    payload["allow_force_pushes"] = current_protection.get(
        'allow_force_pushes', {}).get('enabled', False)
    payload["allow_deletions"] = current_protection.get(
        'allow_deletions', {}).get('enabled', False)
    payload["block_creations"] = current_protection.get(
        'block_creations', {}).get('enabled', False)
    payload["required_conversation_resolution"] = current_protection.get(
        'required_conversation_resolution', {}).get('enabled', False)
    payload["allow_fork_syncing"] = current_protection.get(
        'allow_fork_syncing', {}).get('enabled', False)

    return payload


def update_branch_lock(token, repository, branch, lock, current_protection):
    """
    Updates the branch protection to lock or unlock the branch.

    Args:
        token: GitHub API token
        repository: Repository in format "owner/repo"
        branch: Branch name
        lock: True to lock, False to unlock
        current_protection: Current branch protection settings
    """
    url = f"https://api.github.com/repos/{repository}/branches/{branch}/protection"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Build the request payload preserving existing settings
    payload = build_protection_payload(current_protection, lock)

    action = "Locking" if lock else "Unlocking"
    eprint(f"{action} branch '{branch}'...")

    response = requests.put(url, headers=headers, json=payload)

    if response.status_code not in [200, 201]:
        eprint(f"Error: Failed to update branch protection. Status: {response.status_code}")
        eprint(f"Response: {response.text}")
        sys.exit(1)

    eprint(f"Successfully {'locked' if lock else 'unlocked'} branch '{branch}'.")
    return response.json()


def main():
    """Main function to parse arguments and execute the lock/unlock operation."""
    parser = argparse.ArgumentParser(
        description="Lock or unlock a GitHub branch by modifying branch protection settings.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--branch", required=True,
                        help="The branch name to lock/unlock.")
    parser.add_argument("--freeze", required=True,
                        help="Set to 'true' to lock (freeze), 'false' to unlock (unfreeze).")
    parser.add_argument("--repository", required=True,
                        help="The repository in format 'owner/repo'.")

    args = parser.parse_args()

    freeze = parse_bool(args.freeze)
    token = get_github_token()

    # Get current protection settings
    current_protection = get_branch_protection(token, args.repository, args.branch)
    previous_locked = is_branch_locked(current_protection)

    eprint(f"Current lock state: {'locked' if previous_locked else 'unlocked'}")
    eprint(f"Requested state: {'locked' if freeze else 'unlocked'}")

    if previous_locked == freeze:
        eprint(f"Branch is already {'locked' if freeze else 'unlocked'}. No action needed.")
    else:
        update_branch_lock(token, args.repository, args.branch, freeze, current_protection)

    # Output results for GitHub Actions
    eprint("\n" + "=" * 50)
    eprint(f"{'Froze' if freeze else 'Unfroze'} branch: {args.branch}")
    eprint(f"Previous state: {'locked' if previous_locked else 'unlocked'}")
    eprint(f"Current state: {'locked' if freeze else 'unlocked'}")
    eprint("=" * 50)

    # Output for GitHub Actions (stdout -> GITHUB_OUTPUT)
    print(f"previous_state={str(previous_locked).lower()}")
    print(f"current_state={str(freeze).lower()}")
    print(f"branch={args.branch}")


if __name__ == "__main__":
    main()
