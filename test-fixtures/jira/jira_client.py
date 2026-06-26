#!/usr/bin/env python3
"""Shared Jira connection helper for test fixtures."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from path_utils import safe_path
from jira_common import eprint, get_jira_instance, JIRA_URL_PROD, JIRA_URL_SANDBOX
