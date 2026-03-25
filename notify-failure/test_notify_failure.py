#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for notify_failure.py
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notify_failure import (
    build_message,
    extract_develocity_url,
    extract_root_cause,
    get_commit_info,
    get_job_logs,
    is_enabled,
    parse_failed_jobs,
    write_output,
)


class TestIsEnabled(unittest.TestCase):

    def test_true_by_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SOME_FLAG", None)
            self.assertTrue(is_enabled("SOME_FLAG"))

    def test_false_string(self):
        with patch.dict(os.environ, {"SOME_FLAG": "false"}):
            self.assertFalse(is_enabled("SOME_FLAG"))

    def test_zero_string(self):
        with patch.dict(os.environ, {"SOME_FLAG": "0"}):
            self.assertFalse(is_enabled("SOME_FLAG"))

    def test_true_string(self):
        with patch.dict(os.environ, {"SOME_FLAG": "true"}):
            self.assertTrue(is_enabled("SOME_FLAG"))


class TestParseFailedJobs(unittest.TestCase):

    def test_returns_failed_jobs(self):
        needs = {"build": {"result": "failure"}, "test": {"result": "success"}}
        self.assertEqual(parse_failed_jobs(json.dumps(needs)), ["build"])

    def test_all_success(self):
        needs = {"build": {"result": "success"}, "test": {"result": "success"}}
        self.assertEqual(parse_failed_jobs(json.dumps(needs)), [])

    def test_multiple_failures(self):
        needs = {
            "build": {"result": "failure"},
            "test": {"result": "failure"},
            "deploy": {"result": "success"},
        }
        result = parse_failed_jobs(json.dumps(needs))
        self.assertIn("build", result)
        self.assertIn("test", result)
        self.assertNotIn("deploy", result)

    def test_empty_needs(self):
        self.assertEqual(parse_failed_jobs("{}"), [])

    def test_invalid_json(self):
        self.assertEqual(parse_failed_jobs("not-json"), [])


class TestGetCommitInfo(unittest.TestCase):

    def _mock_response(self, status_code=200, data=None):
        mock = Mock()
        mock.status_code = status_code
        mock.json.return_value = data or {}
        return mock

    @patch("notify_failure.requests.get")
    def test_returns_author_and_message(self, mock_get):
        mock_get.return_value = self._mock_response(data={
            "commit": {
                "author": {"name": "Jane Doe"},
                "message": "Fix authentication bug\n\nDetailed description.",
            }
        })
        author, msg = get_commit_info("token", "SonarSource/repo", "abc1234")
        self.assertEqual(author, "Jane Doe")
        self.assertEqual(msg, "Fix authentication bug")

    @patch("notify_failure.requests.get")
    def test_http_error_returns_fallback(self, mock_get):
        mock_get.return_value = self._mock_response(status_code=404)
        author, msg = get_commit_info("token", "SonarSource/repo", "abc1234")
        self.assertEqual(author, "Unknown")
        self.assertEqual(msg, "Unknown commit")

    @patch("notify_failure.requests.get")
    def test_exception_returns_fallback(self, mock_get):
        mock_get.side_effect = Exception("network error")
        author, msg = get_commit_info("token", "SonarSource/repo", "abc1234")
        self.assertEqual(author, "Unknown")
        self.assertEqual(msg, "Unknown commit")


class TestGetJobLogs(unittest.TestCase):

    def _jobs_response(self):
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            "jobs": [
                {"id": 1, "name": "build", "conclusion": "failure"},
                {"id": 2, "name": "test", "conclusion": "success"},
            ]
        }
        return mock

    def _log_response(self, text):
        mock = Mock()
        mock.status_code = 200
        mock.text = text
        return mock

    @patch("notify_failure.requests.get")
    def test_returns_logs_for_failed_jobs_only(self, mock_get):
        mock_get.side_effect = [
            self._jobs_response(),
            self._log_response("BUILD FAILURE"),
        ]
        logs = get_job_logs("token", "SonarSource/repo", "123")
        self.assertIn("build", logs)
        self.assertNotIn("test", logs)
        self.assertIn("BUILD FAILURE", logs["build"])

    @patch("notify_failure.requests.get")
    def test_jobs_api_error_returns_empty(self, mock_get):
        mock_get.return_value = Mock(status_code=403, json=Mock(return_value={}))
        logs = get_job_logs("token", "SonarSource/repo", "123")
        self.assertEqual(logs, {})

    @patch("notify_failure.requests.get")
    def test_exception_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        logs = get_job_logs("token", "SonarSource/repo", "123")
        self.assertEqual(logs, {})

    @patch("notify_failure.requests.get")
    def test_logs_truncated_to_200_lines(self, mock_get):
        long_log = "\n".join([f"line {i}" for i in range(500)])
        mock_get.side_effect = [
            self._jobs_response(),
            self._log_response(long_log),
        ]
        logs = get_job_logs("token", "SonarSource/repo", "123")
        self.assertEqual(len(logs["build"].splitlines()), 200)


