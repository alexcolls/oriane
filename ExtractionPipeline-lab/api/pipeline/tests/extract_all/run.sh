#!/bin/bash
# Extract All Pipeline Runner
# Simple runner script for the extraction pipeline test suite

set -euo pipefail

# Change to script directory
cd "$(dirname "$0")"

# Export environment variables if needed
export PYTHONPATH="${PYTHONPATH:-}:."

# Run the main Python script with all arguments passed through
python3 main.py "$@"
