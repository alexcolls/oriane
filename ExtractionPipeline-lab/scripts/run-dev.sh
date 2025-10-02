#!/bin/bash

# =============================================================================
# Development Environment Runner
# =============================================================================
# This script sets up and runs the FastAPI pipeline service in development mode.
# It handles virtual environment activation, dependency installation, and 
# starts the development server with hot-reloading enabled.
#
# Usage:
#   ./run-dev.sh [OPTIONS]
#
# Options:
#   -h, --help       Show this help message
#   -p, --port PORT  Specify port (default: 8000)
#   -r, --reload     Enable auto-reload (default: true)
#   --no-reload      Disable auto-reload
#   -v, --verbose    Verbose output
#   --check-deps     Check and install dependencies
#
# Environment Variables:
#   API_PORT         Port to run the server on (default: 8000)
#   API_HOST         Host to bind to (default: 0.0.0.0)
#   LOG_LEVEL        Log level (default: info)
#
# =============================================================================

set -e  # Exit on any error

# Default configuration
DEFAULT_PORT=8000
DEFAULT_HOST="0.0.0.0"
DEFAULT_LOG_LEVEL="info"
RELOAD_ENABLED=true
VERBOSE=false
CHECK_DEPS=false

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Help function
show_help() {
    cat << EOF
Development Environment Runner for Pipeline API

Usage: $0 [OPTIONS]

Options:
    -h, --help       Show this help message
    -p, --port PORT  Specify port (default: $DEFAULT_PORT)
    -r, --reload     Enable auto-reload (default: enabled)
    --no-reload      Disable auto-reload
    -v, --verbose    Verbose output
    --check-deps     Check and install dependencies

Environment Variables:
    API_PORT         Port to run the server on (default: $DEFAULT_PORT)
    API_HOST         Host to bind to (default: $DEFAULT_HOST)
    LOG_LEVEL        Log level (default: $DEFAULT_LOG_LEVEL)

Examples:
    $0                          # Run with default settings
    $0 -p 8080                  # Run on port 8080
    $0 --no-reload              # Run without auto-reload
    $0 -v --check-deps          # Verbose mode with dependency check

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--port)
            if [[ -n $2 && $2 != -* ]]; then
                DEFAULT_PORT=$2
                shift 2
            else
                log_error "Port value is required"
                exit 1
            fi
            ;;
        -r|--reload)
            RELOAD_ENABLED=true
            shift
            ;;
        --no-reload)
            RELOAD_ENABLED=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --check-deps)
            CHECK_DEPS=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set configuration from environment variables or defaults
PORT=${API_PORT:-$DEFAULT_PORT}
HOST=${API_HOST:-$DEFAULT_HOST}
LOG_LEVEL=${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}

# Check if we're in the correct directory
if [ ! -f "main.py" ]; then
    log_error "main.py not found. Please run this script from the pipeline API directory."
    exit 1
fi

log_info "Starting Pipeline API Development Environment"
log_debug "Configuration:"
log_debug "  Port: $PORT"
log_debug "  Host: $HOST"
log_debug "  Log Level: $LOG_LEVEL"
log_debug "  Reload: $RELOAD_ENABLED"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    log_warn "Virtual environment not found. Creating..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        log_error "Failed to create virtual environment"
        exit 1
    fi
    log_info "Virtual environment created successfully"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source .venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
log_debug "Python version: $PYTHON_VERSION"

# Install/check dependencies
if [ "$CHECK_DEPS" = true ] || [ ! -f ".venv/pyvenv.cfg" ]; then
    log_info "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        log_error "Failed to install dependencies"
        exit 1
    fi
    log_info "Dependencies installed successfully"
fi

# Verify critical imports
log_info "Verifying imports..."
python3 -c "
try:
    from main import app
    from auth.apikey import verify_api_key
    from config.env_config import settings
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    log_error "Import verification failed"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    log_warn ".env file not found. Some configuration may be missing."
fi

# Check if symbolic links exist
if [ ! -L "auth" ] || [ ! -L "config" ]; then
    log_warn "Symbolic links for auth/config may be missing"
    log_info "Creating symbolic links..."
    ln -sf ../search/auth auth 2>/dev/null || true
    ln -sf ../search/config config 2>/dev/null || true
fi

# Build uvicorn command
UVICORN_CMD="uvicorn main:app --host $HOST --port $PORT --log-level $LOG_LEVEL"

if [ "$RELOAD_ENABLED" = true ]; then
    UVICORN_CMD="$UVICORN_CMD --reload"
fi

log_info "Starting FastAPI server..."
log_info "Server will be available at: http://$HOST:$PORT"
log_info "API documentation: http://$HOST:$PORT/docs"
log_info "Health check: http://$HOST:$PORT/health"

# Set up signal handlers for graceful shutdown
trap 'log_info "Shutting down server..."; exit 0' SIGINT SIGTERM

# Start the server
log_debug "Executing: $UVICORN_CMD"
exec $UVICORN_CMD
