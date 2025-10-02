#!/bin/bash

# =============================================================================
# 🚀 Oriane API Server Runner
# =============================================================================
# Runs tests and starts the FastAPI server
# Usage:
#   ./run.sh           - Run tests then start server
#   ./run.sh --skip-tests - Start server without running tests
# =============================================================================

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Get the script directory and project root
SCRIPT_DIR="$(dirname "$(realpath "$0")")" 
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root directory
cd "$PROJECT_ROOT"

# Activate the virtual environment
print_info "Activating virtual environment..."
source "$PROJECT_ROOT/.venv/bin/activate"
print_success "Virtual environment activated"

# Check if we should skip tests
if [[ "$1" == "--skip-tests" ]]; then
    print_warning "Skipping tests as requested"
else
    print_info "Running test suite..."
    "$SCRIPT_DIR/run-tests.sh"

    # Check if tests passed
    if [[ $? -ne 0 ]]; then
        echo
        print_warning "Tests failed! Starting server anyway..."
        print_warning "Consider fixing failing tests before deployment."
    else
        print_success "All tests passed! 🎉"
    fi
fi

echo
print_info "Starting FastAPI server..."
print_info "Server will be available at: http://localhost:8000"
print_info "API documentation: http://localhost:8000/api/docs"
print_info "Press Ctrl+C to stop the server"
echo

# Start the FastAPI server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
