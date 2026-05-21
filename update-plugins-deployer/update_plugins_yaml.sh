#!/usr/bin/env bash
# Updates the version anchor in plugins.yaml for the given plugin.
#
# Environment variables (required):
#   PLUGINS_YAML    - path to plugins.yaml
#   PLUGIN_NAME     - plugin name used to compute the anchor key
#   RELEASE_VERSION - new version string (e.g. 1.2.3.45678)

set -euo pipefail

compute_anchor_key() {
  local artifact="$1"
  # Strip -enterprise suffix
  local base="${artifact%-enterprise}"
  # dotnet special case: csharp and vbnet both map to sonar-dotnet
  case "$base" in
    csharp|vbnet) base="dotnet" ;;
    *) ;;
  esac
  echo "sonar-${base}"
}

update_anchor() {
  local anchor_key="$1"
  local version="$2"
  local file="$3"

  # Anchor line format in versions block: "  sonar-KEY: &version-sonar-KEY OLD_VERSION"
  local pattern="^  ${anchor_key}: &version-${anchor_key} "
  if ! grep -q "$pattern" "$file"; then
    echo "::error::Anchor for '${anchor_key}' not found in ${file}. Ensure plugins.yaml has a versions: entry for this plugin." >&2
    exit 1
  fi

  # Use a temp file for cross-platform compatibility (macOS BSD sed vs GNU sed)
  local tmp
  tmp=$(mktemp)
  sed "s|^\(  ${anchor_key}: &version-${anchor_key}\) .*|\1 ${version}|" "$file" > "$tmp"
  mv "$tmp" "$file"
  echo "Updated ${anchor_key} to ${version}"
}

PLUGINS_YAML="${PLUGINS_YAML:-plugins.yaml}"
RELEASE_VERSION="${RELEASE_VERSION:?RELEASE_VERSION is required}"
PLUGIN_NAME="${PLUGIN_NAME:?PLUGIN_NAME is required}"

# The anchor key is always derived from PLUGIN_NAME.
# PLUGIN_ARTIFACTS lists individual artifacts for build.gradle sed matching,
# but plugins.yaml uses one anchor per plugin family (e.g. sonar-security covers
# all security frontends via aliases).
anchor_key=$(compute_anchor_key "$PLUGIN_NAME")
update_anchor "$anchor_key" "$RELEASE_VERSION" "$PLUGINS_YAML"

echo "Showing diff:"
git --no-pager diff "$PLUGINS_YAML" 2>/dev/null || true
