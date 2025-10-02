#!/bin/bash
# WARNING: This script should be run from the `api` directory.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
VENV_DIR=".venv"
# Use python3.12 if available, otherwise fall back.
PYTHON_CMD="python3.12"
CORE_REQS_PATH="../core/py/pipeline/requirements.txt"
API_REQS_PATH="requirements.txt"

# --- Helper functions for cleaner output ---
info() {
    echo "🚀 [INFO] $1"
}

success() {
    echo "✅ [SUCCESS] $1"
}

warn() {
    echo "⚠️  [WARNING] $1"
}

# --- 1. Virtual Environment Setup ---
info "Checking for virtual environment in '$VENV_DIR'..."
if [ ! -d "$VENV_DIR" ]; then
    info "No virtual environment found. Creating one..."
    # Check if the specified python command exists
    if ! command -v $PYTHON_CMD &> /dev/null; then
        warn "Python command '$PYTHON_CMD' not found. Trying 'python3' as a fallback."
        PYTHON_CMD="python3"
        if ! command -v $PYTHON_CMD &> /dev/null; then
            echo "❌ [ERROR] python3 is not installed or not in your PATH. Please install it."
            exit 1
        fi
    fi
    $PYTHON_CMD -m venv "$VENV_DIR"
    success "Virtual environment created."
else
    success "Virtual environment already exists."
fi

# --- 2. Activate Virtual Environment ---
info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
success "Virtual environment activated."

# --- 3. Install/Update Dependencies ---
info "Installing/updating Python packages (this might take a moment)..."
# Upgrade pip first for better dependency resolution
pip install --upgrade pip > /dev/null 2>&1
# Install dependencies from both files, redirecting output for a cleaner console
pip install -r "$CORE_REQS_PATH" -r "$API_REQS_PATH" > /dev/null 2>&1
success "All dependencies are installed and up to date."
