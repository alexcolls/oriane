#!/bin/bash

# 03_build_run_story.sh
# Build and run validation script for the extraction pipeline
# This script implements Step 3 of the broader plan to reproduce build and run paths

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${PROJECT_ROOT}/build_run_report.md"
LOGS_DIR="${PROJECT_ROOT}/build_logs"

# Create logs directory
mkdir -p "$LOGS_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOGS_DIR/build_run_${TIMESTAMP}.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOGS_DIR/build_run_${TIMESTAMP}.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOGS_DIR/build_run_${TIMESTAMP}.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOGS_DIR/build_run_${TIMESTAMP}.log"
}

# Initialize report
init_report() {
    cat > "$REPORT_FILE" << EOF
# Build and Run Report
Generated: $(date)

## Executive Summary
This report captures the results of building and running the extraction pipeline components.

## Test Results Summary

EOF
}

# Function to record test results
record_test_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    {
        echo "### $test_name"
        echo "**Status:** $status"
        echo "**Details:** $details"
        echo "**Timestamp:** $(date)"
        echo ""
    } >> "$REPORT_FILE"
}

# Function to capture pip freeze diff
capture_pip_diff() {
    local component="$1"
    local venv_path="$2"
    
    log_info "Capturing pip freeze for $component"
    
    # Before install
    local before_file="$LOGS_DIR/${component}_pip_before_${TIMESTAMP}.txt"
    local after_file="$LOGS_DIR/${component}_pip_after_${TIMESTAMP}.txt"
    local diff_file="$LOGS_DIR/${component}_pip_diff_${TIMESTAMP}.txt"
    
    # Create empty before file since we're creating fresh venv
    touch "$before_file"
    
    # After install
    if [ -f "$venv_path/bin/python3" ]; then
        "$venv_path/bin/python3" -m pip freeze > "$after_file" 2>/dev/null || true
    fi
    
    # Generate diff
    if [ -f "$after_file" ]; then
        diff "$before_file" "$after_file" > "$diff_file" 2>/dev/null || true
        log_success "Pip freeze diff captured for $component: $diff_file"
    else
        log_warning "Could not capture pip freeze for $component"
    fi
}

# Function to create Python venv and install dependencies
setup_python_venv() {
    local component="$1"
    local path="$2"
    local requirements_file="$3"
    
    log_info "Setting up Python venv for $component at $path"
    
    # Create venv
    if [ ! -d "$path" ]; then
        log_info "Creating directory: $path"
        mkdir -p "$(dirname "$path")"
    fi
    
    cd "$(dirname "$path")"
    local venv_name=$(basename "$path")
    
    # Remove existing venv if it exists
    if [ -d "$venv_name" ]; then
        log_info "Removing existing venv: $venv_name"
        rm -rf "$venv_name"
    fi
    
    # Create new venv
    python3 -m venv "$venv_name" || {
        log_error "Failed to create venv for $component"
        record_test_result "$component Python venv creation" "❌ FAILED" "Could not create virtual environment"
        return 1
    }
    
    # Activate and install
    source "$venv_name/bin/activate"
    
    # Upgrade pip
    python3 -m pip install --upgrade pip || {
        log_warning "Failed to upgrade pip for $component"
    }
    
    # Install requirements if file exists
    if [ -f "$requirements_file" ]; then
        log_info "Installing requirements from: $requirements_file"
        python3 -m pip install -r "$requirements_file" || {
            log_error "Failed to install requirements for $component"
            record_test_result "$component Dependencies Installation" "❌ FAILED" "Could not install requirements from $requirements_file"
            deactivate
            return 1
        }
    else
        log_warning "Requirements file not found: $requirements_file"
    fi
    
    # Capture pip freeze after install
    capture_pip_diff "$component" "$PWD/$venv_name"
    
    deactivate
    record_test_result "$component Python venv setup" "✅ SUCCESS" "Virtual environment created and dependencies installed"
    log_success "Python venv setup complete for $component"
}

