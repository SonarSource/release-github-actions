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
from unittest.mock import Mock, patch, call

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notify_failure import (
    build_message,
    extract_develocity_url,
    extract_root_cause,
    extract_test_counts,
    get_consecutive_failures,
    get_jobs_info,
    get_run_info,
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


class TestGetRunInfo(unittest.TestCase):

    def _run_response(self, pr_number=None, workflow_id=42):
        mock = Mock()
        mock.status_code = 200
        pull_requests = []
        if pr_number:
            pull_requests = [{"number": pr_number}]
        mock.json.return_value = {"workflow_id": workflow_id, "pull_requests": pull_requests}
        return mock

    def _pr_response(self, title, html_url):
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {"title": title, "html_url": html_url}
        return mock

    @patch("notify_failure.requests.get")
    def test_returns_pr_info_and_workflow_id(self, mock_get):
        mock_get.side_effect = [
            self._run_response(pr_number=42, workflow_id=999),
            self._pr_response("Fix auth bug", "https://github.com/org/repo/pull/42"),
        ]
        info = get_run_info("token", "org/repo", "123")
        self.assertEqual(info["pr_number"], 42)
        self.assertEqual(info["pr_title"], "Fix auth bug")
        self.assertEqual(info["pr_url"], "https://github.com/org/repo/pull/42")
        self.assertEqual(info["workflow_id"], 999)

    @patch("notify_failure.requests.get")
    def test_no_pr_returns_none_pr_fields(self, mock_get):
        mock_get.return_value = self._run_response(pr_number=None, workflow_id=999)
        info = get_run_info("token", "org/repo", "123")
        self.assertIsNone(info["pr_number"])
        self.assertIsNone(info["pr_title"])
        self.assertIsNone(info["pr_url"])
        self.assertEqual(info["workflow_id"], 999)

    @patch("notify_failure.requests.get")
    def test_run_api_error_returns_empty(self, mock_get):
        mock_get.return_value = Mock(status_code=403, json=Mock(return_value={}))
        info = get_run_info("token", "org/repo", "123")
        self.assertIsNone(info["workflow_id"])
        self.assertIsNone(info["pr_number"])

    @patch("notify_failure.requests.get")
    def test_exception_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("network error")
        info = get_run_info("token", "org/repo", "123")
        self.assertIsNone(info["workflow_id"])
        self.assertIsNone(info["pr_number"])


class TestGetJobsInfo(unittest.TestCase):

    def _jobs_response(self, steps=None):
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            "jobs": [
                {
                    "id": 1,
                    "name": "build",
                    "conclusion": "failure",
                    "html_url": "https://github.com/org/repo/actions/runs/1/job/1",
                    "steps": steps or [
                        {"name": "Checkout", "conclusion": "success", "number": 1},
                        {"name": "Run tests", "conclusion": "failure", "number": 2},
                    ],
                },
                {
                    "id": 2,
                    "name": "test",
                    "conclusion": "success",
                    "html_url": "https://github.com/org/repo/actions/runs/1/job/2",
                    "steps": [],
                },
            ]
        }
        return mock

    def _log_response(self, text):
        mock = Mock()
        mock.status_code = 200
        mock.text = text
        return mock

    @patch("notify_failure.requests.get")
    def test_returns_logs_urls_and_failed_steps(self, mock_get):
        mock_get.side_effect = [
            self._jobs_response(),
            self._log_response("BUILD FAILURE"),
        ]
        logs, job_urls, failed_steps = get_jobs_info("token", "SonarSource/repo", "123")
        self.assertIn("build", logs)
        self.assertNotIn("test", logs)
        self.assertEqual(job_urls["build"], "https://github.com/org/repo/actions/runs/1/job/1")
        self.assertNotIn("test", job_urls)
        self.assertEqual(failed_steps["build"], "Run tests")

    @patch("notify_failure.requests.get")
    def test_no_failed_step_when_all_steps_succeed(self, mock_get):
        mock_get.side_effect = [
            self._jobs_response(steps=[
                {"name": "Checkout", "conclusion": "success", "number": 1},
            ]),
            self._log_response(""),
        ]
        _, _, failed_steps = get_jobs_info("token", "SonarSource/repo", "123")
        self.assertNotIn("build", failed_steps)

    @patch("notify_failure.requests.get")
    def test_jobs_api_error_returns_empty(self, mock_get):
        mock_get.return_value = Mock(status_code=403, json=Mock(return_value={}))
        logs, job_urls, failed_steps = get_jobs_info("token", "SonarSource/repo", "123")
        self.assertEqual(logs, {})
        self.assertEqual(job_urls, {})
        self.assertEqual(failed_steps, {})

    @patch("notify_failure.requests.get")
    def test_exception_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        logs, job_urls, failed_steps = get_jobs_info("token", "SonarSource/repo", "123")
        self.assertEqual(logs, {})
        self.assertEqual(job_urls, {})
        self.assertEqual(failed_steps, {})

    @patch("notify_failure.requests.get")
    def test_logs_truncated_to_200_lines(self, mock_get):
        long_log = "\n".join([f"line {i}" for i in range(500)])
        mock_get.side_effect = [
            self._jobs_response(),
            self._log_response(long_log),
        ]
        logs, _, _ = get_jobs_info("token", "SonarSource/repo", "123")
        self.assertEqual(len(logs["build"].splitlines()), 200)


