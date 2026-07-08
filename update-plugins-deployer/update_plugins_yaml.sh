#!/usr/bin/env bash
# Updates the version anchor in plugins.yaml for the given plugin.
#
# Environment variables (required):
#   PLUGINS_YAML    - path to plugins.yaml
#   PLUGIN_NAME     - plugin name used to compute the anchor key
#   RELEASE_VERSION - new version string (e.g. 1.2.3.45678)
#
# Environment variables (optional):
#   SET_SONAR_PREFIX - boolean; true (default) prefixes the anchor key with "sonar-",
#                      false leaves the key unprefixed

set -euo pipefail

compute_anchor_key() {
  local artifact="$1"
  # Strip -enterprise suffix
  local base="${artifact%-enterprise}"
  case "$base" in
    # dotnet special case: csharp and vbnet both map to sonar-dotnet
    csharp|vbnet) base="dotnet" ;;
    *) ;;
  esac
  # SET_SONAR_PREFIX controls whether the anchor key is prefixed with "sonar-".
  # Some plugins (e.g. java-a3s-context-collector) use an unprefixed anchor.
  if [[ "$SET_SONAR_PREFIX" == "true" ]]; then
    echo "sonar-${base}"
  else
    echo "$base"
  fi
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
SET_SONAR_PREFIX="${SET_SONAR_PREFIX:-true}"

# The anchor key is always derived from PLUGIN_NAME — one anchor per plugin family
# (e.g. sonar-security covers all security frontends via aliases).
anchor_key=$(compute_anchor_key "$PLUGIN_NAME")
update_anchor "$anchor_key" "$RELEASE_VERSION" "$PLUGINS_YAML"

echo "Showing diff:"
git --no-pager diff "$PLUGINS_YAML" 2>/dev/null || true