# Function to build C++ binaries
build_cpp_binaries() {
    log_info "Building C++ binaries"
    
    local cpp_dir="$PROJECT_ROOT/core/cpp"
    local build_log="$LOGS_DIR/cpp_build_${TIMESTAMP}.log"
    local compile_times_log="$LOGS_DIR/cpp_compile_times_${TIMESTAMP}.log"
    
    if [ ! -d "$cpp_dir" ]; then
        log_warning "C++ directory not found: $cpp_dir"
        record_test_result "C++ Binary Build" "⚠️ SKIPPED" "C++ directory not found"
        return 0
    fi
    
    cd "$cpp_dir"
    
    # Find C++ projects
    local projects=($(find . -name "CMakeLists.txt" -exec dirname {} \; | sort -u))
    
    if [ ${#projects[@]} -eq 0 ]; then
        log_warning "No C++ projects found with CMakeLists.txt"
        record_test_result "C++ Binary Build" "⚠️ SKIPPED" "No CMakeLists.txt files found"
        return 0
    fi
    
    local build_success=true
    
    for project in "${projects[@]}"; do
        log_info "Building C++ project: $project"
        
        cd "$cpp_dir/$project"
        local project_name=$(basename "$project")
        
        # Record compile start time
        local start_time=$(date +%s)
        echo "[$project_name] Build started at $(date)" >> "$compile_times_log"
        
        # Create build directory
        mkdir -p build
        cd build
        
        # Configure with absolute paths
        if ! cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PWD/install" .. >> "$build_log" 2>&1; then
            log_error "CMake configuration failed for $project"
            build_success=false
            continue
        fi
        
        # Build
        if ! make -j$(nproc) >> "$build_log" 2>&1; then
            log_error "Build failed for $project"
            build_success=false
            continue
        fi
        
        # Record compile time
        local end_time=$(date +%s)
        local compile_time=$((end_time - start_time))
        echo "[$project_name] Build completed in ${compile_time}s at $(date)" >> "$compile_times_log"
        
        log_success "Built C++ project: $project (${compile_time}s)"
    done
    
    if [ "$build_success" = true ]; then
        record_test_result "C++ Binary Build" "✅ SUCCESS" "All C++ projects built successfully. See $compile_times_log for timing details."
    else
        record_test_result "C++ Binary Build" "❌ FAILED" "Some C++ projects failed to build. See $build_log for details."
    fi
    
    cd "$PROJECT_ROOT"
}

# Function to start Docker Compose and capture logs
start_docker_compose() {
    log_info "Starting Docker Compose services"
    
    local compose_file="$PROJECT_ROOT/qdrant/deploy/docker-compose.yml"
    local docker_log="$LOGS_DIR/docker_compose_${TIMESTAMP}.log"
    
    if [ ! -f "$compose_file" ]; then
        log_warning "Docker Compose file not found: $compose_file"
        record_test_result "Docker Compose Startup" "⚠️ SKIPPED" "docker-compose.yml not found"
        return 0
    fi
    
    cd "$(dirname "$compose_file")"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found, skipping Docker Compose"
        record_test_result "Docker Compose Startup" "⚠️ SKIPPED" "Docker not available"
        return 0
    fi
    
    # Stop any existing services
    docker-compose -f "$compose_file" down >> "$docker_log" 2>&1 || true
    
    # Start services in detached mode
    if docker-compose -f "$compose_file" up -d >> "$docker_log" 2>&1; then
        log_success "Docker Compose services started"
        
        # Wait a bit for services to initialize
        sleep 10
        
        # Capture container logs
        docker-compose -f "$compose_file" logs >> "$docker_log" 2>&1 || true
        
        record_test_result "Docker Compose Startup" "✅ SUCCESS" "Services started successfully. Logs captured in $docker_log"
    else
        log_error "Failed to start Docker Compose services"
        record_test_result "Docker Compose Startup" "❌ FAILED" "Could not start Docker Compose services. See $docker_log for details."
    fi
    
    cd "$PROJECT_ROOT"
}

# Function to validate make targets
validate_make_targets() {
    log_info "Validating make targets"
    
    cd "$PROJECT_ROOT"
    
    # Test make extract
    log_info "Testing 'make extract'"
    if timeout 30 make extract > "$LOGS_DIR/make_extract_${TIMESTAMP}.log" 2>&1; then
        record_test_result "make extract" "✅ SUCCESS" "Command executed successfully"
        log_success "make extract completed successfully"
    else
        record_test_result "make extract" "❌ FAILED" "Command failed or timed out. See $LOGS_DIR/make_extract_${TIMESTAMP}.log"
        log_error "make extract failed"
    fi
    
    # Test make test
    log_info "Testing 'make test'"
    if timeout 60 make test > "$LOGS_DIR/make_test_${TIMESTAMP}.log" 2>&1; then
        record_test_result "make test" "✅ SUCCESS" "Command executed successfully"
        log_success "make test completed successfully"
    else
        record_test_result "make test" "❌ FAILED" "Command failed or timed out. See $LOGS_DIR/make_test_${TIMESTAMP}.log"
        log_error "make test failed"
    fi
}

# Function to validate entrypoint.py help
validate_entrypoint_help() {
    log_info "Validating core/py/pipeline/entrypoint.py --help"
    
    local entrypoint="$PROJECT_ROOT/core/py/pipeline/entrypoint.py"
    local venv_path="$PROJECT_ROOT/core/py/pipeline/.venv"
    
    if [ ! -f "$entrypoint" ]; then
        log_warning "Entrypoint not found: $entrypoint"
        record_test_result "entrypoint.py --help" "⚠️ SKIPPED" "entrypoint.py not found"
        return 0
    fi
    
    if [ ! -d "$venv_path" ]; then
        log_warning "Virtual environment not found for entrypoint test"
        record_test_result "entrypoint.py --help" "⚠️ SKIPPED" "Virtual environment not available"
        return 0
    fi
    
    cd "$(dirname "$entrypoint")"
    
    # Activate venv and test help
    source "$venv_path/bin/activate"
    
    if python3 entrypoint.py --help > "$LOGS_DIR/entrypoint_help_${TIMESTAMP}.log" 2>&1; then
        record_test_result "entrypoint.py --help" "✅ SUCCESS" "Help command executed successfully"
        log_success "entrypoint.py --help completed successfully"
    else
        record_test_result "entrypoint.py --help" "❌ FAILED" "Help command failed. See $LOGS_DIR/entrypoint_help_${TIMESTAMP}.log"
        log_error "entrypoint.py --help failed"
    fi
    
    deactivate
    cd "$PROJECT_ROOT"
}

# Function to cleanup Docker services
cleanup_docker() {
    log_info "Cleaning up Docker services"
    
    local compose_file="$PROJECT_ROOT/qdrant/deploy/docker-compose.yml"
    
    if [ -f "$compose_file" ] && command -v docker &> /dev/null; then
        cd "$(dirname "$compose_file")"
        docker-compose -f "$compose_file" down >> "$LOGS_DIR/docker_cleanup_${TIMESTAMP}.log" 2>&1 || true
        cd "$PROJECT_ROOT"
        log_success "Docker services cleaned up"
    fi
}

# Function to finalize report
finalize_report() {
    {
        echo "## Build Logs"
        echo "All build logs are stored in: \`$LOGS_DIR\`"
        echo ""
        echo "## Generated Files"
        echo "- Build log: \`$LOGS_DIR/build_run_${TIMESTAMP}.log\`"
        echo "- C++ build log: \`$LOGS_DIR/cpp_build_${TIMESTAMP}.log\`"
        echo "- C++ compile times: \`$LOGS_DIR/cpp_compile_times_${TIMESTAMP}.log\`"
        echo "- Docker logs: \`$LOGS_DIR/docker_compose_${TIMESTAMP}.log\`"
        echo ""
        echo "## Summary"
        echo "Build and run validation completed at $(date)"
        echo ""
    } >> "$REPORT_FILE"
    
    log_success "Report finalized: $REPORT_FILE"
}

# Main execution
main() {
    log_info "Starting build and run validation (Step 3)"
    log_info "Project root: $PROJECT_ROOT"
    log_info "Logs directory: $LOGS_DIR"
    
    # Initialize report
    init_report
    
    # Trap to ensure cleanup on exit
    trap cleanup_docker EXIT
    
    # 1. Create isolated Python venvs and capture pip freeze diffs
    log_info "=== Phase 1: Setting up Python environments ==="
    
    # API venv
    setup_python_venv "api" "$PROJECT_ROOT/api/.venv" "$PROJECT_ROOT/api/pipeline/config/requirements.txt"
    
    # Core pipeline venv
    setup_python_venv "core-pipeline" "$PROJECT_ROOT/core/py/pipeline/.venv" "$PROJECT_ROOT/core/py/pipeline/requirements.txt"
    
    # 2. Build C++ binaries with absolute paths and record compile times
    log_info "=== Phase 2: Building C++ binaries ==="
    build_cpp_binaries
    
    # 3. Spin up Docker Compose and store container logs
    log_info "=== Phase 3: Starting Docker services ==="
    start_docker_compose
    
    # 4. Validate make targets and entrypoint help
    log_info "=== Phase 4: Validating commands ==="
    validate_make_targets
    validate_entrypoint_help
    
    # Finalize report
    finalize_report
    
    log_success "Build and run validation completed successfully!"
    log_info "Check the report at: $REPORT_FILE"
}

# Execute main function
main "$@"
