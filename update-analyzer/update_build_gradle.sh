#!/usr/bin/env bash
# Updates the analyzer version for one or more plugin artifacts in sonar-enterprise's build file.
#
# Environment variables (required):
#   RELEASE_VERSION   - new version string (e.g. 1.2.3.45678)
#   PLUGIN_NAME       - plugin language key (e.g. java); used when PLUGIN_ARTIFACTS is empty
#
# Environment variables (optional):
#   PLUGIN_ARTIFACTS  - comma-separated artifact list; takes precedence over PLUGIN_NAME and is
#                       matched entry by entry, with no family wildcard
#   SET_SONAR_PREFIX  - boolean; true (default) wraps each name as "sonar-<name>-plugin", false
#                       matches the name verbatim. Any other value is a caller error and exits 1
#   BUILD_GRADLE_FILE - path to the build file (default: build.gradle)

set -euo pipefail

BUILD_GRADLE_FILE="${BUILD_GRADLE_FILE:-build.gradle}"
RELEASE_VERSION="${RELEASE_VERSION:?RELEASE_VERSION is required}"
PLUGIN_NAME="${PLUGIN_NAME:?PLUGIN_NAME is required}"
PLUGIN_ARTIFACTS="${PLUGIN_ARTIFACTS:-}"

# Failing open to the verbatim branch would be silent: the pattern matches nothing, and
# create-pull-request reports an unchanged build file as a successful no-op.
case "${SET_SONAR_PREFIX:-true}" in
  true|True|TRUE)    SET_SONAR_PREFIX=true ;;
  false|False|FALSE) SET_SONAR_PREFIX=false ;;
  *)
    echo "::error::Invalid set-sonar-prefix '${SET_SONAR_PREFIX}'. Must be 'true' or 'false'." >&2
    exit 1
    ;;
esac

# Prepare the list of plugins to update
if [[ -n "$PLUGIN_ARTIFACTS" ]]; then
  echo "Using plugin-artifacts: $PLUGIN_ARTIFACTS"
  IFS=',' read -ra PLUGINS <<< "$PLUGIN_ARTIFACTS"
elif [[ "$SET_SONAR_PREFIX" == "true" ]]; then
  # Family match: plugin-name "java" also covers sonar-java-symbolic-execution-plugin.
  echo "Using plugin-name: $PLUGIN_NAME"
  PLUGINS=("${PLUGIN_NAME}.*")
else
  # Unprefixed artifacts are matched exactly - no family wildcard.
  echo "Using plugin-name: $PLUGIN_NAME"
  PLUGINS=("$PLUGIN_NAME")
fi

# Update each plugin
for plugin in "${PLUGINS[@]}"; do
  plugin=$(echo "$plugin" | xargs)
  # SET_SONAR_PREFIX controls the sonar-<name>-plugin wrapping. Some artifacts
  # (e.g. java-a3s-context-collector) do not follow that convention.
  if [[ "$SET_SONAR_PREFIX" == "true" ]]; then
    artifact="sonar-${plugin}-plugin"
  else
    artifact="$plugin"
  fi
  echo "Updating analyzer version in $BUILD_GRADLE_FILE for artifact :$artifact:"
  # Use a temp file for cross-platform compatibility (macOS BSD sed vs GNU sed)
  tmp=$(mktemp)
  sed "s/\(:${artifact}:\)[0-9.]*/\1${RELEASE_VERSION}/g" "$BUILD_GRADLE_FILE" > "$tmp"
  mv "$tmp" "$BUILD_GRADLE_FILE"
done

echo "Showing diff:"
git --no-pager diff "$BUILD_GRADLE_FILE" 2>/dev/null || true
