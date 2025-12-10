#!/usr/bin/env bash
set -euo pipefail

# Inputs via environment:
# - VERSION: version string with -SNAPSHOT suffix (e.g., 1.2.3-SNAPSHOT)
# - EXCLUDED_MODULES: optional comma-separated list of module paths to exclude

VERSION=${VERSION:-}
EXCLUDED_MODULES=${EXCLUDED_MODULES:-}

if [[ -z "$VERSION" ]]; then
  echo "ERROR: VERSION env var is required" >&2
  exit 1
fi

# Build dynamic exclusion args from EXCLUDED_MODULES (comma-separated)
EXCLUDE_ARGS=()
if [[ -n "$EXCLUDED_MODULES" ]]; then
  IFS=',' read -r -a modules <<< "$EXCLUDED_MODULES"
  for m in "${modules[@]}"; do
    # Trim leading/trailing whitespace
    m_trimmed="${m##+([[:space:]])}"
    m_trimmed="${m_trimmed%%+([[:space:]])}"
    # Fallback trim if extglob isn't enabled
    if [[ -z "${m_trimmed}" ]]; then
      m_trimmed="$m"
    fi
    # Remove surrounding spaces using sed as a backup
    m_trimmed="$(printf "%s" "$m_trimmed" | sed 's/^\s\+//;s/\s\+$//')"
    # Skip empty entries
    if [[ -z "$m_trimmed" ]]; then
      continue
    fi
    # Append exclusion for all files under the module path
    EXCLUDE_ARGS+=( -not -path "./${m_trimmed}/*" )
  done
fi

# Update all pom.xml files to the new snapshot version, excluding specified modules
# Keep this robust by using a clear sed pattern
find . -type f -name "pom.xml" \
  "${EXCLUDE_ARGS[@]}" \
  -exec sed -i "s#<version>.*-SNAPSHOT</version>#<version>${VERSION}</version>#g" {} +

# Update gradle.properties to the new snapshot version, if present
if [[ -f gradle.properties ]]; then
  sed -i "s/^version=.*-SNAPSHOT$/version=${VERSION}/" gradle.properties || true
fi

echo "Bump complete: VERSION=${VERSION}, EXCLUDED_MODULES=${EXCLUDED_MODULES}"
