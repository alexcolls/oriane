#!/bin/bash

# Script: 01_clone_repo.sh
# Purpose: Clone a repository and create a baseline snapshot for reproducible analysis
# Usage: ./01_clone_repo.sh <REPO_URL> <TARGET_DIR>

set -e  # Exit on any error

# Check if correct number of arguments provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <REPO_URL> <TARGET_DIR>"
    echo "  REPO_URL: URL of the repository to clone"
    echo "  TARGET_DIR: Absolute path where repository will be cloned"
    exit 1
fi

REPO_URL="$1"
TARGET_DIR="$2"

# Validate that TARGET_DIR is an absolute path
if [[ ! "$TARGET_DIR" = /* ]]; then
    echo "Error: TARGET_DIR must be an absolute path (starting with /)"
    exit 1
fi

# Create parent directory if it doesn't exist
PARENT_DIR="$(dirname "$TARGET_DIR")"
if [ ! -d "$PARENT_DIR" ]; then
    echo "Creating parent directory: $PARENT_DIR"
    mkdir -p "$PARENT_DIR"
fi

# Remove target directory if it already exists
if [ -d "$TARGET_DIR" ]; then
    echo "Warning: Target directory already exists. Removing: $TARGET_DIR"
    rm -rf "$TARGET_DIR"
fi

echo "Cloning repository from: $REPO_URL"
echo "Target directory: $TARGET_DIR"

# Perform shallow clone
git clone --depth=1 "$REPO_URL" "$TARGET_DIR"

# Change to the cloned repository directory
cd "$TARGET_DIR"

# Record baseline information
echo "Recording baseline information..."
BASELINE_FILE="$TARGET_DIR/baseline_info.txt"

# Get commit hash
COMMIT_HASH=$(git rev-parse HEAD)

# Get current branch name
BRANCH_NAME=$(git branch --show-current)

# Get timestamp
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

# Write baseline information to file
cat > "$BASELINE_FILE" << EOF
Repository Baseline Information
===============================
Repository URL: $REPO_URL
Clone Directory: $TARGET_DIR
Commit Hash: $COMMIT_HASH
Branch: $BRANCH_NAME
Timestamp: $TIMESTAMP
Clone Type: Shallow (--depth=1)

EOF

echo "Baseline information recorded in: $BASELINE_FILE"

# Generate tree listing
echo "Generating directory structure..."
if command -v tree >/dev/null 2>&1; then
    echo "Directory Structure (top 3 levels):" >> "$BASELINE_FILE"
    echo "====================================" >> "$BASELINE_FILE"
    tree -L 3 >> "$BASELINE_FILE"
else
    echo "Warning: 'tree' command not found. Using 'find' as fallback."
    echo "Directory Structure (top 3 levels):" >> "$BASELINE_FILE"
    echo "====================================" >> "$BASELINE_FILE"
    find . -maxdepth 3 -type d | sort >> "$BASELINE_FILE"
fi

echo ""
echo "Repository cloning and baseline snapshot completed successfully!"
echo "Location: $TARGET_DIR"
echo "Baseline info: $BASELINE_FILE"
echo ""
echo "Summary:"
echo "- Repository: $REPO_URL"
echo "- Commit: $COMMIT_HASH"
echo "- Branch: $BRANCH_NAME"
echo "- Cloned at: $TIMESTAMP"
