#!/usr/bin/env bash
# Updates analyzer plugin versions in a Gradle build file.
#
# Environment variables (required):
#   BUILD_GRADLE_FILE - path to the Gradle build file to update
#   RELEASE_VERSION   - new version string (e.g. 11.44.2.12345)
#
# Environment variables (optional):
#   PLUGIN_ARTIFACTS  - comma-separated artifact names to update instead of PLUGIN_NAME
#   PLUGIN_NAME       - plugin name used when PLUGIN_ARTIFACTS is empty; supports glob (e.g. java.*)

set -euo pipefail

BUILD_GRADLE_FILE="${BUILD_GRADLE_FILE:?BUILD_GRADLE_FILE is required}"
RELEASE_VERSION="${RELEASE_VERSION:?RELEASE_VERSION is required}"
PLUGIN_NAME="${PLUGIN_NAME:?PLUGIN_NAME is required}"
PLUGIN_ARTIFACTS="${PLUGIN_ARTIFACTS:-}"

if [[ ! -f "$BUILD_GRADLE_FILE" ]]; then
  echo "::error::${BUILD_GRADLE_FILE} not found." >&2
  exit 1
fi

declare -a plugins=()
if [[ -n "$PLUGIN_ARTIFACTS" ]]; then
  echo "Using plugin-artifacts: $PLUGIN_ARTIFACTS"
  IFS=',' read -ra raw_plugins <<< "$PLUGIN_ARTIFACTS"
  for raw in "${raw_plugins[@]}"; do
    plugin="$(echo "$raw" | xargs)"
    [[ -n "$plugin" ]] && plugins+=("$plugin")
  done
else
  echo "Using plugin-name: $PLUGIN_NAME"
  plugins=("${PLUGIN_NAME}.*")
fi

for plugin in "${plugins[@]}"; do
  echo "Updating analyzer version in ${BUILD_GRADLE_FILE} for plugin ${plugin}"
  # Use a temp file for cross-platform compatibility (macOS BSD sed vs GNU sed)
  local_tmp=$(mktemp)
  sed "s/\(:sonar-$plugin-plugin:\)[0-9.]*/\1$RELEASE_VERSION/g" "$BUILD_GRADLE_FILE" > "$local_tmp"
  mv "$local_tmp" "$BUILD_GRADLE_FILE"
done

echo "Showing diff:"
git --no-pager diff "$BUILD_GRADLE_FILE" 2>/dev/null || true
