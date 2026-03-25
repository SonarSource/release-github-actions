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


def _github_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def parse_failed_jobs(needs_json):
    """Extract job names where result == 'failure' from toJSON(needs)."""
    try:
        needs = json.loads(needs_json)
        return [k for k, v in needs.items() if v.get("result") == "failure"]
    except (json.JSONDecodeError, AttributeError):
        eprint("Warning: Failed to parse needs JSON")
        return []


def get_run_info(token, repository, run_id):
    """Fetch run metadata: workflow_id and associated PR info (if any).

    Returns a dict with keys:
      - workflow_id: int or None
      - pr_number: int or None
      - pr_title: str or None
      - pr_url: str or None
    """
    headers = _github_headers(token)
    result = {"workflow_id": None, "pr_number": None, "pr_title": None, "pr_url": None}
    try:
        run_resp = requests.get(
            f"https://api.github.com/repos/{repository}/actions/runs/{run_id}",
            headers=headers, timeout=10,
        )
        if run_resp.status_code != 200:
            eprint(f"Warning: Could not fetch run info (status {run_resp.status_code})")
            return result
        run_data = run_resp.json()
        result["workflow_id"] = run_data.get("workflow_id")
        pull_requests = run_data.get("pull_requests", [])
        if not pull_requests:
            return result
        pr_number = pull_requests[0]["number"]
    except Exception as exc:
        eprint(f"Warning: Failed to fetch run info: {exc}")
        return result

    try:
        pr_resp = requests.get(
            f"https://api.github.com/repos/{repository}/pulls/{pr_number}",
            headers=headers, timeout=10,
        )
        if pr_resp.status_code != 200:
            eprint(f"Warning: Could not fetch PR #{pr_number} (status {pr_resp.status_code})")
            return result
        pr_data = pr_resp.json()
        result["pr_number"] = pr_number
        result["pr_title"] = pr_data["title"]
        result["pr_url"] = pr_data["html_url"]
    except Exception as exc:
        eprint(f"Warning: Failed to fetch PR info: {exc}")
    return result


def get_jobs_info(token, repository, run_id):
    """Fetch info for all jobs in the run.

    Returns a tuple:
      - logs: {job_name: log_text} for failed jobs (last 200 lines each)
      - job_urls: {job_name: html_url} for failed jobs
      - failed_steps: {job_name: step_name} — name of first failed step per job

    Returns ({}, {}, {}) on any error.
    """
    headers = _github_headers(token)
    jobs_url = f"https://api.github.com/repos/{repository}/actions/runs/{run_id}/jobs"
    try:
        response = requests.get(jobs_url, headers=headers, timeout=10)
        if response.status_code != 200:
            eprint(f"Warning: Could not fetch jobs list (status {response.status_code})")
            return {}, {}, {}
        jobs = response.json().get("jobs", [])
    except Exception as exc:
        eprint(f"Warning: Failed to fetch jobs: {exc}")
        return {}, {}, {}

    failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
    job_urls = {j["name"]: j["html_url"] for j in failed_jobs}

    # First failed step per job
    failed_steps = {}
    for job in failed_jobs:
        for step in job.get("steps", []):
            if step.get("conclusion") == "failure":
                failed_steps[job["name"]] = step["name"]
                break

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
    return logs, job_urls, failed_steps


def get_consecutive_failures(token, repository, workflow_id, branch, current_run_id):
    """Count consecutive prior failures for this workflow+branch before the current run.

    Returns the count (0 if no prior failures, or on error).
    """
    if not workflow_id:
        return 0
    headers = _github_headers(token)
    url = f"https://api.github.com/repos/{repository}/actions/workflows/{workflow_id}/runs"
    params = {"branch": branch, "per_page": "10"}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            eprint(f"Warning: Could not fetch workflow runs (status {response.status_code})")
            return 0
        runs = response.json().get("workflow_runs", [])
    except Exception as exc:
        eprint(f"Warning: Failed to fetch workflow runs: {exc}")
        return 0

    count = 0
    for run in runs:
        if str(run.get("id")) == str(current_run_id):
            continue
        if run.get("conclusion") == "failure":
            count += 1
        else:
            break
    return count


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


_SUREFIRE_PATTERN = re.compile(
    r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+)",
    re.IGNORECASE,
)


def extract_test_counts(logs):
    """Scan logs for Maven surefire summary lines and aggregate totals.

    Returns (total_run, total_failures, total_errors) or None if no test output found
    or all failure/error counts are zero.
    """
    total_run = total_failures = total_errors = 0
    found = False
    for log_text in logs.values():
        for match in _SUREFIRE_PATTERN.finditer(log_text):
            found = True
            total_run += int(match.group(1))
            total_failures += int(match.group(2))
            total_errors += int(match.group(3))
    if not found or (total_failures == 0 and total_errors == 0):
        return None
    return (total_run, total_failures, total_errors)


