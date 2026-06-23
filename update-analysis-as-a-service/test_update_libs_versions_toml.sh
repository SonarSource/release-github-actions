#!/usr/bin/env bash
# Unit tests for update_libs_versions_toml.sh
# Run: bash update-analysis-as-a-service/test_update_libs_versions_toml.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/update_libs_versions_toml.sh"

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
    echo "OK $name"
    PASS=$((PASS+1))
  else
    echo "FAIL $name (expected exit $expected_exit, got $actual_exit)"
    FAIL=$((FAIL+1))
  fi
}

assert_contains() {
  local name="$1"
  local file="$2"
  local pattern="$3"
  if grep -Fq "$pattern" "$file"; then
    echo "OK $name"
    PASS=$((PASS+1))
  else
    echo "FAIL $name (pattern not found: $pattern)"
    echo "File contents:"
    cat "$file"
    FAIL=$((FAIL+1))
  fi
}

assert_not_contains() {
  local name="$1"
  local file="$2"
  local pattern="$3"
  if ! grep -Fq "$pattern" "$file"; then
    echo "OK $name"
    PASS=$((PASS+1))
  else
    echo "FAIL $name (pattern should not be present: $pattern)"
    FAIL=$((FAIL+1))
  fi
}

make_libs_versions_toml() {
  local dir="$1"
  mkdir -p "$dir/gradle"
  cat > "$dir/gradle/libs.versions.toml" <<'EOF'
[versions]
sonar-dre = "2.3.0.12320"
sonar-go = "1.38.0.6335"
sonar-java = "0.0.0.1"
sonar-java-plugin = "8.25.0.42802"
sonar-java.plugin = "1.0.0.100"
sonar-javaXplugin = "1.0.0.200"
sonar-java-symbolic-execution-plugin = "8.18.0.242"
sonar-security = "11.33.0.47162"
sonar-python = "5.23.0.33560"

[libraries]
sonar-dre-plugin = { module = "com.sonarsource.dre:sonar-dre-plugin", version.ref = "sonar-dre" }
sonar-go-plugin = { module = "com.sonarsource.go:sonar-go-enterprise-plugin", version.ref = "sonar-go" }
sonar-java-plugin = { module = "org.sonarsource.java:sonar-java-plugin", version.ref = "sonar-java-plugin" }
sonar-java-symbolic-execution-plugin = { module = "org.sonarsource.java:sonar-java-symbolic-execution-plugin", version.ref = "sonar-java-symbolic-execution-plugin" }
sonar-security-plugin = { module = "com.sonarsource.security:sonar-security-plugin", version.ref = "sonar-security" }
sonar-python-plugin = { module = "com.sonarsource.python:sonar-python-enterprise-plugin", version.ref = "sonar-python" }

[plugins]
sonar-dre = "com.sonarsource.dre:sonar-dre-plugin:2.3.0.12320"
EOF
}

T=$(mktemp -d)
make_libs_versions_toml "$T"
LIBS_VERSIONS_TOML="$T/gradle/libs.versions.toml" PLUGIN_NAME="dre" RELEASE_VERSION="2.4.0.1" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_dre=0 || actual_dre=$?
if [[ "$actual_dre" -eq 0 ]]; then
  assert_contains "dre version updated" "$T/gradle/libs.versions.toml" 'sonar-dre = "2.4.0.1"'
  assert_not_contains "dre library alias unchanged" "$T/gradle/libs.versions.toml" 'sonar-dre-plugin = "2.4.0.1"'
  assert_contains "inline coordinate outside versions unchanged" "$T/gradle/libs.versions.toml" 'sonar-dre = "com.sonarsource.dre:sonar-dre-plugin:2.3.0.12320"'
else
  echo "FAIL dre update failed (exit $actual_dre)"
  FAIL=$((FAIL+3))
fi
rm -rf "$T"

T=$(mktemp -d)
make_libs_versions_toml "$T"
special_version='1.2&3\4'
LIBS_VERSIONS_TOML="$T/gradle/libs.versions.toml" PLUGIN_NAME="dre" RELEASE_VERSION="$special_version" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_special_version=0 || actual_special_version=$?
if [[ "$actual_special_version" -eq 0 ]]; then
  assert_contains "version with awk replacement metacharacters is written literally" "$T/gradle/libs.versions.toml" "sonar-dre = \"${special_version}\""
else
  echo "FAIL special version update failed (exit $actual_special_version)"
  FAIL=$((FAIL+1))
fi
rm -rf "$T"

T=$(mktemp -d)
make_libs_versions_toml "$T"
LIBS_VERSIONS_TOML="$T/gradle/libs.versions.toml" PLUGIN_NAME="java" RELEASE_VERSION="9.0.0.2" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_java=0 || actual_java=$?
if [[ "$actual_java" -eq 0 ]]; then
  assert_contains "java plugin version updated" "$T/gradle/libs.versions.toml" 'sonar-java-plugin = "9.0.0.2"'
  assert_contains "java family key unchanged" "$T/gradle/libs.versions.toml" 'sonar-java = "0.0.0.1"'
  assert_not_contains "java symbolic execution unchanged" "$T/gradle/libs.versions.toml" 'sonar-java-symbolic-execution-plugin = "9.0.0.2"'
else
  echo "FAIL java update failed (exit $actual_java)"
  FAIL=$((FAIL+3))
fi
rm -rf "$T"

