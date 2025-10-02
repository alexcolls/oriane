#!/bin/bash

# ========================================================================
# Oriane Extraction Pipeline - Initialization Script
# ========================================================================
# This script sets up the virtual environment and dependencies for the
# extraction pipeline.
#
# Usage:
#   ./init.sh [options]
#
# Options:
#   --help, -h           Show this help message
#   --verbose, -v        Enable verbose logging
#   --force              Force reinstallation of dependencies
# ========================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Absolute path variables
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly VENV_DIR="$SCRIPT_DIR/.venv"
readonly LOCAL_REQ="$SCRIPT_DIR/requirements.txt"
readonly CORE_REQ="$SCRIPT_DIR/../../../core/py/pipeline/requirements.txt"

# ========================================================================
# Helper Functions
# ========================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

show_help() {
    cat << EOF
${GREEN}Oriane Extraction Pipeline Initialization${NC}

${YELLOW}USAGE:${NC}
    ./init.sh [OPTIONS]

${YELLOW}OPTIONS:${NC}
    -v, --verbose         Enable verbose logging
    --force              Force reinstallation of dependencies
    -h, --help           Show this help message

${YELLOW}DESCRIPTION:${NC}
    This script initializes the Python virtual environment and installs
    all required dependencies for the extraction pipeline.

${YELLOW}ENVIRONMENT:${NC}
    Script Directory: ${SCRIPT_DIR}
    Virtual Environment: ${VENV_DIR}
    Local Requirements: ${LOCAL_REQ}
    Core Requirements: ${CORE_REQ}

${YELLOW}EXAMPLES:${NC}
    ./init.sh                    # Initialize the environment
    ./init.sh --verbose          # Initialize with verbose output
    ./init.sh --force            # Force reinstallation of dependencies

EOF
}

# ========================================================================
# Main Function (placeholder)
# ========================================================================

main() {
    echo -e "${GREEN}"
    echo "========================================================================"
    echo "            🛠️  Oriane Extraction Pipeline Initialization"
    echo "========================================================================"
    echo -e "${NC}"

    log_info "Script directory: $SCRIPT_DIR"
    log_info "Virtual environment: $VENV_DIR"
    log_info "Local requirements: $LOCAL_REQ"
    log_info "Core requirements: $CORE_REQ"

    # TODO: Add initialization logic here
    log_info "Initialization script skeleton created successfully!"
}

# ========================================================================
# Script Entry Point
# ========================================================================

# Ensure we're running from the correct directory
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
