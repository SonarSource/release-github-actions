#!/bin/bash

# Get versions from Input, gradle.properties or pom.xml
# This script extracts current version from build files, calculates next version,
# and sets GitHub Actions outputs and environment variables for use in workflows.
#
# Usage: ./get_versions.sh <build-system> [version]
# Arguments:
#   - build-system: Either "maven" or "gradle" (default: "gradle")
#   - version: Optional specific version to use as next version (if not provided, auto-increments)
#
# GITHUB_OUTPUT set:
#   - current-version: The current version without -SNAPSHOT suffix
#   - current-short-version: Current version with trailing .0 removed
#   - next-version: The next development iteration version (also as NEXT_VERSION in env)
#   - next-short-version: Next version with trailing .0 removed (also as NEXT_SHORT_VERSION in env)

set -e

# Function to convert version to short format (removes trailing .0)
# This is useful for display purposes where "1.2.0" is better shown as "1.2"
# Usage: get_short_version "1.2.0" -> "1.2"
#        get_short_version "1.2.3" -> "1.2.3"
get_short_version() {
  local version="$1"
  # Check if version ends with .0 (patch version is zero)
  if [[ "$version" =~ ^([0-9]+)\.([0-9]+)\.0$ ]]; then
    # Return major.minor format
    echo "${BASH_REMATCH[1]}.${BASH_REMATCH[2]}"
  else
    # Return version as-is
    echo "$version"
  fi
}

# Parse command line arguments
BUILD_SYSTEM="${1:-gradle}"  # Default to gradle if not specified
INPUT_VERSION="${2:-}"       # Optional specific version input

# Extract the current version from the appropriate build file
# Look for version with -SNAPSHOT suffix and extract the base version
if [[ "$BUILD_SYSTEM" == "maven" ]]; then
  echo "Extracting version from pom.xml"
  # Use Perl regex to find <version>X.Y.Z-SNAPSHOT</version> pattern
  raw_version=$(grep -oPm1 "(?<=<version>)[^<]*-SNAPSHOT(?=<\/version>)" pom.xml)
else
  echo "Extracting version from gradle.properties"
  # Use Perl regex to find version=X.Y.Z-SNAPSHOT pattern
  raw_version=$(grep -oPm1 "(?<=version=).*-SNAPSHOT" gradle.properties)
fi

# Remove -SNAPSHOT suffix to get clean version number
current_version="${raw_version%-SNAPSHOT}"

# Validate that we successfully extracted a version
if [[ -z "$current_version" ]]; then
  echo "::error::Failed to extract the version from build file."
  exit 1
fi

# Calculate short version for current version (removes trailing .0)
current_short_version=$(get_short_version "$current_version")

# Output current version information
echo "Current version extracted from build file: $current_version (short: $current_short_version)"
echo "current-version=$current_version" >> "$GITHUB_OUTPUT"
echo "current-short-version=$current_short_version" >> "$GITHUB_OUTPUT"

# Determine next version based on input or auto-increment
if [[ -n "$INPUT_VERSION" ]]; then
  # Use explicitly provided version
  next_version="$INPUT_VERSION"
  echo "Using provided version as next version"
else
  # Auto-increment: bump minor version and reset patch to 0
  # Example: 1.2.3 -> 1.3.0
  next_version=$(echo "$current_version" | awk -F. -v OFS=. '{$2++; $3=0; print}')
  echo "Auto-incremented next version"
fi

# Calculate short version for next version (removes trailing .0)
next_short_version=$(get_short_version "$next_version")

# Output next version information and set GitHub Actions variables
echo "Next version will be $next_version (short: $next_short_version)"
echo "next-version=$next_version" >> "$GITHUB_OUTPUT"
echo "NEXT_VERSION=$next_version" >> "$GITHUB_ENV"
echo "next-short-version=$next_short_version" >> "$GITHUB_OUTPUT"

# Set snapshot version for development builds
# This will be used to update build files with the new development version
echo "SNAPSHOT_VERSION=${next_version}-SNAPSHOT" >> "$GITHUB_ENV"
