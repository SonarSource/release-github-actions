#!/usr/bin/env bash
# Unit tests for generate-summary.sh.
# Usage: test-generate-summary.sh <path-to-generate-summary.sh>
# Exits 0 if all tests pass, 1 on first failure.

set -euo pipefail

_script_arg="${1:-$(dirname "$0")/generate-summary.sh}"
SCRIPT="$(cd "$(dirname "$_script_arg")" && pwd)/$(basename "$_script_arg")"

pass=0
fail=0

INITIAL_COMMIT_MSG="initial"
OLD_RULE_CONTENT='<rule>old</rule>'

assert_output_contains() {
  local test_name="$1"
  local pattern="$2"
  local output_file="$3"
  if grep -q "$pattern" "$output_file"; then
    echo "✓ $test_name"
    pass=$((pass + 1))
  else
    echo "✗ $test_name"
    echo "  Expected pattern: $pattern"
    echo "  Actual output:"
    sed 's/^/    /' "$output_file"
    fail=$((fail + 1))
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Helper: create an isolated git repo, commit initial files, stage changes,
# write a log file, run the script, and return the output file path.
# ---------------------------------------------------------------------------
run_test() {
  local work_dir
  work_dir=$(mktemp -d)

  # Each test receives the work_dir; caller populates it before calling run_script.
  echo "$work_dir"
  return 0
}

init_git() {
  git init -q
  git config user.email "test@test.com"
  git config user.name "Test"
  return 0
}

run_script() {
  local work_dir="$1"
  local gh_output="$work_dir/gh_output"
  (cd "$work_dir" && GITHUB_OUTPUT="$gh_output" bash "$SCRIPT" "2.99.0") || true
  echo "$gh_output"
  return 0
}

# ---------------------------------------------------------------------------
# Test 1: flat structure (sonar-rpg style)
# sonarpedia.json at the repo root — mirrors SonarSource/sonar-rpg.
# ---------------------------------------------------------------------------
echo "--- Test 1: flat structure (sonar-rpg style) ---"
WORK_DIR=$(run_test)
cd "$WORK_DIR"
init_git
mkdir -p rules
echo '{}' > sonarpedia.json
echo "$OLD_RULE_CONTENT" > rules/S1000.html
echo '{}' > rules/S1000.json
git add . && git commit -q -m "$INITIAL_COMMIT_MSG"

echo '<rule>new</rule>' > rules/S1000.html
echo '{"updated":true}' > rules/S1001.json
git add .

printf '=== PATH:. ===\nRunning rule-api update\nFound 3 rule(s) to update\n' > rule-api-logs.txt

OUTPUT=$(run_script "$WORK_DIR")
assert_output_contains "flat: row shows 3 to update and 2 updated" \
  './sonarpedia.json.*3.*2' "$OUTPUT"
rm -rf "$WORK_DIR"

# ---------------------------------------------------------------------------
# Test 2: 2-level structure (sonar-security frontend/<lang> style)
# ---------------------------------------------------------------------------
echo "--- Test 2: 2-level structure (sonar-security frontend/java style) ---"
WORK_DIR=$(run_test)
cd "$WORK_DIR"
init_git
mkdir -p frontend/java/rules frontend/python/rules
echo '{}' > frontend/java/sonarpedia.json
echo '{}' > frontend/python/sonarpedia.json
echo "$OLD_RULE_CONTENT" > frontend/java/rules/S1000.html
echo '{}' > frontend/java/rules/S1000.json
echo "$OLD_RULE_CONTENT" > frontend/python/rules/S2000.html
git add . && git commit -q -m "$INITIAL_COMMIT_MSG"

# Update java rules only; python unchanged.
echo '<rule>new</rule>' > frontend/java/rules/S1000.html
echo '{"updated":true}' > frontend/java/rules/S1001.json
git add .

printf '=== PATH:frontend/java ===\nRunning rule-api update\nFound 5 rule(s) to update\n=== PATH:frontend/python ===\nRunning rule-api update\nFound 2 rule(s) to update\n' > rule-api-logs.txt

OUTPUT=$(run_script "$WORK_DIR")
assert_output_contains "2-level: java row shows 5 to update and 2 updated" \
  'frontend/java/sonarpedia.json.*5.*2' "$OUTPUT"
assert_output_contains "2-level: python row shows 2 to update and 0 updated" \
  'frontend/python/sonarpedia.json.*2.*0' "$OUTPUT"
rm -rf "$WORK_DIR"

# ---------------------------------------------------------------------------
# Test 3: deep 3-level structure (sonar-security dotnet style)
# frontend/dotnet/<plugin>/sonarpedia.json — the path the old bug truncated.
# ---------------------------------------------------------------------------
echo "--- Test 3: deep 3-level structure (sonar-security dotnet style) ---"
WORK_DIR=$(run_test)
cd "$WORK_DIR"
init_git
mkdir -p frontend/dotnet/sonar-security-csharp-frontend-plugin/rules
mkdir -p frontend/dotnet/sonar-security-vbnet-frontend-plugin/rules
echo '{}' > frontend/dotnet/sonar-security-csharp-frontend-plugin/sonarpedia.json
echo '{}' > frontend/dotnet/sonar-security-vbnet-frontend-plugin/sonarpedia.json
echo "$OLD_RULE_CONTENT" > frontend/dotnet/sonar-security-csharp-frontend-plugin/rules/S3649.html
echo '{}' > frontend/dotnet/sonar-security-csharp-frontend-plugin/rules/S3649.json
echo "$OLD_RULE_CONTENT" > frontend/dotnet/sonar-security-vbnet-frontend-plugin/rules/S3649.html
git add . && git commit -q -m "$INITIAL_COMMIT_MSG"

echo '<rule>new</rule>' > frontend/dotnet/sonar-security-csharp-frontend-plugin/rules/S3649.html
echo '{"updated":true}' > frontend/dotnet/sonar-security-csharp-frontend-plugin/rules/S3650.json
git add .

printf '=== PATH:frontend/dotnet/sonar-security-csharp-frontend-plugin ===\nRunning rule-api update\nFound 4 rule(s) to update\n=== PATH:frontend/dotnet/sonar-security-vbnet-frontend-plugin ===\nRunning rule-api update\nFound 4 rule(s) to update\n' > rule-api-logs.txt

OUTPUT=$(run_script "$WORK_DIR")
assert_output_contains "3-level: csharp row shows 4 to update and 2 updated" \
  'sonar-security-csharp-frontend-plugin/sonarpedia.json.*4.*2' "$OUTPUT"
assert_output_contains "3-level: vbnet row shows 4 to update and 0 updated" \
  'sonar-security-vbnet-frontend-plugin/sonarpedia.json.*4.*0' "$OUTPUT"
rm -rf "$WORK_DIR"

# ---------------------------------------------------------------------------
# Test 4: no rules to update — fallback summary string
# ---------------------------------------------------------------------------
echo "--- Test 4: no rules to update (fallback summary) ---"
WORK_DIR=$(run_test)
cd "$WORK_DIR"
init_git
echo '{}' > sonarpedia.json
git add . && git commit -q -m "$INITIAL_COMMIT_MSG"

printf '=== PATH:. ===\nRunning rule-api update\nFound 0 rule(s) to update\n' > rule-api-logs.txt

OUTPUT=$(run_script "$WORK_DIR")
assert_output_contains "zero rules: fallback summary written" \
  'summary=Update rule metadata' "$OUTPUT"
rm -rf "$WORK_DIR"

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
echo ""
echo "Results: $pass passed, $fail failed"
[[ "$fail" -eq 0 ]]