T=$(mktemp -d)
make_libs_versions_toml "$T"
LIBS_VERSIONS_TOML="$T/gradle/libs.versions.toml" PLUGIN_NAME="java" PLUGIN_ARTIFACTS="sonar-java" RELEASE_VERSION="9.0.0.3" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_sonar_java=0 || actual_sonar_java=$?
if [[ "$actual_sonar_java" -eq 0 ]]; then
  assert_contains "sonar-prefixed java plugin version updated" "$T/gradle/libs.versions.toml" 'sonar-java-plugin = "9.0.0.3"'
  assert_contains "sonar-prefixed java family key unchanged" "$T/gradle/libs.versions.toml" 'sonar-java = "0.0.0.1"'
else
  echo "FAIL sonar-prefixed java update failed (exit $actual_sonar_java)"
  FAIL=$((FAIL+2))
fi
rm -rf "$T"

T=$(mktemp -d)
make_libs_versions_toml "$T"
LIBS_VERSIONS_TOML="$T/gradle/libs.versions.toml" PLUGIN_NAME="java" PLUGIN_ARTIFACTS="java,java-symbolic-execution" RELEASE_VERSION="9.1.0.3" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_multi_java=0 || actual_multi_java=$?
if [[ "$actual_multi_java" -eq 0 ]]; then
  assert_contains "java plugin multi update" "$T/gradle/libs.versions.toml" 'sonar-java-plugin = "9.1.0.3"'
  assert_contains "java symbolic execution multi update" "$T/gradle/libs.versions.toml" 'sonar-java-symbolic-execution-plugin = "9.1.0.3"'
else
  echo "FAIL multi java update failed (exit $actual_multi_java)"
  FAIL=$((FAIL+2))
fi
rm -rf "$T"

T=$(mktemp -d)
make_libs_versions_toml "$T"
LIBS_VERSIONS_TOML="$T/gradle/libs.versions.toml" PLUGIN_NAME="go" PLUGIN_ARTIFACTS="go-enterprise" RELEASE_VERSION="1.39.0.4" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_go=0 || actual_go=$?
if [[ "$actual_go" -eq 0 ]]; then
  assert_contains "go enterprise suffix stripped" "$T/gradle/libs.versions.toml" 'sonar-go = "1.39.0.4"'
else
  echo "FAIL go update failed (exit $actual_go)"
  FAIL=$((FAIL+1))
fi
rm -rf "$T"

T=$(mktemp -d)
make_libs_versions_toml "$T"
LIBS_VERSIONS_TOML="$T/gradle/libs.versions.toml" PLUGIN_NAME="java" PLUGIN_ARTIFACTS="sonar-java.plugin" RELEASE_VERSION="1.0.0.300" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_literal=0 || actual_literal=$?
if [[ "$actual_literal" -eq 0 ]]; then
  assert_contains "regex metachar key updated literally" "$T/gradle/libs.versions.toml" 'sonar-java.plugin = "1.0.0.300"'
  assert_contains "similar key not updated by regex" "$T/gradle/libs.versions.toml" 'sonar-javaXplugin = "1.0.0.200"'
else
  echo "FAIL literal key update failed (exit $actual_literal)"
  FAIL=$((FAIL+2))
fi
rm -rf "$T"

for blank_artifacts in " , " ","; do
  T=$(mktemp -d)
  make_libs_versions_toml "$T"
  LIBS_VERSIONS_TOML="$T/gradle/libs.versions.toml" PLUGIN_NAME="python" PLUGIN_ARTIFACTS="$blank_artifacts" RELEASE_VERSION="5.24.0.5" \
    bash "$SCRIPT" >/dev/null 2>&1 && actual_blank_artifacts=0 || actual_blank_artifacts=$?
  if [[ "$actual_blank_artifacts" -eq 0 ]]; then
    assert_contains "blank artifacts '$blank_artifacts' fall back to plugin name" "$T/gradle/libs.versions.toml" 'sonar-python = "5.24.0.5"'
  else
    echo "FAIL blank artifacts '$blank_artifacts' fallback failed (exit $actual_blank_artifacts)"
    FAIL=$((FAIL+1))
  fi
  rm -rf "$T"
done

T=$(mktemp -d)
make_libs_versions_toml "$T"
run_test "unknown plugin is skipped without failing" 0 \
  bash -c "LIBS_VERSIONS_TOML='$T/gradle/libs.versions.toml' PLUGIN_NAME='nonexistent-plugin-xyz' RELEASE_VERSION='1.0.0.1' bash '$SCRIPT'"
assert_contains "unknown plugin leaves toml unchanged" "$T/gradle/libs.versions.toml" 'sonar-python = "5.23.0.33560"'
rm -rf "$T"

T=$(mktemp -d)
make_libs_versions_toml "$T"
LIBS_VERSIONS_TOML="$T/gradle/libs.versions.toml" PLUGIN_NAME="python" PLUGIN_ARTIFACTS="python,nonexistent-plugin-xyz" RELEASE_VERSION="5.24.0.6" \
  bash "$SCRIPT" >/dev/null 2>&1 && actual_mixed=0 || actual_mixed=$?
if [[ "$actual_mixed" -eq 0 ]]; then
  assert_contains "mixed artifacts: known key updated" "$T/gradle/libs.versions.toml" 'sonar-python = "5.24.0.6"'
else
  echo "FAIL mixed artifacts: unknown should be skipped, known updated (exit $actual_mixed)"
  FAIL=$((FAIL+1))
fi
rm -rf "$T"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
