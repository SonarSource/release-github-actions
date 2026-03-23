#!/usr/bin/env bash
# Generate the rule-update summary markdown table from rule-api-logs.txt.
# Usage: generate-summary.sh <rule-api-version> [log-file]
#   rule-api-version  Version string appended at the end of the summary.
#   log-file          Path to the log file (default: rule-api-logs.txt).
#
# Reads the log file, builds a markdown table with one row per sonarpedia
# directory, and writes the result to GITHUB_OUTPUT (summary=...).
# Exits 0 in all cases; sets summary to "Update rule metadata" when there
# are no rules to report.

set -euo pipefail

rule_api_version="${1:-}"
log_file="${2:-rule-api-logs.txt}"

summary_file="rule-api-summary.md"
current_sonarpedia=""
current_dir=""
has_entries=false
total_rules=0
total_updated=0

echo "| Sonarpedia | Rules to update | Rules updated |" > "$summary_file"
echo "|---|---:|---:|" >> "$summary_file"

while IFS= read -r line; do
  if [[ $line == "=== PATH:"* ]]; then
    current_dir=$(echo "$line" | sed 's/=== PATH:\(.*\) ===/\1/')
    current_sonarpedia="${current_dir}/sonarpedia.json"
  elif [[ $line == *"Found "* && $line == *" rule(s) to update"* ]]; then
    rule_count=$(echo "$line" | grep -oE 'Found [0-9]+' | grep -oE '[0-9]+')
    if [[ -n "$rule_count" && "$rule_count" != "0" && -n "$current_sonarpedia" ]]; then
      # Count rule files actually changed under this sonarpedia directory.
      # Rule files are .html and .json files (excluding sonarpedia.json itself).
      changed_files=$(git diff --name-only HEAD -- "${current_dir}" \
        | grep -v 'sonarpedia\.json$' || true)
      updated_count=$(echo "$changed_files" | grep -cE '\.(html|json)$' || true)
      echo "| \`${current_sonarpedia}\` | ${rule_count} | ${updated_count} |" >> "$summary_file"
      total_rules=$((total_rules + rule_count))
      total_updated=$((total_updated + updated_count))
      has_entries=true
    fi
  fi
done < "$log_file"

if [[ "$has_entries" == "true" ]]; then
  echo "| **Total** | **${total_rules}** | **${total_updated}** |" >> "$summary_file"
fi

if [[ -n "$rule_api_version" ]]; then
  echo -e "\nRule API Version: ${rule_api_version}" >> "$summary_file"
fi

if [[ "$has_entries" == "false" ]]; then
  echo "summary=Update rule metadata" >> "${GITHUB_OUTPUT:-/dev/null}"
else
  {
    echo "summary<<EOF"
    cat "$summary_file"
    echo "EOF"
  } >> "${GITHUB_OUTPUT:-/dev/null}"
fi

rm -f "$log_file" "$summary_file"