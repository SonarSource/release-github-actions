#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared utility functions for lock-branch action scripts.
"""

import os
import sys


def eprint(*args, **kwargs):
    """
    Prints messages to the standard error stream (stderr).

    This function serves as a dedicated logger for informational messages,
    warnings, or errors. In a CI/CD pipeline, this ensures that diagnostic
    output is kept separate from the primary result of the script, which is
    written to standard output (stdout).
    """
    print(*args, file=sys.stderr, **kwargs)


def parse_bool(value):
    """Parses a boolean from string."""
    if isinstance(value, bool):
        return value
    return value.lower() in ('true', '1', 'yes')


def require_env_token(name):
    """
    Gets a required token from environment variable.

    Args:
        name: Environment variable name

    Returns:
        str: The token value

    Exits with code 1 if the token is not set.
    """
    token = os.environ.get(name)
    if not token:
        eprint(f"Error: {name} environment variable must be set.")
        sys.exit(1)
    return token
