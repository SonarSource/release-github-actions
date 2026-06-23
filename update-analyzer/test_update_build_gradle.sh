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
    echo "❌ $name (pattern unexpectedly found: $pattern)"
    FAIL=$((FAIL+1))
  fi
}

make_fixture() {
  cat > "$1" <<'EOF'
dependencies {
    compile ":sonar-java-plugin:1.0.0"
    compile ":sonar-python-plugin:2.3.4"
    compile ":sonar-other-dep:5.5.5"
}
EOF
}

# --- Test: update by PLUGIN_NAME ---
TMP=$(mktemp)
make_fixture "$TMP"
BUILD_GRADLE_FILE="$TMP" PLUGIN_NAME=java RELEASE_VERSION=1.2.3.4567 \
  bash "$SCRIPT" >/dev/null 2>&1
assert_contains "plugin-name updates matching plugin" "$TMP" ':sonar-java-plugin:1.2.3.4567'
assert_not_contains "plugin-name does not touch other plugins" "$TMP" ':sonar-python-plugin:1.2.3.4567'
assert_not_contains "non-plugin line untouched" "$TMP" ':sonar-other-dep:1.2.3.4567'
rm "$TMP"

# --- Test: update by PLUGIN_ARTIFACTS (single) ---
TMP=$(mktemp)
make_fixture "$TMP"
BUILD_GRADLE_FILE="$TMP" PLUGIN_NAME=ignored PLUGIN_ARTIFACTS=python RELEASE_VERSION=9.9.9.9999 \
  bash "$SCRIPT" >/dev/null 2>&1
assert_contains "plugin-artifacts updates named artifact" "$TMP" ':sonar-python-plugin:9.9.9.9999'
assert_not_contains "plugin-artifacts does not touch others" "$TMP" ':sonar-java-plugin:9.9.9.9999'
rm "$TMP"

# --- Test: update by PLUGIN_ARTIFACTS (comma-separated) ---
TMP=$(mktemp)
make_fixture "$TMP"
BUILD_GRADLE_FILE="$TMP" PLUGIN_NAME=ignored PLUGIN_ARTIFACTS='java,python' RELEASE_VERSION=3.0.0.1 \
  bash "$SCRIPT" >/dev/null 2>&1
assert_contains "multi-artifact updates java" "$TMP" ':sonar-java-plugin:3.0.0.1'
assert_contains "multi-artifact updates python" "$TMP" ':sonar-python-plugin:3.0.0.1'
rm "$TMP"

# --- Test: missing file fails ---
if BUILD_GRADLE_FILE=/nonexistent/build.gradle PLUGIN_NAME=java RELEASE_VERSION=1.0 \
    bash "$SCRIPT" >/dev/null 2>&1; then
  echo "❌ missing file should fail"
  FAIL=$((FAIL+1))
else
  echo "✅ missing file correctly fails"
  PASS=$((PASS+1))
fi

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed"
[[ "$FAIL" -eq 0 ]]
