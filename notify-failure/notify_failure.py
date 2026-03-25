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


def get_commit_info(token, repository, sha):
    """Fetch commit author name and first line of commit message via GitHub API.

    Returns (author_name, commit_message_first_line) or ("Unknown", "Unknown commit") on error.
    """
    url = f"https://api.github.com/repos/{repository}/commits/{sha}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            eprint(f"Warning: GitHub API returned {response.status_code} for commit {sha}")
            return "Unknown", "Unknown commit"
        data = response.json()
        commit = data.get("commit", {})
        author = commit.get("author", {}).get("name", "Unknown")
        message = commit.get("message", "").split("\n")[0]
        return author, message
    except Exception as exc:
        eprint(f"Warning: Failed to fetch commit info: {exc}")
        return "Unknown", "Unknown commit"


def parse_failed_jobs(needs_json):
    """Extract job names where result == 'failure' from toJSON(needs)."""
    try:
        needs = json.loads(needs_json)
        return [k for k, v in needs.items() if v.get("result") == "failure"]
    except (json.JSONDecodeError, AttributeError):
        eprint("Warning: Failed to parse needs JSON")
        return []


def get_job_logs(token, repository, run_id):
    """Fetch log text for each failed job in the run.

    Returns {job_name: log_text} with logs truncated to the last 200 lines.
    Returns {} on any error.
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
            return {}
        jobs = response.json().get("jobs", [])
    except Exception as exc:
        eprint(f"Warning: Failed to fetch jobs: {exc}")
        return {}

    failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
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
    return logs


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


def build_message(repo, sha, ref_name, workflow, run_id, run_attempt,
                  actor, server_url, failed_jobs,
                  author, commit_msg,
                  root_cause,
                  develocity_url,
                  include_run_attempt):
    """Assemble the mrkdwn Slack message. Sections are omitted when their value is None."""
    short_sha = sha[:7]
    repo_url = f"{server_url}/{repo}"
    run_url = f"{repo_url}/actions/runs/{run_id}"
    failed = ", ".join(failed_jobs) if failed_jobs else "unknown"

    attempt_part = f"  •  *Attempt:* {run_attempt}" if include_run_attempt else ""
    header = (
        f":alert: *CI Failure* — <{repo_url}|{repo}>\n\n"
        f"*Workflow:* {workflow}  •  *Branch:* `{ref_name}`{attempt_part}\n"
        f"*Failed Jobs:* {failed}"
    )

    commit_block = ""
    if author is not None and commit_msg is not None:
        commit_block = (
            f"\n\n*Last Commit:* `{short_sha}` {commit_msg}\n"
            f"*Author:* {author}  •  *Triggered by:* {actor}"
        )

    extra_block = ""
    if root_cause is not None:
        extra_block += f"\n\n:microscope: *Root Cause:* {root_cause}"
    if develocity_url is not None:
        extra_block += f"\n:bar_chart: *Build Scan:* <{develocity_url}|View Develocity Scan>"

    footer = f"\n\n<{run_url}|:mag: View Run>  •  <{run_url}|:repeat: Re-run Failed Jobs>"

    return header + commit_block + extra_block + footer


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
    sha = os.environ.get("GH_SHA", "")
    ref_name = os.environ.get("GH_REF_NAME", "")
    workflow = os.environ.get("GH_WORKFLOW", "")
    run_id = os.environ.get("GH_RUN_ID", "")
    run_attempt = os.environ.get("GH_RUN_ATTEMPT", "1")
    actor = os.environ.get("GH_ACTOR", "")
    server_url = os.environ.get("GH_SERVER_URL", "https://github.com")

    include_commit_info = is_enabled("INCLUDE_COMMIT_INFO")
    include_root_cause = is_enabled("INCLUDE_ROOT_CAUSE")
    include_develocity = is_enabled("INCLUDE_DEVELOCITY")
    include_run_attempt = is_enabled("INCLUDE_RUN_ATTEMPT")

    failed_jobs = parse_failed_jobs(needs_json)

    author, commit_msg = None, None
    if include_commit_info and token and sha:
        author, commit_msg = get_commit_info(token, repository, sha)

    logs = {}
    if (include_root_cause or include_develocity) and token and run_id:
        logs = get_job_logs(token, repository, run_id)

    root_cause = extract_root_cause(logs) if include_root_cause else None
    develocity_url = extract_develocity_url(logs) if include_develocity else None

    message = build_message(
        repo=repository,
        sha=sha,
        ref_name=ref_name,
        workflow=workflow,
        run_id=run_id,
        run_attempt=run_attempt,
        actor=actor,
        server_url=server_url,
        failed_jobs=failed_jobs,
        author=author,
        commit_msg=commit_msg,
        root_cause=root_cause,
        develocity_url=develocity_url,
        include_run_attempt=include_run_attempt,
    )

    eprint("Built failure message successfully.")
    write_output(message)


if __name__ == "__main__":
    main()
