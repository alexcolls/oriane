#!/bin/bash

# ========================================================================
# Oriane Extraction Pipeline - Main Runner Script
# ========================================================================
# This script sources all required environment files, activates the virtual
# environment, and runs the main batch extraction pipeline.
#
# Usage:
#   ./run.sh [options]
#
# Options:
#   --verbose, -v        Enable verbose logging
#   --dry-run            Validate environment without running
#   --batch-size         Set custom batch size (default: 1000)
#   --json-checkpoint    Use JSON file for checkpoints
#   --db-checkpoint      Use database table for checkpoints
#   --help, -h           Show this help message
#
# Environment Files Loaded (in order):
#   1. .env (local extraction environment)
#   2. ../../../core/py/pipeline/.env (core pipeline environment)
#
# Virtual Environment (Local):
#   ./.venv (local to this directory)
# ========================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_ENV_FILE="${SCRIPT_DIR}/.env"
readonly PIPELINE_ENV_FILE="${SCRIPT_DIR}/../../core/py/pipeline/.env"
readonly VENV_DIR="${SCRIPT_DIR}/.venv"
readonly MAIN_SCRIPT="${SCRIPT_DIR}/main.py"

# Default options
VERBOSE=false
DRY_RUN=false
BATCH_SIZE=1000
MAX_WORKERS=8
CHECKPOINT_MODE="json"

# ========================================================================
# Helper Functions
# ========================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

show_help() {
    cat << EOF
${GREEN}Oriane Extraction Pipeline Runner${NC}

${YELLOW}USAGE:${NC}
    ./run.sh [OPTIONS]

${YELLOW}OPTIONS:${NC}
    -v, --verbose         Enable verbose logging
    --batch-size          Set custom batch size (default: 1000)
    --json-checkpoint     Use JSON file for checkpoints (default)
    --db-checkpoint       Use database table for checkpoints
    --dry-run             Validate environment and dependencies without running
    -h, --help            Show this help message

${YELLOW}DESCRIPTION:${NC}
    This script runs the Oriane video extraction pipeline with proper environment
    setup. It automatically sources environment files, activates the Python virtual
    environment, and starts the batch orchestrator.

${YELLOW}ENVIRONMENT FILES:${NC}
    1. ${ROOT_ENV_FILE}
    2. ${PIPELINE_ENV_FILE}

${YELLOW}VIRTUAL ENVIRONMENT:${NC}
    ${VENV_DIR}

${YELLOW}EXAMPLES:${NC}
    ./run.sh                     # Run the pipeline normally
    ./run.sh --verbose           # Run with verbose output
    ./run.sh --dry-run           # Validate setup without running
    ./run.sh --batch-size 500    # Run with 500 records per batch
    ./run.sh --db-checkpoint     # Use database checkpoint storage

${YELLOW}LOGS:${NC}
    Processing logs are written to: logs/extraction.log
    Use 'tail -f logs/extraction.log' to monitor progress.

EOF
}

# ========================================================================
# Environment Validation Functions
# ========================================================================

check_file_exists() {
    local file="$1"
    local description="$2"

    if [[ ! -f "$file" ]]; then
        log_error "$description not found: $file"
        return 1
    fi
    log_info "$description found: $file"
    return 0
}

check_directory_exists() {
    local dir="$1"
    local description="$2"

    if [[ ! -d "$dir" ]]; then
        log_error "$description not found: $dir"
        return 1
    fi
    log_info "$description found: $dir"
    return 0
}

validate_environment_files() {
    log_info "Validating environment files..."

    local errors=0

    if ! check_file_exists "$ROOT_ENV_FILE" "Local environment file"; then
        log_warning "Local .env file is missing - some features may not work"
        log_warning "Create it with: cp .env.sample .env"
        ((errors++))
    fi

    if ! check_file_exists "$PIPELINE_ENV_FILE" "Core pipeline environment file"; then
        log_error "Core pipeline .env file is missing - this is required"
        log_error "Check: ${PIPELINE_ENV_FILE}"
        ((errors++))
    fi

    return $errors
}

validate_virtual_environment() {
    log_info "Validating Python virtual environment..."

    if ! check_directory_exists "$VENV_DIR" "Python virtual environment"; then
        log_error "Virtual environment not found. Create it with:"
        log_error "  cd $(dirname $PIPELINE_ENV_FILE)"
        log_error "  python3 -m venv .venv"
        log_error "  source .venv/bin/activate"
        log_error "  pip install -r requirements.txt"
        return 1
    fi

    local activate_script="${VENV_DIR}/bin/activate"
    if ! check_file_exists "$activate_script" "Virtual environment activation script"; then
        log_error "Virtual environment appears corrupted. Please recreate it."
        return 1
    fi

    return 0
}

validate_main_script() {
    log_info "Validating main script..."

    if ! check_file_exists "$MAIN_SCRIPT" "Main pipeline script"; then
        return 1
    fi

    return 0
}

check_database_connection() {
    log_info "Testing database connection..."

    if [[ -z "${DB_HOST:-}" ]]; then
        log_warning "DB_HOST not set - database connection may fail"
        return 1
    fi

    log_info "Database host configured: ${DB_HOST}"
    return 0
}

# ========================================================================
# Environment Loading Functions
# ========================================================================

source_env_file() {
    local env_file="$1"
    local description="$2"

    log_info "Loading $description: $env_file"

    if [[ -f "$env_file" ]]; then
        set -a  # Export all variables
        source "$env_file"
        set +a  # Stop exporting
        log_info "Successfully loaded $description"
    else
        log_warning "$description not found: $env_file"
        return 1
    fi

    return 0
}

