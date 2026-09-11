#!/usr/bin/env bash
# Unit tests for update_build_gradle.sh
# Run: bash test_update_build_gradle.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/update_build_gradle.sh"

PASS=0
FAIL=0

assert_contains() {
  local name="$1"
  local file="$2"
  local pattern="$3"
  if grep -qF "$pattern" "$file"; then
    echo "✅ $name"
    PASS=$((PASS+1))
  else
    echo "❌ $name (pattern not found: $pattern)"
    echo "   File contents:"
    cat "$file"
    FAIL=$((FAIL+1))
  fi
}

assert_not_contains() {
  local name="$1"
  local file="$2"
  local pattern="$3"
  if ! grep -qF "$pattern" "$file"; then
    echo "✅ $name"
    PASS=$((PASS+1))
  else
    echo "❌ $name (pattern should not be present: $pattern)"
    FAIL=$((FAIL+1))
  fi
}

assert_output_contains() {
  local name="$1"
  local output="$2"
  local pattern="$3"
  if [[ "$output" == *"$pattern"* ]]; then
    echo "✅ $name"
    PASS=$((PASS+1))
  else
    echo "❌ $name (pattern not found: $pattern)"
    echo "   Output: $output"
    FAIL=$((FAIL+1))
  fi
}

assert_exit() {
  local name="$1"
  local expected="$2"
  local actual="$3"
  if [[ "$actual" -eq "$expected" ]]; then
    echo "✅ $name"
    PASS=$((PASS+1))
  else
    echo "❌ $name (expected exit $expected, got $actual)"
    FAIL=$((FAIL+1))
  fi
}

# --- Fixtures ---

# Original versions are deliberately distinct so an unintended rewrite is visible.
make_build_gradle() {
  local dir="$1"
  cat > "$dir/build.gradle" <<'EOF'
dependencies {
  implementation ':sonar-java-plugin:8.0.0.1000'
  implementation ':sonar-java-symbolic-execution-plugin:8.1.0.2000'
  implementation ':sonar-kotlin-plugin:2.0.0.100'
  implementation ':java-a3s-context-collector:1.0.0.5'
}
EOF
}

# Runs the script in a throwaway directory holding a fresh fixture.
# Usage: run_script <dir> [VAR=value ...]
# Sets the global `rc` to the script's exit code.
run_script() {
  local dir="$1"; shift
  make_build_gradle "$dir"
  if (cd "$dir" && env "$@" bash "$SCRIPT") >/dev/null 2>&1; then
    rc=0
  else
    rc=$?
  fi
}

NEW=9.9.9.9999

# --- Default / prefixed behaviour ---

# Regression test for the silent-verbatim bug: a consumer that forwards an unset input passes an
# empty string, which does NOT pick up the action's declared default. Empty must mean prefixed.
for flag_desc in "unset:" "empty:SET_SONAR_PREFIX=" "explicit true:SET_SONAR_PREFIX=true" \
                 "True:SET_SONAR_PREFIX=True" "TRUE:SET_SONAR_PREFIX=TRUE"; do
  desc="${flag_desc%%:*}"
  env_arg="${flag_desc#*:}"
  T=$(mktemp -d)
  # shellcheck disable=SC2086 # deliberate word split: empty env_arg must vanish
  run_script "$T" PLUGIN_NAME=java RELEASE_VERSION="$NEW" $env_arg
  assert_exit "prefix $desc → exit 0" 0 "$rc"
  assert_contains "prefix $desc → sonar-java-plugin bumped" "$T/build.gradle" ":sonar-java-plugin:$NEW"
  assert_contains "prefix $desc → family member bumped" "$T/build.gradle" ":sonar-java-symbolic-execution-plugin:$NEW"
  assert_contains "prefix $desc → unrelated plugin untouched" "$T/build.gradle" ":sonar-kotlin-plugin:2.0.0.100"
  rm -rf "$T"
done

# --- Unprefixed behaviour ---

# Verbatim match: the artifact does not follow the sonar-<name>-plugin convention.
for flag in false False FALSE; do
  T=$(mktemp -d)
  run_script "$T" PLUGIN_NAME=java-a3s-context-collector RELEASE_VERSION="$NEW" "SET_SONAR_PREFIX=$flag"
  assert_exit "prefix $flag → exit 0" 0 "$rc"
  assert_contains "prefix $flag → unprefixed artifact bumped" "$T/build.gradle" ":java-a3s-context-collector:$NEW"
  assert_not_contains "prefix $flag → no sonar- wrapping applied" "$T/build.gradle" "sonar-java-a3s-context-collector"
  rm -rf "$T"
done

