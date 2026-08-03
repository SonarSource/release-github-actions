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

Trigger the repo's automated-release wrapper workflow (the hand-authored `.github/workflows/*.yml`
file that forwards to `SonarSource/release-github-actions/.github/workflows/automated-release.yml@v1`
— its filename varies per repo, see Step 1) for an analyzer repo and stay with it until every
pull request it opens (version bump, SQS, SQC, SQAA) is reviewed, green, and merged, and the
SONAR integration ticket's fixVersion is set — so the user can ask once and walk away instead of
babysitting PRs across multiple repos and a Jira ticket.

This skill assumes the target repo already has that wrapper workflow set up (see the
`automated-release-setup` skill if it doesn't).

**Always link, don't just name.** Whenever you mention a Jira ticket, a GitHub workflow run, or
a pull request anywhere in this skill's output, include its actual URL
(`https://sonarsource.atlassian.net/browse/<KEY>` for Jira, or whatever `gh`/the Atlassian MCP
returns) — not just the key/number. The user should be able to click straight through without
having to construct the link themselves.

**Heads up on permission prompts.** This skill runs a number of read-only shell commands (`gh`,
`git`, `date`, `mktemp`) to inspect repo/release state and poll status as it goes. If you'd
rather not approve each one individually, pre-approve these command prefixes for the session (or
project-locally in `.claude/settings.local.json`) before starting — the skill itself has no way
to do this for you.

## Step 1 — Identify the repo and read its release config

1. **Check the current directory first.** If it's already a git checkout of a repo under the
   `SonarSource` org (`git remote get-url origin`) with a `.github/workflows/*.yml` file that
   forwards to `release-github-actions/.github/workflows/automated-release.yml@v1` (grep as in
   step 4 below — don't assume the filename), ask the user via `AskUserQuestion`: "Release
   `<repo>` (the one you're in)?" with that as the first/default option and "No, a different
   repo" as the other. Only fall through to step 2 below if the user picks the latter, or if the
   current directory isn't a recognizable checkout at all.
2. Otherwise, parse the repo name from the request, e.g. "Release sonar-pli" or "Release
   SonarSource/sonar-pli". A bare name (`sonar-pli`) is assumed to be under the `SonarSource`
   GitHub org; accept a full `org/repo` too.
3. Find a local checkout to read the wrapper workflow file from:
   - If the current directory is already a checkout of that repo (`git remote get-url origin`
     matches), use it directly.
   - Otherwise, ask the user (via `AskUserQuestion`) where it's already cloned — offer a
     free-text path option and a "not cloned yet" option. Don't assume any particular directory
     layout (e.g. `~/Projects`) — that's a personal convention, not a portable default.
   - If not cloned, ask where to clone it, defaulting to a fresh temp directory
     (`mktemp -d`) so it's disposable. A shallow `git clone` is enough — this only needs to
     read one YAML file, not build or test anything.
4. Read the repo's wrapper workflow file. **Don't assume it's named
   `automated-release.yml`** — it's hand-authored per repo (by the `automated-release-setup`
   skill or manually) and the filename varies (e.g. sonar-php uses `AutomateRelease.yml`).
   Find it by content, not name:
   ```bash
   grep -rl "release-github-actions/.github/workflows/automated-release.yml@v1" .github/workflows/
   ```
   Use whatever path that returns for every later step in this skill (reading inputs here, and
   the `gh workflow run <filename>` call in Step 5 — that command also takes the actual
   filename, not a hardcoded `automated-release.yml`). This file declares `workflow_dispatch`
   inputs and forwards them to
   `SonarSource/release-github-actions/.github/workflows/automated-release.yml@v1`. **Parse the
   actual file — don't assume a fixed input list.** Every repo customizes it (e.g. some add
   `ide-integration`, `dry-run`, `bump-version`; others don't).
5. From that same file, note the hardcoded `with:` values for `project-name`, `plugin-name`,
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

- If either check fails, stop — but don't just report the failure and give up. Diagnose it and
  help the user fix it (see "Diagnosing and fixing releasability problems" below). Do not
  proceed to Step 3 until releasability passes.
- Tell the user this is a **pre-flight convenience check**, not the authoritative one — the
  workflow's own `check-releasability` job re-checks the exact commit SHA via
  `SonarSource/gh-action_releasability@v3` when it actually runs, so this step is about failing
  fast and cheaply, not replacing that gate.

### Diagnosing and fixing releasability problems

Don't stop at "releasability failed" — read the `description` field closely, since it usually
names the specific sub-check that failed (e.g. `"failed optional checks -> Jira"`,
`"failed optional checks -> Peachee Languages Statistics"`) and diagnose each failure to a
concrete, actionable cause before presenting it to the user:

- **`-> Jira`**: the releasability check requires no unresolved tickets against the project's
  unreleased Jira version. Query for the blockers directly instead of asking the user to go
  look. Resolve the Jira `cloudId` (site host, e.g. `sonarsource.atlassian.net`) via
  `mcp__atlassian__getAccessibleAtlassianResources` if not already known, then use the
  Atlassian MCP (`mcp__atlassian__searchJiraIssuesUsingJql`) with something like:
  `project = <JIRA_PROJECT_KEY> AND fixVersion in unreleasedVersions() AND status not in (Done, Closed, Resolved, Canceled)`
  — adjust the "done-like" status list per project if that query returns nothing, since
  workflow status names vary per project. List every matching ticket with its **clickable Jira
  link** (`https://<site>/browse/<KEY>`), summary, status, and assignee so the user can see
  exactly what's outstanding without having to go look it up themselves, and check
  `mcp__atlassian__getTransitionsForJiraIssue` for each to see whether a direct
  "Close as Done" / "Cancel Issue" / similar terminal transition exists.
- **`-> Quality Gate`**: a SonarQube quality gate is failing on the release branch — link the
  user directly to the project's SonarQube quality gate page rather than guessing at a fix;
  this isn't something to auto-resolve.
- **`-> Dependencies` / `-> Licenses` / `-> Manifest Values` / `-> Parent POM` / `-> GitHub`**:
  these indicate a code/config problem (outdated parent POM, license mismatch, manifest
  metadata) that needs a real code change — report which one failed, with a link to the
  releasability check run (`target_url` on the status) so the user can see the detail, and
  stop; don't attempt an automated fix for these.
- **Other failing check-runs** (from the check-runs API call above, not the Releasability
  status itself): report the check name with a link to its GitHub Actions run/job (`.html_url`
  on the check-run) so the user can look at the logs directly; these are usually CI/build
  failures needing a real fix, not a quick toggle.

For each fixable issue (mainly the Jira case), **suggest the concrete fix, with a link to the
ticket, and ask for confirmation before acting** — e.g. "[SONARPLI-390](<jira-link>) is 'In
Validation' and blocking release; transition it to Done?" — since transitioning a ticket or
touching shared state is visible to others and should not happen silently. Use
`mcp__atlassian__transitionJiraIssue` once confirmed, and share the ticket's link again in the
confirmation of what was done.

**After every fix is applied, don't assume it's reflected immediately** — the `Releasability`
commit status is stale until it's recomputed. Find the job that posted it and re-run just that
job, then re-poll the status before declaring victory:

```bash
# The status's target_url points at the workflow run that posted it. Find the specific
# job named "Releasability Check" (or similar) inside that run:
gh run view <run-id-from-target_url> --repo <owner>/<repo> --json jobs \
  --jq '.jobs[] | select(.name | test("Releasability"; "i"))'

# Re-run just that job (not the whole pipeline):
gh run rerun <run-id> --repo <owner>/<repo> --job <job-id>

# Poll until it completes, then re-fetch the Releasability status (same command as above)
# and confirm the description no longer mentions the fixed issue.
```

Repeat the diagnose → fix → confirm → re-run → re-check loop until releasability actually
passes (description like `"passed releasability checks"`, not just `state == "success"` with a
lingering "failed optional checks" description). Only then proceed to Step 3.

## Step 3 — Interview

Using `AskUserQuestion`, ask for each `workflow_dispatch` input found in Step 1, in the order
they appear in the YAML:

- **`AskUserQuestion` requires ≥2 options per question — it errors out otherwise.** A required
  free-text input with no meaningful default (e.g. `short-description` on a repo where it has no
  YAML default) is not a valid multi-choice question. For these, either (a) skip
  `AskUserQuestion` entirely and just ask in plain text, or (b) derive a concrete draft value
  first — e.g. from the unreleased Jira ticket(s) for this project (see the derivation pattern
  used for `short-description` below) — and offer that draft as one option against a "type my
  own" option as the second. Don't send a single-option question; it fails validation and wastes
  a round trip. Batch the remaining genuinely-multi-choice inputs (booleans, branch, version) into
  one `AskUserQuestion` call rather than a call-per-input.
- If a required free-text field like `short-description` has no natural default, consider
  proactively querying the project's unreleased Jira backlog
  (`project = <jira-project-key> AND fixVersion in unreleasedVersions() ORDER BY issuetype ASC,
  key ASC` via `mcp__atlassian__searchJiraIssuesUsingJql`) and drafting a summary from the
  ticket(s) found, rather than asking the user to write one from scratch or falling back to a
  generic placeholder — this is the same backlog Step 3's release-notes drafting already reads,
  so it's not extra API surface.
- Show each input's description and default value so the user can accept a default with one
  click instead of retyping it.
- Present boolean inputs as Yes/No with the YAML default pre-selected.
- For `new-version` (or equivalent): mention that leaving it blank lets the workflow
  auto-increment the current minor version.
- If the user sets `dry-run` (or `use-jira-sandbox`/`is-draft-release`) to `false`... actually,
  the important warning is the opposite: **if `dry-run` is left `true` or explicitly requested**,
  tell the user plainly that this is not a true no-op. It only affects the Jira sandbox and
  whether the GitHub release is a draft — the SQS/SQC/SQAA/bump-version pull requests are still
  created for real either way. Don't let "dry-run" imply nothing will happen outside GitHub.
- If `sqs-integration` is enabled (default `true`), also ask which SQS release this analyzer
  version will ship with — this sets the `fixVersion` on the SONAR/SQS integration ticket that
  the workflow creates later (see Step 9). Ask this now, up front, rather than after the SQS PR
  merges — the skill's whole point is one confirmation before triggering, then walking away;
  asking mid-flight would reintroduce the exact interruption it's meant to avoid. Compute a
  default before asking, don't ask blind: query the Jira **SONAR** project's versions
  (`jira_client.project_versions()` — same pattern as
  `get-jira-release-notes/get_jira_release_notes.py`), filter to `released == false`, sort by
  `releaseDate` ascending, and take the first as "next SQS release" (names follow the
  `sqs-YYYY.N` convention, e.g. `sqs-2026.5`). Ask via `AskUserQuestion` with that default as
  the first option (labelled with its name and release date, e.g. "sqs-2026.5 (2026-09-21,
  next release) — default") and a free-text option to name a different version — "next" is a
  reasonable guess but not a guarantee, a change can miss a train and ship in a later one.
  Store the chosen version name; nothing is written to Jira yet — see Step 9.
- For `release-notes`: if the user leaves it blank (accepting auto-generation by
  `get-jira-release-notes`), ask via `AskUserQuestion` (Yes/No) whether they'd like a short
  intro paragraph drafted ahead of the auto-generated issue list. The `release-notes` input is
  all-or-nothing — a non-blank value fully replaces auto-generation — so this only works by
  building the whole value here, not by asking the workflow to prepend anything:
  1. If yes, fetch the same issues `get-jira-release-notes` would
     (`project = <jira-project-key> AND fixVersion = "<new-version>" ORDER BY issuetype ASC, key
     ASC` via `mcp__atlassian__searchJiraIssuesUsingJql`), using the `issue-categories` order
     from that repo's `automated-release.yml` `with:` block if it overrides the default
     (`Feature,False Positive,False Negative,Bug,Security,Maintenance`).
  2. Draft a 1-2 sentence paragraph summarizing the release's theme from those issue summaries
     and the `short-description` already given, and show it to the user for approval/edit —
     one round of confirmation, same as everywhere else in this step.
  3. Reproduce `get_jira_release_notes.py`'s `format_notes_as_markdown` structure exactly (`#
     Release notes - {project name} - {version}` header, then `### {category}` sections in
     order, each issue as `[KEY](jira-url/browse/KEY) summary`), inserting the approved
     paragraph directly under the header line. Use this full string as the `release-notes`
     value passed in Step 5.
  4. If the user declines, leave `release-notes` blank — unchanged, auto-generated behavior.

## Step 4 — Summary and confirmation

Show a concrete table of input → value (including defaults accepted silently) and the exact
`gh workflow run` command that will be executed. If `sqs-integration` is enabled, include the
SQS fixVersion chosen in Step 3 as its own row (e.g. `| SQS fixVersion (SONAR ticket) |
sqs-2026.5 |`), and note that it will be applied automatically to the SONAR integration ticket
once that ticket exists later in the run (Step 9) — with no further prompt for it. Also state
plainly what happens *after* triggering: this skill will monitor the workflow to completion,
then automatically approve and merge all resulting pull requests (bump-version, SQS, SQC, SQAA)
as soon as each is green — with no further prompts in between, unless something fails or needs a
judgment call (see Step 8's failure handling). Ask the user to confirm this whole flow once, up
front, in plain language — triggering a release is a cross-repo, hard-to-reverse action, and
the point of this skill is that one confirmation here is the only interaction needed; don't ask
again before merging each PR later, or before setting the fixVersion in Step 9.

## Step 5 — Trigger

Use the actual filename discovered in Step 1 (e.g. `AutomateRelease.yml`), not a hardcoded
`automated-release.yml` — `gh workflow run` and `gh run list --workflow` both need the real
filename or they'll silently match nothing / the wrong workflow.

```bash
gh workflow run <actual-filename> --repo <owner>/<repo> --ref <branch> \
  -f "<input>=<value>" ...
```

Conveniently, `gh workflow run` actually does print the run URL directly to stdout on recent
`gh` versions — capture and share that; don't assume you need to construct one, but do
construct `https://github.com/<owner>/<repo>/actions/workflows/<actual-filename>` as a fallback
if the output is empty.

Then resolve the run ID the same way `publish-github-release/action.yml` does:

```bash
sleep 30
RUN_ID=$(gh run list --repo <owner>/<repo> --workflow <actual-filename> --limit 1 \
  --created ">=$SINCE" --json databaseId --jq '.[0].databaseId')
```

Compute `SINCE` as "5 minutes ago" in UTC ISO-8601. `date` flags differ between macOS (`date -u
-v-5M`) and GNU/Linux (`date -u -d '5 minutes ago'`) — detect which is available
(`date -v-5M +%s >/dev/null 2>&1` succeeds on BSD/macOS date) and use the matching form, since
this skill runs on a user's local machine, not just CI.

If `RUN_ID` comes back empty, wait a bit longer and retry — don't fail immediately.

## Step 6 — Monitor the workflow run

Poll every ~15 seconds. **Avoid the bash variable name `status`** in polling scripts — it's a
read-only/special variable in some shells and assigning to it crashes the script with
`read-only variable: status`; use `run_status`/`run_conclusion` instead.

```bash
gh run view "$RUN_ID" --repo <owner>/<repo> --json status,conclusion
```

until `status == "completed"`. If `conclusion != "success"` (or `status` is `cancelled` or
`failure`), don't stop immediately — first check whether the failure is a **real** problem or a
**transient infra blip**, since the two need very different responses:

1. Run `gh run view "$RUN_ID" --repo <owner>/<repo> --log-failed` and read the actual error.
2. **Transient/infra signatures** — retry automatically without asking, since these are
   noise, not signal:
   - The `Check Releasability` job re-checking the exact commit SHA (this happens even though
     Step 2 already passed the pre-flight check — the workflow's own check is authoritative and
     re-runs independently, per Step 2's caveat) fails one specific sub-check with a
     network-level error rather than a real business-rule violation, e.g.
     `java.lang.IllegalStateException: java.io.IOException: Connection reset` on the `Jira`
     sub-check while every other sub-check (`QA`, `GitHub`, `ParentPOM`, `CheckDependencies`,
     `QualityGate`, etc.) passed. This is a dropped connection to the lambda backing that one
     check, not an actual unresolved-ticket problem — Step 2 already ruled that out.
   - Any other single-job failure whose log shows a connection/timeout/network error unrelated
     to the actual release logic.
   - In these cases: tell the user plainly what failed and why it looks transient (name the
     specific error and note which other checks passed), then re-trigger the **entire workflow**
     with the identical inputs from Step 5 (a full re-run is simpler and safer than trying to
     rerun just one internal job of someone else's reusable workflow) — don't ask for
     confirmation first, since this is a low-risk retry of something the user already approved
     once in Step 4, not a new judgment call.
3. **Real failure signatures** — stop and report, don't retry blindly: a business-rule check
   genuinely failing (an actual unresolved Jira ticket, a real quality gate failure, a real build
   error, a real test failure) or the same transient-looking failure recurring on the retry.
   Report to the user with the run's link
   (`https://github.com/<owner>/<repo>/actions/runs/<RUN_ID>`) and stop — don't guess at a fix;
   the actual fix likely needs a human familiar with the failing job.

## Step 7 — Discover the pull requests

The workflow's own outputs (`sqs-pull-request-url`, `sqc-pull-request-url`,
`sqaa-pull-request-url`, `bump-version-pull-request-url`) are **not** retrievable via `gh run
view` for a `workflow_dispatch`-triggered run — those outputs only surface to a `workflow_call`
caller job. Find the PRs directly by their known branch-name conventions instead:

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

- **SQAA PR** (Analysis as a Service, opens in `sonar-analysis-as-a-service`): branch pattern
  `<plugin-name>/update-aaas-<release-version>`.

  ```bash
  gh pr list --repo SonarSource/sonar-analysis-as-a-service --state open --json number,url,headRefName \
    --jq '.[] | select(.headRefName | startswith("<plugin-name>/update-aaas-"))'
  ```

Only look for a PR if its corresponding integration flag (`sqs-integration`, `sqc-integration`,
`bump-version`) was `true` in the triggered run — skip the lookup entirely otherwise, since no
PR will ever appear. The SQAA PR needs **both** `sqc-integration` and `sqaa-integration` to be
`true` (mirrors the workflow's own `if:` condition on the `update-analysis-as-a-service` job) —
skip looking for it if either is `false`.

The jobs that open these PRs run sequentially after the main release steps, so if a PR isn't
found immediately, retry a few times with a short delay before reporting it missing. For the
SQAA PR specifically, "not found after retrying" can also mean the analyzer just isn't onboarded
to SQAA yet — `update-analysis-as-a-service` skips silently (no PR, no failure) when it finds no
matching version-catalog entry. Report that as "no SQAA PR — analyzer not yet onboarded to
Analysis as a Service," not as a problem to chase.

As soon as each PR is found, tell the user with its `.url` field from the `gh pr list` output —
don't make them wait for the final report to see the links.

## Step 8 — Approve and merge each pull request

For each PR found in Step 7, poll roughly every 30 seconds:

```bash
gh pr view <PR_URL> --json statusCheckRollup,mergeable,mergeStateStatus
```

**Don't fully trust a background Monitor's summarized state (e.g. a shell loop's own "GREEN" /
"FAILED" echo) as the final word before merging — re-verify with a direct, fresh `gh pr view`
call first.** A polling script's own bucketing logic (e.g. matching on generic
`status`/`conclusion` strings) can misclassify a real failing check as pending/passed if the
matching is too loose, or simply lag behind the true state by one poll interval. Treat the
monitor as a wake-up signal, not as ground truth — always re-check the specific PR directly
before approving/merging, and specifically re-derive the failing/pending lists yourself from the
raw `statusCheckRollup` array rather than trusting a prior summary string.

If one PR's checks fail while others in the same run are still pending or already green, don't
let one failure block progress on the rest — validate and merge the clean ones while you
diagnose the failing one (see below).

Once all checks in `statusCheckRollup` are `SUCCESS` (or neutral/skipped) and `mergeable ==
"MERGEABLE"`, **validate the diff before approving** — green CI means the change builds and
passes tests, not that it's the change you expected. A green PR that touches the wrong files is
still a bug. Don't skip this just because Step 4's confirmation already covers the overall flow.

### A failing check isn't necessarily a real failure — diagnose before giving up

If a check fails, read its actual job log (`gh run view <run-id> --repo <owner>/<repo> --job
<job-id> --log`) before reporting it as blocking, using the same transient-vs-real distinction
as Step 6:

- **Transient/infra signatures** — e.g. a Testcontainers/Docker container failing to become
  healthy (`ContainerLaunchException` → `TimeoutException` → `ConnectException` on a health
  check), a network blip, a flaky/unrelated integration-test suite (e.g. a `python`-analyzer
  integration test failing on a PR that only bumps the `php` version — the failure is in a test
  suite the change doesn't even touch). In these cases, re-run just the failed job (not the
  whole PR's CI) and keep polling — this is the appropriate scope here because, unlike Step 6's
  reusable-workflow run, you have direct visibility into and control over each individual CI job
  on a PR:
  ```bash
  gh run rerun <run-id> --repo <owner>/<repo> --job <job-id>
  ```
  Don't ask for confirmation before retrying a job like this — it's the same low-risk "retry
  something that already looked fine" judgment call as Step 6's transient-failure handling.
- **Real failure signatures** — the diff itself touches unexpected files (see the red flags
  below), the failing test is actually in the plugin/component being bumped, or the same job
  fails again after a retry. Stop polling that PR, report the failure with a link to the PR and
  the specific job log, and keep polling the others — one failing PR shouldn't block reporting
  on or merging the rest.

### Validate before approving

Each of these PRs is generated from a known, narrow template — fetch its diff
(`gh pr diff <PR_URL>`) and check it matches the expected shape:

- **Bump-version PR**: should touch only version-declaration files (`pom.xml`,
  `gradle.properties`, or whatever `bump-version`/`bump-versions.yaml` targets for this repo's
  build system) and only bump the version string itself — no unrelated file changes.
- **SQS PR** (`sonar-enterprise`): should touch only the single build file
  (`build.gradle`/equivalent) that pins the plugin's version, changing just the version number
  for `plugin-name` (or `plugin-artifacts-sqs` if set) to the expected `release-version`.
- **SQC PR** (`sonar-plugins-deployer`): same shape as SQS, in its own config file.
- **SQAA PR** (`sonar-analysis-as-a-service`): should touch only
  `gradle/sonar-plugins.versions.toml`, bumping the version-catalog entry/entries for
  `plugin-name` (or `plugin-artifacts-sqaa` if set) to the expected `release-version` — no other
  files, no other catalog entries.

Red flags to stop and report instead of approving:
- Files outside the expected one (or two, if the tool also touches a lockfile) changed.
- The version number in the diff doesn't match the `new-version`/`release-version` from this
  release run.
- More than one plugin/dependency entry changed when only this release's plugin should have.
- The diff is empty, or unexpectedly large (e.g. hundreds of lines) for what should be a
  one-line version bump.

If the diff looks as expected, proceed to approve and merge **without asking for confirmation
again** — the user already approved this whole flow once in Step 4, and pausing per-PR after a
clean validation defeats the point of the skill (trigger once, walk away). If the diff raises
one of the red flags above, stop, show the specific unexpected part of the diff with a link to
the PR, and ask the user how to proceed rather than merging it.

1. **Approve**: `gh pr review <PR_URL> --approve`, using the user's own logged-in `gh`
   identity. This works without a separate token — the PR was opened by the vault-sourced
   `release-automation` bot token running inside the GitHub Actions workflow, a different
   identity than whoever is running this skill locally, so GitHub's "can't approve your own PR"
   restriction doesn't apply.
2. **Merge**: check which merge method the target repo actually allows before merging —
   `gh repo view <owner>/<repo> --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed`
   — and use whichever method the repo supports (don't assume squash or merge-commit).
   `gh pr merge <PR_URL> --<method>`.
   - **`sonar-enterprise` requires an explicit `--subject`.** Its GitHub ruleset enforces a
     commit-message-pattern on the squash commit
     (`^(SONAR-[0-9]+|SCA-[0-9]+|SQRP-[0-9]+) [A-Z][^#]*$`), and the default squash message
     (which can append the commit list) fails it. For any PR in `sonar-enterprise`, always pass
     `--subject "<PR title>" --body ""` on the first merge attempt — the PR title (e.g.
     `SONAR-31203 Update \`abap\` to version 3.22.0.8389`) already matches. Don't wait for the
     plain `gh pr merge --squash` to fail first.
   - Other repos in this flow (`sonar-plugins-deployer`, the release repo itself) have no such
     rule observed so far; if a future merge fails with a `Repository rule violations` /
     commit-message-regex error there too, apply the same `--subject`/`--body ""` fix.

(See "A failing check isn't necessarily a real failure" above for how to triage a failing PR
check before deciding to stop polling it.)

A single sequential loop that checks all outstanding PRs each iteration is enough; there's no
need for real concurrency since this is a long-running, low-frequency poll.

## Step 9 — Set fixVersion on the SONAR integration ticket

Skip entirely if `sqs-integration` was not enabled for this run, or the SQS PR (Step 7/8) was
never found/merged — no ticket to update. The fixVersion to apply was already decided in
Step 3; this step just applies it, with no further user interaction.

The "SQS Ticket" created during the workflow run (job "Create Integration Tickets", step
"Create SQS Ticket") is filed in the Jira **SONAR** project and linked to the release ticket —
this is the ticket `docs/AUTOMATED_RELEASE.md`'s manual checklist calls "the SONAR ticket" and
already lists "Set fix versions on the SONAR ticket" as a step a human is supposed to
remember. This step does it instead.

1. **Find the ticket.** Search by summary rather than assuming an ID:
   ```
   project = SONAR AND summary ~ "Update <plugin-name> to <release-version>" ORDER BY created DESC
   ```
   via `mcp__atlassian__searchJiraIssuesUsingJql` — this is the same "Update X to Y" summary
   pattern `create_integration_ticket.py` generates from `plugin-name` + `release-version`, so
   it should be a unique match. If not found (summary format changed, ticket not created),
   report this in the final report and skip — don't guess a ticket key.

2. **Set it**: update the ticket's `fixVersions` via `mcp__atlassian__editJiraIssue`
   (`fields: {"fixVersions": [{"name": "<version chosen in Step 3>"}]}`). If the ticket
   already has a different fixVersion set (can happen — don't assume it's empty), this
   overwrites it with the value the user explicitly chose upfront, which is intentional — they
   already confirmed it once, no need to check twice.

## Step 10 — Final report

Summarize what happened, with a clickable link for every item: the release version and its
GitHub release link, the Jira release ticket link (if surfaced in the workflow run logs/summary
— check `$GITHUB_STEP_SUMMARY` via `gh run view --log` if `verbose` was true), and the final
state of each PR (merged / needs attention, each with its PR link / skipped because its flag was
off / for SQAA specifically, "no PR — analyzer not yet onboarded to Analysis as a Service" when
applicable). If any releasability issues were fixed in Step 2, list those tickets and their
links too, as a record of what was changed to unblock the release. If `sqs-integration` was
enabled, also report the SONAR ticket link and the fixVersion set on it (or "skipped — no SQS PR
merged", or "ticket not found" if Step 9 couldn't locate it).