load_environment() {
    log_info "Loading environment configuration..."

    # Load local environment first (lower priority)
    source_env_file "$ROOT_ENV_FILE" "local environment"

    # Load core pipeline environment second (higher priority)
    source_env_file "$PIPELINE_ENV_FILE" "core pipeline environment"

    # Set checkpoint mode
    export CHECKPOINT_MODE="$CHECKPOINT_MODE"

    # Set batch size
    export BATCH_SIZE="$BATCH_SIZE"

    log_info "Environment configuration loaded successfully!"
}

validate_required_env_vars() {
    log_info "Validating required environment variables..."

    local required_vars=(
        "DB_HOST"
        "DB_NAME"
        "DB_USER"
        "DB_PASSWORD"
    )

    local missing_required=()

    # Check required variables
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_required+=("$var")
        else
            log_info "$var is configured"
        fi
    done

    # Report missing required variables
    if [[ ${#missing_required[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_required[*]}"
        log_error "Please set these in $ROOT_ENV_FILE or $PIPELINE_ENV_FILE"
        return 1
    fi

    return 0
}

# ========================================================================
# Pipeline Execution Functions
# ========================================================================

activate_virtual_environment() {
    log_info "Activating Python virtual environment..."

    local activate_script="${VENV_DIR}/bin/activate"

    # Source the activation script
    source "$activate_script"

    log_info "Virtual environment activated: $VIRTUAL_ENV"
    log_info "Python executable: $(which python)"
    log_info "Python version: $(python --version)"

    # Verify we're in the correct environment (normalize paths)
    local expected_venv="$(realpath "$VENV_DIR")"
    local actual_venv="$(realpath "$VIRTUAL_ENV")"
    if [[ "$actual_venv" != "$expected_venv" ]]; then
        log_error "Failed to activate virtual environment correctly"
        log_error "Expected: $expected_venv"
        log_error "Actual: $actual_venv"
        return 1
    fi

    return 0
}

run_pipeline() {
    log_info "Starting Oriane Extraction Pipeline..."
    log_info "Working directory: $(pwd)"
    log_info "Batch size: $BATCH_SIZE"
    log_info "Max workers: $MAX_WORKERS"
    log_info "Checkpoint mode: $CHECKPOINT_MODE"

    # Change to the script directory to ensure relative paths work correctly
    cd "$SCRIPT_DIR"

    # Set up signal handlers for graceful shutdown
    trap 'log_warning "Received interrupt signal. Pipeline may continue running..."; exit 130' INT TERM

    if [[ "$DRY_RUN" == true ]]; then
        log_success "Dry run completed - all validation checks passed!"
        log_info "Run without --dry-run to execute the pipeline"
        exit 0
    fi

    # Prepare arguments for the Python script
    local python_args=("--batch-size" "$BATCH_SIZE" "--max-workers" "$MAX_WORKERS")

    if [[ "$VERBOSE" == true ]]; then
        export LOG_LEVEL="DEBUG"
        log_info "Verbose mode enabled - setting LOG_LEVEL=DEBUG"
    fi

    if [[ "$CHECKPOINT_MODE" == "json" ]]; then
        python_args+=("--json-checkpoint")
    fi

    # Run the main pipeline script
    log_info "Executing: python $MAIN_SCRIPT ${python_args[*]}"
    python "$MAIN_SCRIPT" "${python_args[@]}"

    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        log_success "Pipeline completed successfully!"
    else
        log_error "Pipeline failed with exit code: $exit_code"
        log_error "Check logs/extraction.log for details"
    fi

    return $exit_code
}

# ========================================================================
# Main Function
# ========================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                VERBOSE=true
                log_info "Verbose mode enabled"
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                log_info "Dry run mode enabled"
                shift
                ;;
            --batch-size)
                BATCH_SIZE="$2"
                log_info "Batch size set to: $BATCH_SIZE"
                shift 2
                ;;
            --max-workers)
                MAX_WORKERS="$2"
                log_info "Max workers set to: $MAX_WORKERS"
                shift 2
                ;;
            --json-checkpoint)
                CHECKPOINT_MODE="json"
                log_info "Using JSON checkpoint storage"
                shift
                ;;
            --db-checkpoint)
                CHECKPOINT_MODE="database"
                log_info "Using database checkpoint storage"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                log_error "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

main() {
    echo -e "${GREEN}"
    echo "========================================================================"
    echo "            🚀 Oriane Video Extraction Pipeline Runner"
    echo "========================================================================"
    echo -e "${NC}"

    # Parse command line arguments
    parse_arguments "$@"

    local validation_errors=0

    # Step 1: Validate environment files
    if ! validate_environment_files; then
        ((validation_errors++))
    fi

    # Step 2: Validate virtual environment
    if ! validate_virtual_environment; then
        ((validation_errors++))
    fi

    # Step 3: Validate main script
    if ! validate_main_script; then
        ((validation_errors++))
    fi

    # Exit early if validation failed
    if [[ $validation_errors -gt 0 ]]; then
        log_error "Validation failed with $validation_errors error(s)"
        log_error "Please fix the issues above before running the pipeline"
        exit 1
    fi

    # Step 4: Load environment configuration
    load_environment

    # Step 5: Validate required environment variables
    if ! validate_required_env_vars; then
        log_error "Environment validation failed"
        exit 1
    fi

    # Step 6: Check database connection
    check_database_connection

    # Step 7: Activate virtual environment
    if ! activate_virtual_environment; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi

    log_success "Environment setup completed successfully!"

    # Step 8: Run the pipeline
    run_pipeline
    exit $?
}

# ========================================================================
# Script Entry Point
# ========================================================================

# Ensure we're running from the correct directory
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
