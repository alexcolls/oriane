#!/usr/bin/env bash
set -euo pipefail

# Absolute working dir
TEST_DIR="./"
cd "$TEST_DIR"

# Export env vars
export $(grep -v '^#' "$TEST_DIR/.env" | xargs)

# Install deps if missing
python3 -m pip install --quiet python-dotenv requests

# Run the test
python3 "$TEST_DIR/test_script.py"
