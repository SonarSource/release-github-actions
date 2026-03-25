#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Builds a rich Slack failure notification message from GitHub context and the GitHub API.
Writes the message to GITHUB_OUTPUT.
"""

import json
import os
import re
import requests
import secrets
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def is_enabled(env_var):
    return os.environ.get(env_var, "true").lower() not in ("false", "0", "no")


def parse_failed_jobs(needs_json):
    """Extract job names where result == 'failure' from toJSON(needs)."""
    try:
        needs = json.loads(needs_json)
        return [k for k, v in needs.items() if v.get("result") == "failure"]
    except (json.JSONDecodeError, AttributeError):
        eprint("Warning: Failed to parse needs JSON")
        return []


def get_jobs_info(token, repository, run_id):
    """Fetch info for all jobs in the run.

    Returns a tuple:
      - logs: {job_name: log_text} for failed jobs (last 200 lines each)
      - job_urls: {job_name: html_url} for failed jobs

    Returns ({}, {}) on any error.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    jobs_url = f"https://api.github.com/repos/{repository}/actions/runs/{run_id}/jobs"
    try:
        response = requests.get(jobs_url, headers=headers, timeout=10)
        if response.status_code != 200:
            eprint(f"Warning: Could not fetch jobs list (status {response.status_code})")
            return {}, {}
        jobs = response.json().get("jobs", [])
    except Exception as exc:
        eprint(f"Warning: Failed to fetch jobs: {exc}")
        return {}, {}

    failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
    job_urls = {j["name"]: j["html_url"] for j in failed_jobs}

    logs = {}
    for job in failed_jobs:
        job_id = job["id"]
        job_name = job["name"]
        log_url = f"https://api.github.com/repos/{repository}/actions/jobs/{job_id}/logs"
        try:
            # Logs endpoint redirects to a pre-signed URL; allow_redirects=True handles it.
            log_response = requests.get(log_url, headers=headers, timeout=30, allow_redirects=True)
            if log_response.status_code == 200:
                lines = log_response.text.splitlines()
                logs[job_name] = "\n".join(lines[-200:])
            else:
                eprint(f"Warning: Could not fetch logs for job '{job_name}' (status {log_response.status_code})")
        except Exception as exc:
            eprint(f"Warning: Failed to fetch logs for job '{job_name}': {exc}")
    return logs, job_urls


# Patterns that indicate a meaningful error line (order matters — checked top to bottom)
_ERROR_PATTERNS = [
    re.compile(r"\berror:\s+.{5,}", re.IGNORECASE),          # javac: "error: method X is not public"
    re.compile(r"\bEXCEPTION\b", re.IGNORECASE),             # Exception in thread / ExceptionInInitializerError
    re.compile(r"\bBUILD FAILURE\b"),                         # Maven BUILD FAILURE
    re.compile(r"\bFAILED\b"),                                # General FAILED marker
    re.compile(r"AssertionError"),                            # Test assertion failures
    re.compile(r"^\s*at .+\(.+:\d+\)$"),                     # Stack trace lines
]

# Patterns to skip (noisy lines that aren't useful root cause info)
_SKIP_PATTERNS = [
    re.compile(r"Downloading(?: from)?\s+http", re.IGNORECASE),
    re.compile(r"Downloaded\s+http", re.IGNORECASE),
    re.compile(r"Progress\s*\(\d+/\d+\)", re.IGNORECASE),
    re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s*$"),  # bare timestamps
    re.compile(r"^\s*$"),
]


