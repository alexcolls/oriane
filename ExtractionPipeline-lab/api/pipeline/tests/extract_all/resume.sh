#!/bin/bash
# Resume Extract All Pipeline
# Simple resume script for the extraction pipeline test suite

set -euo pipefail

# Change to script directory
cd "$(dirname "$0")"

# Export environment variables if needed
export PYTHONPATH="${PYTHONPATH:-}:."

# Run the main Python script with --resume flag and all arguments passed through
python3 main.py --resume "$@"
