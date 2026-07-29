---
name: automated-release-run
description: >
  Use this skill whenever the user asks to "release <repo>", "run the release for <repo>",
  "trigger the automated release for <repo>", or any variation of triggering and monitoring the
  automated-release.yml workflow for a SonarSource analyzer project to completion. Unlike
  automated-release-setup (which wires the workflow into a repo once), this skill runs an
  actual release: it interviews the user for the workflow_dispatch inputs, checks
  releasability, triggers the workflow, then polls and merges the resulting pull requests so
  nobody has to remember to come back later.
---

# Run an Automated Release

Trigger `automated-release.yml` for an analyzer repo and stay with it until every pull request
it opens (version bump, SQS, SQC) is reviewed, green, and merged — so the user can ask once and
walk away instead of babysitting three PRs across three repos.

This skill assumes the target repo already has `automated-release.yml` set up (see the
`automated-release-setup` skill if it doesn't).

## Step 1 — Identify the repo and read its release config

The user names the repo directly, e.g. "Release sonar-pli" or "Release SonarSource/sonar-pli" —
don't infer the target from the current working directory.

1. Parse the repo name from the request. A bare name (`sonar-pli`) is assumed to be under the
   `SonarSource` GitHub org; accept a full `org/repo` too.
2. Find a local checkout to read `.github/workflows/automated-release.yml` from:
   - If the current directory is already a checkout of that repo (`git remote get-url origin`
     matches), use it directly.
   - Otherwise, ask the user (via `AskUserQuestion`) where it's already cloned — offer a
     free-text path option and a "not cloned yet" option. Don't assume any particular directory
     layout (e.g. `~/Projects`) — that's a personal convention, not a portable default.
   - If not cloned, ask where to clone it, defaulting to a fresh temp directory
     (`mktemp -d`) so it's disposable. A shallow `git clone` is enough — this only needs to
     read one YAML file, not build or test anything.
3. Read `.github/workflows/automated-release.yml` from that checkout. This file is a
   hand-authored thin wrapper (created by the `automated-release-setup` skill) that declares
   `workflow_dispatch` inputs and forwards them to
   `SonarSource/release-github-actions/.github/workflows/automated-release.yml@v1`. **Parse the
   actual file — don't assume a fixed input list.** Every repo customizes it (e.g. some add
   `ide-integration`, `dry-run`, `bump-version`; others don't).
4. From that same file, note the hardcoded `with:` values for `project-name`, `plugin-name`,
   `jira-project-key` — these are fixed per repo, don't ask the user for them.

## Step 2 — Releasability pre-flight

Before interviewing the user, verify the target branch (default `master`, or whatever the user
names in Step 3) is actually releasable. This is a fast fail before spending any time on the
interview or a full workflow run.

```bash
gh api "/repos/<owner>/<repo>/commits/<branch>/status" \
  --jq '.statuses[] | select(.context=="Releasability")'
```

- Fail with the description shown if `.state != "success"`, or if the description contains
  "failed optional checks" (mirrors `check-releasability-status/action.yml`'s logic).
- Also check for any other failing required checks on the branch:

```bash
gh api "/repos/<owner>/<repo>/commits/<branch>/check-runs" \
  --jq '.check_runs[] | select(.conclusion != "success" and .conclusion != "skipped" and .conclusion != "neutral")'
```

- If either check fails, stop and report exactly which check(s) failed and why. Do not proceed
  to Step 3.
- Tell the user this is a **pre-flight convenience check**, not the authoritative one — the
  workflow's own `check-releasability` job re-checks the exact commit SHA via
  `SonarSource/gh-action_releasability@v3` when it actually runs, so this step is about failing
  fast and cheaply, not replacing that gate.

## Step 3 — Interview

Using `AskUserQuestion`, ask for each `workflow_dispatch` input found in Step 1, in the order
they appear in the YAML:

- Show each input's description and default value so the user can accept a default with one
  click instead of retyping it.
- Present boolean inputs as Yes/No with the YAML default pre-selected.
- For `new-version` (or equivalent): mention that leaving it blank lets the workflow
  auto-increment the current minor version.
- If the user sets `dry-run` (or `use-jira-sandbox`/`is-draft-release`) to `false`... actually,
  the important warning is the opposite: **if `dry-run` is left `true` or explicitly requested**,
  tell the user plainly that this is not a true no-op. It only affects the Jira sandbox and
  whether the GitHub release is a draft — the SQS/SQC/bump-version pull requests are still
  created for real either way. Don't let "dry-run" imply nothing will happen outside GitHub.

## Step 4 — Summary and confirmation

Show a concrete table of input → value (including defaults accepted silently) and the exact
`gh workflow run` command that will be executed. Ask the user to confirm in plain language
before proceeding — triggering a release is a cross-repo, hard-to-reverse action.

## Step 5 — Trigger

```bash
gh workflow run automated-release.yml --repo <owner>/<repo> --ref <branch> \
  -f "<input>=<value>" ...
```

Then resolve the run ID the same way `publish-github-release/action.yml` does:

```bash
sleep 30
RUN_ID=$(gh run list --repo <owner>/<repo> --workflow automated-release.yml --limit 1 \
  --created ">=$SINCE" --json databaseId --jq '.[0].databaseId')
```

Compute `SINCE` as "5 minutes ago" in UTC ISO-8601. `date` flags differ between macOS (`date -u
-v-5M`) and GNU/Linux (`date -u -d '5 minutes ago'`) — detect which is available
(`date -v-5M +%s >/dev/null 2>&1` succeeds on BSD/macOS date) and use the matching form, since
this skill runs on a user's local machine, not just CI.

If `RUN_ID` comes back empty, wait a bit longer and retry — don't fail immediately.

## Step 6 — Monitor the workflow run

Poll every ~15 seconds:

```bash
gh run view "$RUN_ID" --repo <owner>/<repo> --json status,conclusion
```

until `status == "completed"`. If `conclusion != "success"` (or `status` is `cancelled` or
`failure`), run `gh run view "$RUN_ID" --repo <owner>/<repo> --log-failed`, report the failure
to the user, and stop. Don't guess at a fix — the actual fix likely needs a human familiar with
the failing job.

## Step 7 — Discover the three pull requests

The workflow's own outputs (`sqs-pull-request-url`, `sqc-pull-request-url`,
`bump-version-pull-request-url`) are **not** retrievable via `gh run view` for a
`workflow_dispatch`-triggered run — those outputs only surface to a `workflow_call` caller job.
Find the PRs directly by their known branch-name conventions instead:

- **Bump-version PR** (same repo as the release): branch prefix
  `bot/prepare-next-development-iteration-` (this is also what `release-lock.yml` matches on —
  it's a load-bearing convention, not incidental).

  ```bash
  gh pr list --repo <owner>/<repo> --state open --json number,url,headRefName \
    --jq '.[] | select(.headRefName | startswith("bot/prepare-next-development-iteration-"))'
  ```

- **SQS PR** (SonarQube Server, opens in `sonar-enterprise`): branch pattern
  `<plugin-name>/update-analyzer-<release-version>`.

  ```bash
  gh pr list --repo SonarSource/sonar-enterprise --state open --json number,url,headRefName \
    --jq '.[] | select(.headRefName | startswith("<plugin-name>/update-analyzer-"))'
  ```

- **SQC PR** (SonarQube Cloud, opens in `sonar-plugins-deployer`): same branch pattern, in
  `SonarSource/sonar-plugins-deployer` instead.

Only look for a PR if its corresponding integration flag (`sqs-integration`, `sqc-integration`,
`bump-version`) was `true` in the triggered run — skip the lookup entirely otherwise, since no
PR will ever appear.

The jobs that open these PRs run sequentially after the main release steps, so if a PR isn't
found immediately, retry a few times with a short delay before reporting it missing.

## Step 8 — Approve and merge each pull request

For each PR found in Step 7, poll roughly every 30 seconds:

```bash
gh pr view <PR_URL> --json statusCheckRollup,mergeable,mergeStateStatus
```

Once all checks in `statusCheckRollup` are `SUCCESS` (or neutral/skipped) and `mergeable ==
"MERGEABLE"`:

1. **Approve**: `gh pr review <PR_URL> --approve`, using the user's own logged-in `gh`
   identity. This works without a separate token — the PR was opened by the vault-sourced
   `release-automation` bot token running inside the GitHub Actions workflow, a different
   identity than whoever is running this skill locally, so GitHub's "can't approve your own PR"
   restriction doesn't apply.
2. **Merge**: check which merge method the target repo actually allows before merging —
   `gh repo view <owner>/<repo> --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed`
   — and use whichever method the repo supports (don't assume squash or merge-commit).
   `gh pr merge <PR_URL> --<method>`.

If a PR's checks fail: stop polling that one, report the failure with a link to the PR, and
keep polling the others — one failing PR shouldn't block reporting on the rest.

A single sequential loop that checks all outstanding PRs each iteration is enough; there's no
need for real concurrency since this is a long-running, low-frequency poll.

## Step 9 — Final report

Summarize what happened: the release version, links to the GitHub release and the Jira release
ticket (if surfaced in the workflow run logs/summary), and the final state of each of the three
PRs (merged / needs attention, with a link / skipped because its flag was off).