class TestGetConsecutiveFailures(unittest.TestCase):

    def _runs_response(self, runs):
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {"workflow_runs": runs}
        return mock

    @patch("notify_failure.requests.get")
    def test_counts_consecutive_failures(self, mock_get):
        mock_get.return_value = self._runs_response([
            {"id": 999, "conclusion": "success"},  # current run (skipped)
            {"id": 998, "conclusion": "failure"},
            {"id": 997, "conclusion": "failure"},
            {"id": 996, "conclusion": "success"},
        ])
        count = get_consecutive_failures("token", "org/repo", "wf1", "main", "999")
        self.assertEqual(count, 2)

    @patch("notify_failure.requests.get")
    def test_stops_at_success(self, mock_get):
        mock_get.return_value = self._runs_response([
            {"id": 999, "conclusion": "success"},  # current (skipped)
            {"id": 998, "conclusion": "success"},
            {"id": 997, "conclusion": "failure"},
        ])
        count = get_consecutive_failures("token", "org/repo", "wf1", "main", "999")
        self.assertEqual(count, 0)

    @patch("notify_failure.requests.get")
    def test_api_error_returns_zero(self, mock_get):
        mock_get.return_value = Mock(status_code=403, json=Mock(return_value={}))
        count = get_consecutive_failures("token", "org/repo", "wf1", "main", "999")
        self.assertEqual(count, 0)

    @patch("notify_failure.requests.get")
    def test_exception_returns_zero(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        count = get_consecutive_failures("token", "org/repo", "wf1", "main", "999")
        self.assertEqual(count, 0)

    def test_no_workflow_id_returns_zero(self):
        count = get_consecutive_failures("token", "org/repo", "", "main", "999")
        self.assertEqual(count, 0)


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


class TestExtractTestCounts(unittest.TestCase):

    def test_finds_surefire_line(self):
        logs = {"build": "Tests run: 42, Failures: 3, Errors: 1, Skipped: 0"}
        result = extract_test_counts(logs)
        self.assertEqual(result, (42, 3, 1))

    def test_aggregates_multiple_lines(self):
        logs = {"build": (
            "Tests run: 10, Failures: 1, Errors: 0, Skipped: 0\n"
            "Tests run: 20, Failures: 2, Errors: 1, Skipped: 0"
        )}
        result = extract_test_counts(logs)
        self.assertEqual(result, (30, 3, 1))

    def test_all_passing_returns_none(self):
        logs = {"build": "Tests run: 42, Failures: 0, Errors: 0, Skipped: 0"}
        self.assertIsNone(extract_test_counts(logs))

    def test_no_surefire_output_returns_none(self):
        logs = {"build": "No test output here"}
        self.assertIsNone(extract_test_counts(logs))

    def test_empty_logs_returns_none(self):
        self.assertIsNone(extract_test_counts({}))

    def test_aggregates_across_jobs(self):
        logs = {
            "build": "Tests run: 10, Failures: 1, Errors: 0, Skipped: 0",
            "test": "Tests run: 5, Failures: 0, Errors: 2, Skipped: 0",
        }
        result = extract_test_counts(logs)
        self.assertEqual(result, (15, 1, 2))


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
            ref_name="main",
            workflow="Java CI",
            run_id="123456789",
            run_attempt="2",
            actor="janedoe",
            server_url="https://github.com",
            failed_job_names=["qa_plugin", "build"],
            job_urls={
                "qa_plugin": "https://github.com/SonarSource/sonar-php/actions/runs/123456789/job/1",
                "build": "https://github.com/SonarSource/sonar-php/actions/runs/123456789/job/2",
            },
            failed_steps={"qa_plugin": "Run unit tests"},
            pr_number=42,
            pr_title="Fix authentication bug",
            pr_url="https://github.com/SonarSource/sonar-php/pull/42",
            consecutive_failures=3,
            root_cause="error: method analyze(UCFG) is not public",
            test_counts=(42, 3, 1),
            develocity_url="https://develocity.sonar.build/s/bobyeotpte5wm",
            include_run_attempt=True,
            include_failed_step=True,
            include_flakiness=True,
            include_test_counts=True,
        )
        kwargs.update(overrides)
        return kwargs

    def test_contains_repo_link(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("<https://github.com/SonarSource/sonar-php|SonarSource/sonar-php>", msg)

    def test_contains_run_url(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("https://github.com/SonarSource/sonar-php/actions/runs/123456789", msg)

    def test_contains_failed_job_links(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("qa_plugin", msg)
        self.assertIn("/job/1", msg)

    def test_failed_step_shown_after_job(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("Run unit tests", msg)
        self.assertIn("step:", msg)

    def test_failed_step_omitted_when_disabled(self):
        msg = build_message(**self._default_kwargs(include_failed_step=False))
        self.assertNotIn("step:", msg)

    def test_failed_step_omitted_when_no_step_info(self):
        msg = build_message(**self._default_kwargs(failed_steps={}))
        self.assertNotIn("step:", msg)

    def test_pr_line_shown(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("#42", msg)
        self.assertIn("Fix authentication bug", msg)
        self.assertIn("https://github.com/SonarSource/sonar-php/pull/42", msg)

    def test_pr_line_omitted_when_none(self):
        msg = build_message(**self._default_kwargs(pr_number=None, pr_title=None, pr_url=None))
        self.assertNotIn("PR:", msg)

    def test_flakiness_shown_when_consecutive_ge_2(self):
        msg = build_message(**self._default_kwargs(consecutive_failures=3))
        self.assertIn("Flaky", msg)
        self.assertIn("3", msg)

    def test_flakiness_omitted_when_less_than_2(self):
        msg = build_message(**self._default_kwargs(consecutive_failures=1))
        self.assertNotIn("Flaky", msg)

    def test_flakiness_omitted_when_zero(self):
        msg = build_message(**self._default_kwargs(consecutive_failures=0))
        self.assertNotIn("Flaky", msg)

    def test_flakiness_omitted_when_disabled(self):
        msg = build_message(**self._default_kwargs(include_flakiness=False, consecutive_failures=5))
        self.assertNotIn("Flaky", msg)

    def test_test_counts_shown(self):
        msg = build_message(**self._default_kwargs(test_counts=(42, 3, 1)))
        self.assertIn("Test Failures", msg)
        self.assertIn("3 failures", msg)
        self.assertIn("1 error", msg)
        self.assertIn("42 tests", msg)

    def test_test_counts_omitted_when_none(self):
        msg = build_message(**self._default_kwargs(test_counts=None))
        self.assertNotIn("Test Failures", msg)

    def test_test_counts_omitted_when_disabled(self):
        msg = build_message(**self._default_kwargs(include_test_counts=False))
        self.assertNotIn("Test Failures", msg)

    def test_contains_root_cause(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("method analyze(UCFG)", msg)

    def test_root_cause_omitted_when_none(self):
        msg = build_message(**self._default_kwargs(root_cause=None))
        self.assertNotIn("Root Cause", msg)

    def test_contains_develocity_link(self):
        msg = build_message(**self._default_kwargs())
        self.assertIn("develocity.sonar.build", msg)

    def test_develocity_omitted_when_none(self):
        msg = build_message(**self._default_kwargs(develocity_url=None))
        self.assertNotIn("Build Scan", msg)

    def test_attempt_shown_when_enabled(self):
        msg = build_message(**self._default_kwargs(include_run_attempt=True))
        self.assertIn("Attempt", msg)

    def test_attempt_omitted_when_disabled(self):
        msg = build_message(**self._default_kwargs(include_run_attempt=False))
        self.assertNotIn("Attempt", msg)

    def test_unknown_failed_jobs(self):
        msg = build_message(**self._default_kwargs(failed_job_names=[], job_urls={}))
        self.assertIn("unknown", msg)

    def test_no_commit_info_in_message(self):
        msg = build_message(**self._default_kwargs())
        self.assertNotIn("Last Commit", msg)
        self.assertNotIn("Author:", msg)

    def test_singular_failure_grammar(self):
        msg = build_message(**self._default_kwargs(test_counts=(10, 1, 1)))
        self.assertIn("1 failure", msg)
        self.assertIn("1 error", msg)
        self.assertNotIn("1 failures", msg)
        self.assertNotIn("1 errors", msg)


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