# No family wildcard when unprefixed: plugin-name "java" must NOT touch sonar-java-plugin.
T=$(mktemp -d)
run_script "$T" PLUGIN_NAME=java RELEASE_VERSION="$NEW" SET_SONAR_PREFIX=false
assert_exit "unprefixed 'java' → exit 0" 0 "$rc"
assert_contains "unprefixed 'java' leaves sonar-java-plugin alone" "$T/build.gradle" ":sonar-java-plugin:8.0.0.1000"
assert_not_contains "unprefixed 'java' rewrites nothing" "$T/build.gradle" "$NEW"
rm -rf "$T"

# --- plugin-artifacts list ---

# Each entry is matched exactly — no family wildcard, so symbolic-execution stays put.
T=$(mktemp -d)
run_script "$T" PLUGIN_NAME=jvm PLUGIN_ARTIFACTS="java,kotlin" RELEASE_VERSION="$NEW"
assert_exit "plugin-artifacts → exit 0" 0 "$rc"
assert_contains "plugin-artifacts bumps java" "$T/build.gradle" ":sonar-java-plugin:$NEW"
assert_contains "plugin-artifacts bumps kotlin" "$T/build.gradle" ":sonar-kotlin-plugin:$NEW"
assert_contains "plugin-artifacts does not family-match" "$T/build.gradle" ":sonar-java-symbolic-execution-plugin:8.1.0.2000"
rm -rf "$T"

# Whitespace around entries is trimmed.
T=$(mktemp -d)
run_script "$T" PLUGIN_NAME=jvm PLUGIN_ARTIFACTS=" java , kotlin " RELEASE_VERSION="$NEW"
assert_exit "padded plugin-artifacts → exit 0" 0 "$rc"
assert_contains "padded plugin-artifacts bumps java" "$T/build.gradle" ":sonar-java-plugin:$NEW"
assert_contains "padded plugin-artifacts bumps kotlin" "$T/build.gradle" ":sonar-kotlin-plugin:$NEW"
rm -rf "$T"

# plugin-artifacts combined with the unprefixed flag.
T=$(mktemp -d)
run_script "$T" PLUGIN_NAME=jvm PLUGIN_ARTIFACTS="java-a3s-context-collector" \
  RELEASE_VERSION="$NEW" SET_SONAR_PREFIX=false
assert_exit "unprefixed plugin-artifacts → exit 0" 0 "$rc"
assert_contains "unprefixed plugin-artifacts bumped" "$T/build.gradle" ":java-a3s-context-collector:$NEW"
rm -rf "$T"

# --- Invalid set-sonar-prefix fails loudly instead of matching verbatim ---

for bad in yes 1 ture TrUe no; do
  T=$(mktemp -d)
  run_script "$T" PLUGIN_NAME=java RELEASE_VERSION="$NEW" "SET_SONAR_PREFIX=$bad"
  assert_exit "invalid prefix '$bad' → exit 1" 1 "$rc"
  assert_not_contains "invalid prefix '$bad' leaves build file untouched" "$T/build.gradle" "$NEW"
  rm -rf "$T"
done

# The error message names the offending value.
T=$(mktemp -d)
make_build_gradle "$T"
err=$( (cd "$T" && PLUGIN_NAME=java RELEASE_VERSION="$NEW" SET_SONAR_PREFIX=yes bash "$SCRIPT") 2>&1 || true )
assert_output_contains "invalid prefix error message names the value" \
  "$err" "::error::Invalid set-sonar-prefix 'yes'"
rm -rf "$T"

# --- Required variables ---

T=$(mktemp -d)
run_script "$T" PLUGIN_NAME=java
assert_exit "missing RELEASE_VERSION → exit 1" 1 "$rc"
rm -rf "$T"

T=$(mktemp -d)
run_script "$T" RELEASE_VERSION="$NEW"
assert_exit "missing PLUGIN_NAME → exit 1" 1 "$rc"
rm -rf "$T"

# --- BUILD_GRADLE_FILE override ---

T=$(mktemp -d)
make_build_gradle "$T"
mv "$T/build.gradle" "$T/custom.gradle"
if (cd "$T" && PLUGIN_NAME=java RELEASE_VERSION="$NEW" BUILD_GRADLE_FILE=custom.gradle \
    bash "$SCRIPT") >/dev/null 2>&1; then rc=0; else rc=$?; fi
assert_exit "BUILD_GRADLE_FILE override → exit 0" 0 "$rc"
assert_contains "BUILD_GRADLE_FILE override applied" "$T/custom.gradle" ":sonar-java-plugin:$NEW"
rm -rf "$T"

# --- Summary ---
echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
