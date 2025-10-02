#!/bin/bash

# =============================================================================
# Test Runner and Logger
# =============================================================================
# This script runs the test suite for the FastAPI pipeline service, logs the
# results, and provides an option for verbose output.
#
# Usage:
#   ./run-tests.sh [OPTIONS]
#
# Options:
#   -h, --help        Show this help message
#   -v, --verbose     Verbose output
#   -l, --log LOGFILE Specify log file (default: test_results.log)
#   --fail-fast       Stop on first test failure
#
# =============================================================================

set -e  # Exit on any error

# Default configuration
LOGFILE="test_results.log"
VERBOSE=false
FAIL_FAST=false

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Test Runner and Logger for Pipeline API

Usage: $0 [OPTIONS]

Options:
    -h, --help        Show this help message
    -v, --verbose     Verbose output
    -l, --log LOGFILE Specify log file (default: $LOGFILE)
    --fail-fast       Stop on first test failure

Examples:
    $0 -v                          # Run with verbose output
    $0 --log "my_test_log.log"    # Log results to a custom file
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -l|--log)
            if [[ -n $2 && $2 != -* ]]; then
                LOGFILE=$2
                shift 2
            else
                log_error "Logfile name is required"
                exit 1
            fi
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    log_error "Virtual environment not found. Please run 'run-dev.sh' to set up the development environment."
    exit 1
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source .venv/bin/activate

# Run the test suite
log_info "Running tests..."
python3 -u test_implementation.py 2>&1 | tee $LOGFILE

# Check for test failures if fail-fast is enabled
if [ $? -ne 0 ] && [ "$FAIL_FAST" = true ]; then
    log_error "Test failed. Exiting due to fail-fast policy."
    exit 1
fi

log_info "Test results logged to: $LOGFILE"



