#!/bin/bash

# =============================================================================
# Project Setup Script
# =============================================================================
# This script initializes the project environment, creates virtual environment,
# installs dependencies, and sets up necessary configurations for the FastAPI
# pipeline service.
#
# Usage:
#   ./setup-project.sh
#
# Prerequisites:
#   - Python 3 and pip
#
# =============================================================================

set -e  # Exit on any error

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

# Check Python and pip installation
log_info "Checking Python and pip installation..."
if ! command -v python3 > /dev/null; then
    log_error "Python 3 not installed or not found in PATH. Please install it first."
    exit 1
fi

if ! command -v pip3 > /dev/null; then
    log_error "pip not installed or not found in PATH. Please install it first."
    exit 1
fi

log_info "Python and pip check passed"

# Create virtual environment
log_info "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    log_info "Virtual environment created successfully"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip

# Install project dependencies
log_info "Installing project dependencies..."
pip install -r requirements.txt

# Configuration setup check
log_info "Checking symbolic links for shared configurations..."
if [ ! -L "auth" ]; then
    ln -sf ../search/auth auth
    log_info "Created symbolic link for auth"
fi

if [ ! -L "config" ]; then
    ln -sf ../search/config config
    log_info "Created symbolic link for config"
fi

log_info "Project setup completed successfully"
log_info "You can now run the development server using './run-dev.sh'"

