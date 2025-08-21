#!/bin/bash

# This script updates rule metadata using the rule-api.jar file.
# It processes directories containing sonarpedia.json files, either specified by the user or discovered in the repository.

set -e  # Exit immediately if a command exits with a non-zero status

echo "" > rule-api-logs.txt

# Check if specific sonarpedia-files input is provided
if [ -n "${PROVIDED_SONARPEDIA_FILES}" ]; then
  echo "Using specified sonarpedia files: ${PROVIDED_SONARPEDIA_FILES}"

  # Convert comma-separated list to array and process each file
  IFS=',' read -ra SONARPEDIA_FILES <<< "${PROVIDED_SONARPEDIA_FILES}"
  sonarpedia_dirs=""

  for file in "${SONARPEDIA_FILES[@]}"; do
    # Trim whitespace
    file=$(echo "$file" | xargs)

    # Check if file exists
    if [ -f "$file" ]; then
      # Get directory containing the file
      dir=$(dirname "$file")
      sonarpedia_dirs="$sonarpedia_dirs$dir"$'\n'
    else
      echo "Warning: Specified sonarpedia file not found: $file"
    fi
  done

  # Remove empty lines and duplicates
  sonarpedia_dirs=$(echo "$sonarpedia_dirs" | grep -v '^$' | sort | uniq)
else
  echo "No specific files provided, discovering all sonarpedia.json files in repository"

  # Find all directories containing sonarpedia.json files
  sonarpedia_dirs=$(find . -name "sonarpedia.json" -type f | sed 's|/sonarpedia.json$||' | sort | uniq)
fi

if [ -z "$sonarpedia_dirs" ]; then
  echo "No sonarpedia.json files found to process"
  exit 1
fi

echo "Found sonarpedia.json files in the following directories:"
echo "$sonarpedia_dirs"
echo ""

# Store the original directory
original_dir=$(pwd)

# Loop through each directory containing sonarpedia.json
while IFS= read -r dir; do
  if [ -d "$dir" ]; then
    echo "Processing directory: $dir"
    cd "$dir"

    # Extract a meaningful name for logging (use last part of path)
    dir_name=$(basename "$dir")
    parent_dir=$(dirname "$dir")
    if [ "$parent_dir" != "." ]; then
      dir_name="${parent_dir##*/}/${dir_name}"
    fi

    echo "=== $dir_name ===" >> "$original_dir/rule-api-logs.txt"

    # Calculate relative path to rule-api.jar from current directory
    rel_path=$(realpath --relative-to="$PWD" "$original_dir/rule-api.jar")

    # Run rule-api update in the current directory
    java -jar "$rel_path" update 2>&1 | tee -a "$original_dir/rule-api-logs.txt"

    # Return to the original directory
    cd "$original_dir"
  fi
done <<< "$sonarpedia_dirs"