_DEVELOCITY_PATTERN = re.compile(r"https://\S+/s/[a-z0-9]+")


def extract_develocity_url(logs):
    """Return the first Develocity build scan URL found in any job log, or None."""
    for log_text in logs.values():
        match = _DEVELOCITY_PATTERN.search(log_text)
        if match:
            return match.group(0)
    return None


def build_message(repo, ref_name, workflow, run_id, run_attempt,
                  actor, server_url,
                  failed_job_names, job_urls, failed_steps,
                  pr_number, pr_title, pr_url,
                  consecutive_failures,
                  root_cause,
                  test_counts,
                  develocity_url,
                  include_run_attempt, include_failed_step,
                  include_flakiness, include_test_counts):
    """Assemble the mrkdwn Slack message. Sections are omitted when their value is None/falsy."""
    repo_url = f"{server_url}/{repo}"
    run_url = f"{repo_url}/actions/runs/{run_id}"

    # Build failed jobs as links with optional failed step annotation
    if failed_job_names:
        failed_parts = []
        for name in failed_job_names:
            job_link = f"<{job_urls[name]}|{name}>" if name in job_urls else name
            if include_failed_step and name in failed_steps:
                step_url = job_urls.get(name, run_url)
                job_link += f" (step: <{step_url}|{failed_steps[name]}>)"
            failed_parts.append(job_link)
        failed = ", ".join(failed_parts)
    else:
        failed = "unknown"

    attempt_part = f"  •  *Attempt:* {run_attempt}" if include_run_attempt else ""
    header = (
        f":alert: *CI Failure* — <{repo_url}|{repo}>\n\n"
        f"*Workflow:* {workflow}  •  *Branch:* `{ref_name}`{attempt_part}\n"
        f"*Triggered by:* {actor}"
    )

    pr_line = ""
    if pr_number is not None and pr_url is not None and pr_title is not None:
        pr_line = f"\n*PR:* <{pr_url}|#{pr_number} {pr_title}>"

    header += pr_line + f"\n*Failed Jobs:* {failed}"

    flakiness_block = ""
    if include_flakiness and consecutive_failures >= 2:
        flakiness_block = f"\n\n:rotating_light: *Flaky:* This workflow has failed {consecutive_failures} consecutive times on this branch"

    extra_block = ""
    if root_cause is not None:
        extra_block += f"\n\n:microscope: *Root Cause:* {root_cause}"
    if include_test_counts and test_counts is not None:
        total_run, total_failures, total_errors = test_counts
        parts = []
        if total_failures:
            parts.append(f"{total_failures} failure{'s' if total_failures != 1 else ''}")
        if total_errors:
            parts.append(f"{total_errors} error{'s' if total_errors != 1 else ''}")
        extra_block += f"\n:test_tube: *Test Failures:* {', '.join(parts)} (across {total_run} tests)"
    if develocity_url is not None:
        extra_block += f"\n:bar_chart: *Build Scan:* <{develocity_url}|View Develocity Scan>"

    footer = f"\n\n<{run_url}|:mag: View Run & Re-run Failed Jobs>"

    return header + flakiness_block + extra_block + footer


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
    include_pr_info = is_enabled("INCLUDE_PR_INFO")
    include_failed_step = is_enabled("INCLUDE_FAILED_STEP")
    include_test_counts = is_enabled("INCLUDE_TEST_COUNTS")
    include_flakiness = is_enabled("INCLUDE_FLAKINESS")

    failed_job_names = parse_failed_jobs(needs_json)

    run_info = {}
    if token and run_id and (include_pr_info or include_flakiness):
        run_info = get_run_info(token, repository, run_id)

    pr_number = run_info.get("pr_number") if include_pr_info else None
    pr_title = run_info.get("pr_title") if include_pr_info else None
    pr_url = run_info.get("pr_url") if include_pr_info else None
    workflow_id = run_info.get("workflow_id")

    logs, job_urls, failed_steps = {}, {}, {}
    if token and run_id:
        logs, job_urls, failed_steps = get_jobs_info(token, repository, run_id)

    consecutive_failures = 0
    if include_flakiness and token and workflow_id and ref_name:
        consecutive_failures = get_consecutive_failures(token, repository, workflow_id, ref_name, run_id)

    root_cause = extract_root_cause(logs) if include_root_cause else None
    test_counts = extract_test_counts(logs) if include_test_counts else None
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
        failed_steps=failed_steps,
        pr_number=pr_number,
        pr_title=pr_title,
        pr_url=pr_url,
        consecutive_failures=consecutive_failures,
        root_cause=root_cause,
        test_counts=test_counts,
        develocity_url=develocity_url,
        include_run_attempt=include_run_attempt,
        include_failed_step=include_failed_step,
        include_flakiness=include_flakiness,
        include_test_counts=include_test_counts,
    )

    eprint("Built failure message successfully.")
    write_output(message)


if __name__ == "__main__":
    main()