def extract_root_cause(logs):
    """Scan job logs and return the first meaningful error line (≤120 chars), or None."""
    for log_text in logs.values():
        for line in log_text.splitlines():
            stripped = line.strip()
            if any(skip.search(stripped) for skip in _SKIP_PATTERNS):
                continue
            if any(pat.search(stripped) for pat in _ERROR_PATTERNS):
                # Trim log timestamp prefix (GitHub Actions prepends "2024-01-01T00:00:00.000Z ")
                clean = re.sub(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+", "", stripped)
                # Trim Maven module prefix like "[ERROR] "
                clean = re.sub(r"^\[ERROR\]\s*", "", clean).strip()
                if len(clean) > 120:
                    clean = clean[:117] + "..."
                if clean:
                    return clean
    return None


_DEVELOCITY_PATTERN = re.compile(r"https://\S+/s/[a-z0-9]+")


def extract_develocity_url(logs):
    """Return the first Develocity build scan URL found in any job log, or None."""
    for log_text in logs.values():
        match = _DEVELOCITY_PATTERN.search(log_text)
        if match:
            return match.group(0)
    return None


def build_message(repo, ref_name, workflow, run_id, run_attempt,
                  actor, server_url, failed_job_names, job_urls,
                  root_cause, develocity_url, include_run_attempt):
    """Assemble the mrkdwn Slack message. Sections are omitted when their value is None."""
    repo_url = f"{server_url}/{repo}"
    run_url = f"{repo_url}/actions/runs/{run_id}"

    # Build failed jobs as links when a URL is available, plain text otherwise
    if failed_job_names:
        failed_parts = [
            f"<{job_urls[name]}|{name}>" if name in job_urls else name
            for name in failed_job_names
        ]
        failed = ", ".join(failed_parts)
    else:
        failed = "unknown"

    attempt_part = f"  •  *Attempt:* {run_attempt}" if include_run_attempt else ""
    header = (
        f":alert: *CI Failure* — <{repo_url}|{repo}>\n\n"
        f"*Workflow:* {workflow}  •  *Branch:* `{ref_name}`{attempt_part}\n"
        f"*Triggered by:* {actor}\n"
        f"*Failed Jobs:* {failed}"
    )

    extra_block = ""
    if root_cause is not None:
        extra_block += f"\n\n:microscope: *Root Cause:* {root_cause}"
    if develocity_url is not None:
        extra_block += f"\n:bar_chart: *Build Scan:* <{develocity_url}|View Develocity Scan>"

    footer = f"\n\n<{run_url}|:mag: View Run & Re-run Failed Jobs>"

    return header + extra_block + footer


def write_output(message):
    """Write the message to GITHUB_OUTPUT using the multiline heredoc syntax."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        # Fallback for local testing
        print(f"message={message}")
        return
    delimiter = secrets.token_hex(8)
    with open(github_output, "a", encoding="utf-8") as f:
        f.write(f"message<<{delimiter}\n{message}\n{delimiter}\n")


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    needs_json = os.environ.get("NEEDS_JSON", "{}")
    repository = os.environ.get("GH_REPOSITORY", "")
    # Use head_ref (PR source branch) when available, fall back to ref_name
    ref_name = os.environ.get("GH_HEAD_REF") or os.environ.get("GH_REF_NAME", "")
    workflow = os.environ.get("GH_WORKFLOW", "")
    run_id = os.environ.get("GH_RUN_ID", "")
    run_attempt = os.environ.get("GH_RUN_ATTEMPT", "1")
    actor = os.environ.get("GH_ACTOR", "")
    server_url = os.environ.get("GH_SERVER_URL", "https://github.com")

    include_root_cause = is_enabled("INCLUDE_ROOT_CAUSE")
    include_develocity = is_enabled("INCLUDE_DEVELOCITY")
    include_run_attempt = is_enabled("INCLUDE_RUN_ATTEMPT")

    failed_job_names = parse_failed_jobs(needs_json)

    logs, job_urls = {}, {}
    if token and run_id:
        logs, job_urls = get_jobs_info(token, repository, run_id)

    root_cause = extract_root_cause(logs) if include_root_cause else None
    develocity_url = extract_develocity_url(logs) if include_develocity else None

    message = build_message(
        repo=repository,
        ref_name=ref_name,
        workflow=workflow,
        run_id=run_id,
        run_attempt=run_attempt,
        actor=actor,
        server_url=server_url,
        failed_job_names=failed_job_names,
        job_urls=job_urls,
        root_cause=root_cause,
        develocity_url=develocity_url,
        include_run_attempt=include_run_attempt,
    )

    eprint("Built failure message successfully.")
    write_output(message)


if __name__ == "__main__":
    main()
