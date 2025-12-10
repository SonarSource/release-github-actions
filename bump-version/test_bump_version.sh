#!/usr/bin/env bash
set -euo pipefail

# Basic tests for bump_version.sh using a temporary workspace
# This script is intended to be run locally or in CI to validate behavior.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUMP_SCRIPT="${SCRIPT_DIR}/bump_version.sh"

assert() {
  local msg="$1"; shift
  if ! "$@"; then
    echo "ASSERT FAIL: ${msg}" >&2
    exit 1
  fi
}

# Create temp workspace
TMPDIR="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

# Scaffold files
mkdir -p "$TMPDIR/moduleA" "$TMPDIR/moduleB" "$TMPDIR/e2e/projects" "$TMPDIR/e2e/benchmarks"

cat > "$TMPDIR/pom.xml" <<'XML'
<project>
  <version>0.0.1-SNAPSHOT</version>
</project>
XML

cat > "$TMPDIR/moduleA/pom.xml" <<'XML'
<project>
  <version>0.0.1-SNAPSHOT</version>
</project>
XML

cat > "$TMPDIR/moduleB/pom.xml" <<'XML'
<project>
  <version>0.0.1-SNAPSHOT</version>
</project>
XML

cat > "$TMPDIR/gradle.properties" <<'PROPS'
version=0.0.1-SNAPSHOT
PROPS

cat > "$TMPDIR/e2e/projects/pom.xml" <<'XML'
<project>
  <version>0.0.1-SNAPSHOT</version>
</project>
XML

cat > "$TMPDIR/e2e/benchmarks/pom.xml" <<'XML'
<project>
  <version>0.0.1-SNAPSHOT</version>
</project>
XML

# Run without exclusions
(
  cd "$TMPDIR"
  VERSION="1.2.3-SNAPSHOT" EXCLUDED_MODULES="" bash "$BUMP_SCRIPT"
)

# Verify root pom updated
assert "root pom updated" grep -q '<version>1.2.3-SNAPSHOT</version>' "$TMPDIR/pom.xml"
# Verify gradle.properties updated
assert "gradle.properties updated" grep -q 'version=1.2.3-SNAPSHOT' "$TMPDIR/gradle.properties"
# Verify e2e files still updated (since we didn't add static exclusions in script)
# Our script does not include static e2e exclusions; test only dynamic

# Reset files
sed -i 's/1.2.3-SNAPSHOT/0.0.1-SNAPSHOT/g' "$TMPDIR"/pom.xml "$TMPDIR"/moduleA/pom.xml "$TMPDIR"/moduleB/pom.xml "$TMPDIR"/e2e/projects/pom.xml "$TMPDIR"/e2e/benchmarks/pom.xml
sed -i 's/version=1.2.3-SNAPSHOT/version=0.0.1-SNAPSHOT/' "$TMPDIR/gradle.properties"

# Run with exclusions for moduleA and e2e/*
(
  cd "$TMPDIR"
  VERSION="2.0.0-SNAPSHOT" EXCLUDED_MODULES="moduleA,e2e/projects,e2e/benchmarks" bash "$BUMP_SCRIPT"
)

# Root pom should be updated
assert "root pom updated v2" grep -q '<version>2.0.0-SNAPSHOT</version>' "$TMPDIR/pom.xml"
# moduleA pom should remain old due to exclusion
assert "moduleA excluded" grep -q '<version>0.0.1-SNAPSHOT</version>' "$TMPDIR/moduleA/pom.xml"
# moduleB pom should be updated
assert "moduleB updated" grep -q '<version>2.0.0-SNAPSHOT</version>' "$TMPDIR/moduleB/pom.xml"
# e2e files should remain old due to exclusion
assert "e2e projects excluded" grep -q '<version>0.0.1-SNAPSHOT</version>' "$TMPDIR/e2e/projects/pom.xml"
assert "e2e benchmarks excluded" grep -q '<version>0.0.1-SNAPSHOT</version>' "$TMPDIR/e2e/benchmarks/pom.xml"
# gradle.properties updated to v2
assert "gradle.properties v2" grep -q 'version=2.0.0-SNAPSHOT' "$TMPDIR/gradle.properties"

echo "All tests passed"
