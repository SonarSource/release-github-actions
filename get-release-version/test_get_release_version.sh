#!/bin/bash
# -*- coding: utf-8 -*-

# Test script for get-release-version GitHub Action

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Mock gh command function
mock_gh_success() {
    # shellcheck disable=SC2317
    if [[ "$*" == *"commits/master/status"* ]]; then
        echo "1.2.3"
    else
        echo "Unexpected gh command: $*" >&2
        return 1
    fi
}

mock_gh_empty_response() {
    # shellcheck disable=SC2317
    if [[ "$*" == *"commits/master/status"* ]]; then
        echo ""
    else
        echo "Unexpected gh command: $*" >&2
        return 1
    fi
}

# Test helper functions
print_test_start() {
    echo -e "${YELLOW}Testing: $1${NC}"
}

print_test_pass() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

print_test_fail() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    echo -e "${RED}   Expected: $2${NC}"
    echo -e "${RED}   Got: $3${NC}"
    ((TESTS_FAILED++))
}

# Test function to simulate the action's logic
test_get_release_version() {
    local test_name="$1"
    local expected_result="$2"
    local gh_mock_function="$3"
    
    print_test_start "$test_name"
    
    # Set up test environment
    export GITHUB_REPOSITORY="owner/repo"
    export GITHUB_OUTPUT="/tmp/github_output_test"
    export GITHUB_ENV="/tmp/github_env_test"
    
    # Clear output files
    echo "" > "$GITHUB_OUTPUT"
    echo "" > "$GITHUB_ENV"
    
    # Mock the gh command
    eval "gh() { $gh_mock_function \"\$@\"; }"
    
    # Simulate the action's logic
    local exit_code=0
    local release_version=""
    
    # Execute the main logic from the action
    if release_version=$(gh api "/repos/${GITHUB_REPOSITORY}/commits/master/status" --jq ".statuses[] | select(.context == \"repox-master\") | .description | split(\"'\")[1]" 2>/dev/null); then
        if [ -z "$release_version" ]; then
            echo "❌ Could not extract release version from repox-master status"
            exit_code=1
        else
            echo "✅ Extracted release version: $release_version"
            echo "release-version=$release_version" >> "$GITHUB_OUTPUT"
            echo "RELEASE_VERSION=$release_version" >> "$GITHUB_ENV"
        fi
    else
        echo "❌ Failed to call GitHub API"
        exit_code=1
    fi
    
    # Verify results
    if [ "$expected_result" = "success" ]; then
        if [ $exit_code -eq 0 ] && [ -n "$release_version" ]; then
            # Check if output files contain expected content
            if grep -q "release-version=" "$GITHUB_OUTPUT" && grep -q "RELEASE_VERSION=" "$GITHUB_ENV"; then
                print_test_pass "$test_name"
            else
                print_test_fail "$test_name" "Output and env files to contain release version" "Missing content in files"
            fi
        else
            print_test_fail "$test_name" "Successful execution with release version" "Exit code: $exit_code, Version: '$release_version'"
        fi
    else
        if [ $exit_code -ne 0 ]; then
            print_test_pass "$test_name"
        else
            print_test_fail "$test_name" "Non-zero exit code" "Exit code: $exit_code"
        fi
    fi
    
    # Cleanup
    rm -f "$GITHUB_OUTPUT" "$GITHUB_ENV"
}

# Run tests
echo "=== Running Get Release Version Action Tests ==="
echo

test_get_release_version "Successful version extraction" "success" "mock_gh_success"
test_get_release_version "Empty response handling" "failure" "mock_gh_empty_response"

echo
echo "=== Test Results ==="
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed!${NC}"
    exit 1
fi