class TestExtractRootCause(unittest.TestCase):

    def test_javac_error(self):
        logs = {"build": "2024-01-01T00:00:00.000Z [ERROR] error: method analyze(UCFG) is not public"}
        result = extract_root_cause(logs)
        self.assertIsNotNone(result)
        self.assertIn("method analyze", result)

    def test_build_failure(self):
        logs = {"build": "some output\n[INFO] BUILD FAILURE\nmore output"}
        result = extract_root_cause(logs)
        self.assertIsNotNone(result)
        self.assertIn("BUILD FAILURE", result)

    def test_skips_download_lines(self):
        logs = {"build": "Downloading from central: https://repo1.maven.org/artifact\nBUILD FAILURE"}
        result = extract_root_cause(logs)
        self.assertIsNotNone(result)
        self.assertNotIn("Downloading", result)

    def test_no_error_returns_none(self):
        logs = {"build": "Everything looks fine\nAll tests passed"}
        self.assertIsNone(extract_root_cause(logs))

    def test_empty_logs_returns_none(self):
        self.assertIsNone(extract_root_cause({}))

    def test_long_line_truncated(self):
        logs = {"build": "error: " + "x" * 200}
        result = extract_root_cause(logs)
        self.assertIsNotNone(result)
        self.assertLessEqual(len(result), 120)

    def test_strips_error_prefix(self):
        logs = {"build": "[ERROR] error: some compilation error here"}
        result = extract_root_cause(logs)
        self.assertNotIn("[ERROR]", result)


class TestExtractDevelocityUrl(unittest.TestCase):

    def test_finds_develocity_url(self):
        logs = {"build": "[INFO] https://develocity.sonar.build/s/bobyeotpte5wm\nmore output"}
        result = extract_develocity_url(logs)
        self.assertEqual(result, "https://develocity.sonar.build/s/bobyeotpte5wm")

    def test_returns_first_match(self):
        logs = {
            "build": "https://develocity.sonar.build/s/aaa111",
            "test": "https://develocity.sonar.build/s/bbb222",
        }
        result = extract_develocity_url(logs)
        self.assertIn(result, [
            "https://develocity.sonar.build/s/aaa111",
            "https://develocity.sonar.build/s/bbb222",
        ])

    def test_no_url_returns_none(self):
        logs = {"build": "No scan link in this log"}
        self.assertIsNone(extract_develocity_url(logs))

    def test_empty_logs_returns_none(self):
        self.assertIsNone(extract_develocity_url({}))


class TestBuildMessage(unittest.TestCase):

    def _default_kwargs(self, **overrides):
        kwargs = dict(
            repo="SonarSource/sonar-php",
            sha="abc1234def5678",
            ref_name="main",
            workflow="Java CI",
            run_id="123456789",
            run_attempt="2",
            actor="janedoe",
            server_url="https://github.com",
            failed_jobs=["qa_plugin", "build"],
            author="Jane Doe",
            commit_msg="Fix authentication bug",
            root_cause="error: method analyze(UCFG) is not public",
            develocity_url="https://develocity.sonar.build/s/bobyeotpte5wm",
            include_run_attempt=True,
        )
        kwargs.update(overrides)
        return kwargs

    def test_contains_repo_link(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("<https://github.com/SonarSource/sonar-php|SonarSource/sonar-php>", msg)

    def test_contains_run_url(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("https://github.com/SonarSource/sonar-php/actions/runs/123456789", msg)

    def test_contains_failed_jobs(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("qa_plugin", msg)
        self.assertIn("build", msg)

    def test_contains_short_sha(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("abc1234", msg)
        self.assertNotIn("abc1234def5678", msg)  # full SHA should not appear

    def test_contains_author(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("Jane Doe", msg)
        self.assertIn("janedoe", msg)

    def test_contains_root_cause(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("method analyze(UCFG)", msg)

    def test_contains_develocity_link(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("develocity.sonar.build", msg)

    def test_attempt_shown_when_enabled(self):
        msg = build_message(**self._default_kwargs(include_run_attempt=True))
        self.assertIn("Attempt", msg)
        self.assertIn("2", msg)

    def test_attempt_omitted_when_disabled(self):
        msg = build_message(**self._default_kwargs(include_run_attempt=False))
        self.assertNotIn("Attempt", msg)

    def test_commit_omitted_when_none(self):
        msg = build_message(**self._default_kwargs(author=None, commit_msg=None))
        self.assertNotIn("Last Commit", msg)
        self.assertNotIn("Author", msg)

    def test_root_cause_omitted_when_none(self):
        msg = build_message(**self._default_kwargs(root_cause=None))
        self.assertNotIn("Root Cause", msg)

    def test_develocity_omitted_when_none(self):
        msg = build_message(**self._default_kwargs(develocity_url=None))
        self.assertNotIn("Build Scan", msg)
        self.assertNotIn("develocity", msg)

    def test_unknown_failed_jobs(self):
        msg = build_message(**self._default_kwargs(failed_jobs=[]))
        self.assertIn("unknown", msg)


class TestWriteOutput(unittest.TestCase):

    def test_writes_to_github_output(self):
        with tempfile.NamedTemporaryFile(mode="r", suffix=".env", delete=False) as f:
            tmp_path = f.name
        try:
            with patch.dict(os.environ, {"GITHUB_OUTPUT": tmp_path}):
                write_output("Hello\nWorld")
            with open(tmp_path) as f:
                content = f.read()
            self.assertIn("message<<", content)
            self.assertIn("Hello\nWorld", content)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
