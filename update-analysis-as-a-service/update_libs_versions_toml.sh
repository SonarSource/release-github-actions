#!/usr/bin/env bash
# Updates analyzer version keys in gradle/libs.versions.toml for Analysis as a Service.
#
# Environment variables (required):
#   LIBS_VERSIONS_TOML - path to gradle/libs.versions.toml
#   PLUGIN_NAME        - plugin name used when PLUGIN_ARTIFACTS is empty
#   RELEASE_VERSION    - new version string (e.g. 1.2.3.45678)
#
# Environment variables (optional):
#   PLUGIN_ARTIFACTS   - comma-separated artifact names to update instead of PLUGIN_NAME

set -euo pipefail

LIBS_VERSIONS_TOML="${LIBS_VERSIONS_TOML:-gradle/libs.versions.toml}"
RELEASE_VERSION="${RELEASE_VERSION:?RELEASE_VERSION is required}"
PLUGIN_NAME="${PLUGIN_NAME:?PLUGIN_NAME is required}"
PLUGIN_ARTIFACTS="${PLUGIN_ARTIFACTS:-}"

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

candidate_keys() {
  local artifact="$1"
  local base="${artifact%-enterprise}"

  if [[ "$base" == sonar-* ]]; then
    if [[ "$base" != *-plugin ]]; then
      printf '%s-plugin\n' "$base"
    fi
    printf '%s\n' "$base"
    return
  fi

  if [[ "$base" != *-plugin ]]; then
    printf 'sonar-%s-plugin\n' "$base"
  fi
  printf 'sonar-%s\n' "$base"
}

find_version_key() {
  local artifact="$1"
  local key

  while IFS= read -r key; do
    if VERSION_CATALOG_KEY="$key" awk '
      BEGIN { key = ENVIRON["VERSION_CATALOG_KEY"] }
      function trim(value) {
        sub(/^[[:space:]]+/, "", value)
        sub(/[[:space:]]+$/, "", value)
        return value
      }
      /^\[versions\][[:space:]]*$/ { in_versions = 1; next }
      /^\[/ { in_versions = 0 }
      in_versions {
        split($0, parts, "=")
        if (trim(parts[1]) == key && $0 ~ /^[^=]+=[[:space:]]*"[^"]*"/) {
          found = 1
        }
      }
      END { exit found ? 0 : 1 }
    ' "$LIBS_VERSIONS_TOML"; then
      printf '%s' "$key"
      return 0
    fi
  done < <(candidate_keys "$artifact")

  return 1
}

update_version_key() {
  local key="$1"
  local tmp

  tmp=$(mktemp)
  VERSION_CATALOG_KEY="$key" RELEASE_VERSION="$RELEASE_VERSION" awk '
    BEGIN {
      key = ENVIRON["VERSION_CATALOG_KEY"]
      version = ENVIRON["RELEASE_VERSION"]
    }
    function trim(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      return value
    }
    /^\[versions\][[:space:]]*$/ { in_versions = 1; print; next }
    /^\[/ { in_versions = 0 }
    in_versions {
      split($0, parts, "=")
    }
    in_versions && trim(parts[1]) == key && $0 ~ /^[^=]+=[[:space:]]*"[^"]*"/ && match($0, /"[^"]*"/) {
      $0 = substr($0, 1, RSTART - 1) "\"" version "\"" substr($0, RSTART + RLENGTH)
    }
    { print }
  ' "$LIBS_VERSIONS_TOML" > "$tmp"
  mv "$tmp" "$LIBS_VERSIONS_TOML"
  echo "Updated ${key} to ${RELEASE_VERSION}"
}

if [[ ! -f "$LIBS_VERSIONS_TOML" ]]; then
  echo "::error::${LIBS_VERSIONS_TOML} not found." >&2
  exit 1
fi

declare -a artifacts=()
if [[ -n "$PLUGIN_ARTIFACTS" ]]; then
  declare -a raw_artifacts=()
  IFS=',' read -ra raw_artifacts <<< "$PLUGIN_ARTIFACTS"
  for raw_artifact in "${raw_artifacts[@]}"; do
    artifact="$(trim "$raw_artifact")"
    if [[ -n "$artifact" ]]; then
      artifacts+=("$artifact")
    fi
  done
fi

if [[ "${#artifacts[@]}" -eq 0 ]]; then
  artifacts=("$PLUGIN_NAME")
fi

declare -a updated_keys=()
for artifact in "${artifacts[@]}"; do
  artifact="$(trim "$artifact")"
  if [[ -z "$artifact" ]]; then
    continue
  fi

  if ! key="$(find_version_key "$artifact")"; then
    echo "::warning::No version key found for artifact '${artifact}' in ${LIBS_VERSIONS_TOML}. Tried: $(candidate_keys "$artifact" | paste -sd ', ' -). Skipping." >&2
    continue
  fi

  already_updated=false
  if [[ "${#updated_keys[@]}" -gt 0 ]]; then
    for updated_key in "${updated_keys[@]}"; do
      if [[ "$updated_key" == "$key" ]]; then
        already_updated=true
        break
      fi
    done
  fi

  if [[ "$already_updated" == "false" ]]; then
    update_version_key "$key"
    updated_keys+=("$key")
  fi
done

if [[ "${#updated_keys[@]}" -eq 0 ]]; then
  echo "::warning::No version keys were updated — analyzer likely not yet onboarded to SQAA. No PR will be created." >&2
  exit 0
fi

echo "Showing diff:"
git --no-pager diff "$LIBS_VERSIONS_TOML" 2>/dev/null || true
