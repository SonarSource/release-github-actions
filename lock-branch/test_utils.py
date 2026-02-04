#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for utils.py
"""

import unittest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import eprint, parse_bool, require_env_token


class TestUtils(unittest.TestCase):

    def test_parse_bool_true_values(self):
        """Test parsing true values."""
        self.assertTrue(parse_bool('true'))
        self.assertTrue(parse_bool('True'))
        self.assertTrue(parse_bool('TRUE'))
        self.assertTrue(parse_bool('1'))
        self.assertTrue(parse_bool('yes'))
        self.assertTrue(parse_bool(True))

    def test_parse_bool_false_values(self):
        """Test parsing false values."""
        self.assertFalse(parse_bool('false'))
        self.assertFalse(parse_bool('False'))
        self.assertFalse(parse_bool('FALSE'))
        self.assertFalse(parse_bool('0'))
        self.assertFalse(parse_bool('no'))
        self.assertFalse(parse_bool(False))

    @patch.dict(os.environ, {'TEST_TOKEN': 'my-token'})
    def test_require_env_token_present(self):
        """Test requiring a token that exists."""
        self.assertEqual(require_env_token('TEST_TOKEN'), 'my-token')

    @patch.dict(os.environ, {}, clear=True)
    def test_require_env_token_missing(self):
        """Test requiring a token that doesn't exist causes exit."""
        with self.assertRaises(SystemExit) as cm:
            require_env_token('NONEXISTENT_TOKEN')
        self.assertEqual(cm.exception.code, 1)

    @patch('sys.stderr')
    def test_eprint_writes_to_stderr(self, mock_stderr):
        """Test that eprint writes to stderr."""
        eprint("test message")
        mock_stderr.write.assert_called()


if __name__ == '__main__':
    unittest.main()
