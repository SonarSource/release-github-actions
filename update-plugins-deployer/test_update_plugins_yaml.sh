#!/usr/bin/env bash
# Unit tests for update_plugins_yaml.sh
# Run: bash test_update_plugins_yaml.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/update_plugins_yaml.sh"

PASS=0
FAIL=0

run_test() {
  local name="$1"
  local expected_exit="$2"
  shift 2
  if "$@" >/dev/null 2>&1; then
    actual_exit=0
  else
    actual_exit=$?
  fi
  if [[ "$actual_exit" -eq "$expected_exit" ]]; then
    echo "✅ $name"
    PASS=$((PASS+1))
  else
    echo "❌ $name (expected exit $expected_exit, got $actual_exit)"
    FAIL=$((FAIL+1))
  fi
}

assert_contains() {
  local name="$1"
  local file="$2"
  local pattern="$3"
  if grep -q "$pattern" "$file"; then
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
  if ! grep -q "$pattern" "$file"; then
    echo "✅ $name"
    PASS=$((PASS+1))
  else
    echo "❌ $name (pattern should not be present: $pattern)"
    FAIL=$((FAIL+1))
  fi
}

# --- Fixtures ---

make_plugins_yaml() {
  local dir="$1"
  cat > "$dir/plugins.yaml" <<'EOF'
versions:
  sonar-java: &version-sonar-java 8.29.0.43460
  sonar-security: &version-sonar-security 11.29.0.45905
  sonar-go: &version-sonar-go 1.36.0.5922
  sonar-dotnet: &version-sonar-dotnet 10.25.0.139117
  sonar-iac: &version-sonar-iac 2.9.0.20183
  sonar-text: &version-sonar-text 2.43.0.11106
  sonar-python: &version-sonar-python 5.21.0.32726
  sonar-php: &version-sonar-php 3.56.0.15870
  java-a3s-context-collector: &version-java-a3s-context-collector 1.0.0.100

plugins:
  - key: sonar-java
    version: *version-sonar-java

  - key: sonar-security
    version: *version-sonar-security

  - key: sonar-security-java-frontend
    version: *version-sonar-security

  - key: sonar-go-enterprise
    version: *version-sonar-go

  - key: sonar-csharp-enterprise
    version: *version-sonar-dotnet

  - key: sonar-vbnet-enterprise
    version: *version-sonar-dotnet

  - key: sonar-iac-enterprise
    version: *version-sonar-iac

  - key: sonar-text-enterprise
    version: *version-sonar-text

  - key: sonar-python-enterprise
    version: *version-sonar-python

  - key: sonar-php
    version: *version-sonar-php

  - key: java-a3s-context-collector
    version: *version-java-a3s-context-collector
EOF
}

# --- Tests ---

# Test: single artifact update (java)
T=$(mktemp -d)
make_plugins_yaml "$T"
PLUGINS_YAML="$T/plugins.yaml" PLUGIN_ARTIFACTS="" PLUGIN_NAME="java" RELEASE_VERSION="9.0.0.12345" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_java=0 || actual_java=$?
if [[ "$actual_java" -eq 0 ]]; then
  assert_contains "java anchor updated" "$T/plugins.yaml" "sonar-java: &version-sonar-java 9.0.0.12345"
  assert_not_contains "security anchor unchanged" "$T/plugins.yaml" "sonar-security: &version-sonar-security 9.0.0.12345"
else
  echo "❌ java update failed (exit $actual_java)"
  FAIL=$((FAIL+2))
fi
rm -rf "$T"

# Test: artifact with -enterprise suffix (go-enterprise → sonar-go)
T=$(mktemp -d)
make_plugins_yaml "$T"
PLUGINS_YAML="$T/plugins.yaml" PLUGIN_ARTIFACTS="go-enterprise" PLUGIN_NAME="go" RELEASE_VERSION="2.0.0.1" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_go=0 || actual_go=$?
if [[ "$actual_go" -eq 0 ]]; then
  assert_contains "go anchor updated" "$T/plugins.yaml" "sonar-go: &version-sonar-go 2.0.0.1"
  assert_not_contains "java anchor unchanged after go update" "$T/plugins.yaml" "sonar-java: &version-sonar-java 2.0.0.1"
else
  echo "❌ go-enterprise update failed (exit $actual_go)"
  FAIL=$((FAIL+2))
fi
rm -rf "$T"

# Test: csharp-enterprise → sonar-dotnet anchor
T=$(mktemp -d)
make_plugins_yaml "$T"
PLUGINS_YAML="$T/plugins.yaml" PLUGIN_ARTIFACTS="csharp-enterprise,vbnet-enterprise" PLUGIN_NAME="dotnet-enterprise" RELEASE_VERSION="11.0.0.1" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_dotnet=0 || actual_dotnet=$?
if [[ "$actual_dotnet" -eq 0 ]]; then
  assert_contains "dotnet anchor updated once" "$T/plugins.yaml" "sonar-dotnet: &version-sonar-dotnet 11.0.0.1"
else
  echo "❌ dotnet update failed (exit $actual_dotnet)"
  FAIL=$((FAIL+1))
fi
rm -rf "$T"

# Test: security with frontends — only anchor updated, frontends stay as aliases
T=$(mktemp -d)
make_plugins_yaml "$T"
PLUGINS_YAML="$T/plugins.yaml" PLUGIN_ARTIFACTS="security" PLUGIN_NAME="security" RELEASE_VERSION="12.0.0.1" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_sec=0 || actual_sec=$?
if [[ "$actual_sec" -eq 0 ]]; then
  assert_contains "security anchor updated" "$T/plugins.yaml" "sonar-security: &version-sonar-security 12.0.0.1"
else
  echo "❌ security update failed (exit $actual_sec)"
  FAIL=$((FAIL+1))
fi
rm -rf "$T"

# Test: SONAR_PREFIX="false" → anchor not prefixed with sonar-
T=$(mktemp -d)
make_plugins_yaml "$T"
PLUGINS_YAML="$T/plugins.yaml" PLUGIN_ARTIFACTS="" PLUGIN_NAME="java-a3s-context-collector" SONAR_PREFIX="false" RELEASE_VERSION="2.0.0.200" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_a3s=0 || actual_a3s=$?
if [[ "$actual_a3s" -eq 0 ]]; then
  assert_contains "java-a3s-context-collector anchor updated" "$T/plugins.yaml" "java-a3s-context-collector: &version-java-a3s-context-collector 2.0.0.200"
  assert_not_contains "java-a3s-context-collector anchor not sonar-prefixed" "$T/plugins.yaml" "sonar-java-a3s-context-collector"
else
  echo "❌ java-a3s-context-collector update failed (exit $actual_a3s)"
  FAIL=$((FAIL+2))
fi
rm -rf "$T"

# Test: SONAR_PREFIX="true" → anchor is prefixed with sonar-
T=$(mktemp -d)
make_plugins_yaml "$T"
PLUGINS_YAML="$T/plugins.yaml" PLUGIN_ARTIFACTS="" PLUGIN_NAME="java" SONAR_PREFIX="true" RELEASE_VERSION="9.1.0.12345" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_prefix=0 || actual_prefix=$?
if [[ "$actual_prefix" -eq 0 ]]; then
  assert_contains "SONAR_PREFIX=true prefixes anchor" "$T/plugins.yaml" "sonar-java: &version-sonar-java 9.1.0.12345"
else
  echo "❌ SONAR_PREFIX=true update failed (exit $actual_prefix)"
  FAIL=$((FAIL+1))
fi
rm -rf "$T"

# Test: unknown plugin → fails hard
T=$(mktemp -d)
make_plugins_yaml "$T"
run_test "unknown plugin fails hard" 1 \
  bash -c "PLUGINS_YAML='$T/plugins.yaml' PLUGIN_ARTIFACTS='' PLUGIN_NAME='nonexistent-plugin-xyz' RELEASE_VERSION='1.0.0.1' bash '$SCRIPT'"
rm -rf "$T"

# Test: invalid ticket key → fails (handled by action.yml, but script shouldn't care)
# (ticket validation is in action.yml, not the script itself)

# --- Summary ---
echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
