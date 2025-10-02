#!/bin/bash

# =============================================================================
# 🧪 Oriane API Test Runner
# =============================================================================
# Runs all tests with nice formatting and emoji logging

# Created: 2025-07-15
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_header() {
    local title=$1
    echo
    print_color $BLUE "════════════════════════════════════════════════════════════════"
    print_color $WHITE "  $title"
    print_color $BLUE "════════════════════════════════════════════════════════════════"
    echo
}

# Function to print step info
print_step() {
    local emoji=$1
    local message=$2
    print_color $CYAN "$emoji $message"
}

# Function to print success
print_success() {
    local message=$1
    print_color $GREEN "✅ $message"
}

# Function to print warning
print_warning() {
    local message=$1
    print_color $YELLOW "⚠️  $message"
}

# Function to print error
print_error() {
    local message=$1
    print_color $RED "❌ $message"
}

# Function to check if virtual environment is activated
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "Virtual environment not detected. Activating .venv..."
        if [[ -f ".venv/bin/activate" ]]; then
            source .venv/bin/activate
            print_success "Virtual environment activated"
        else
            print_error "Virtual environment not found! Please create .venv first."
            exit 1
        fi
    else
        print_success "Virtual environment already active: $(basename $VIRTUAL_ENV)"
    fi
}

# Function to check dependencies
check_dependencies() {
    print_step "🔍" "Checking test dependencies..."

    # Check if pytest is available
    if ! python -c "import pytest" &> /dev/null; then
        print_error "pytest not found! Installing..."
        pip install pytest
    fi

    # Check if test assets exist
    if [[ ! -d "tests/assets" ]]; then
        print_warning "Test assets directory not found!"
        print_step "📁" "Creating tests/assets directory..."
        mkdir -p tests/assets
        print_warning "Please add test files (image.png, image.jpeg, video.mp4) to tests/assets/"
    else
        print_success "Test assets directory found"

        # Check for specific test files
        local missing_files=()
        [[ ! -f "tests/assets/image.png" ]] && missing_files+=("image.png")
        [[ ! -f "tests/assets/image.jpeg" ]] && missing_files+=("image.jpeg")
        [[ ! -f "tests/assets/video.mp4" ]] && missing_files+=("video.mp4")

        if [[ ${#missing_files[@]} -gt 0 ]]; then
            print_warning "Missing test assets: ${missing_files[*]}"
        else
            print_success "All test assets found"
        fi
    fi
}

# Function to run a specific test file
run_test_file() {
    local test_file=$1
    local test_name=$2
    local emoji=$3

    print_step "$emoji" "Running $test_name..."

    if python -m pytest "$test_file" -v --tb=short --color=yes; then
        print_success "$test_name passed!"
        return 0
    else
        print_error "$test_name failed!"
        return 1
    fi
}

# Function to generate test summary
generate_summary() {
    local total_tests=$1
    local passed_tests=$2
    local failed_tests=$3
    local skipped_tests=$4
    local duration=$5

    echo
    print_header "🏁 TEST SUMMARY"

    print_color $WHITE "📊 Results:"
    print_success "Passed: $passed_tests"
    [[ $failed_tests -gt 0 ]] && print_error "Failed: $failed_tests" || print_color $GREEN "Failed: $failed_tests"
    [[ $skipped_tests -gt 0 ]] && print_warning "Skipped: $skipped_tests" || print_color $GREEN "Skipped: $skipped_tests"
    print_color $BLUE "📈 Total: $total_tests tests"
    print_color $PURPLE "⏱️  Duration: ${duration}s"

    echo
    if [[ $failed_tests -eq 0 ]]; then
        print_color $GREEN "🎉 ALL TESTS PASSED! 🎉"
        print_color $GREEN "Ready for deployment! 🚀"
    else
        print_color $RED "💥 SOME TESTS FAILED! 💥"
        print_color $YELLOW "Please fix failing tests before deployment."
    fi
    echo
}

# Main function
main() {
    # Start timer
    local start_time=$(date +%s)

    print_header "🧪 ORIANE API TEST SUITE"
    print_color $PURPLE "Starting comprehensive test run..."
    print_color $BLUE "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

    # Check environment
    print_step "🔧" "Checking environment..."
    check_venv
    check_dependencies

    # Initialize counters
    local total_failed=0
    local test_files=(
        "tests/test_auth.py:🔐 Authentication Unit Tests"
        "tests/test_auth_integration.py:🔗 Authentication Integration Tests"
        "tests/test_api_endpoints_auth.py:🛡️  API Endpoint Authentication Tests"
        "tests/test_add_content.py:📁 Add Content Endpoint Tests"
        "tests/test_get_embeddings.py:🔗 Get Embeddings Endpoint Tests"
        "tests/test_search_by.py:🔍 Search By Text & Image Endpoint Tests"
        "tests/test_user_content_search.py:👤 User Content Search Endpoint Tests"
        "tests/test_video_processing_service.py:🎬 Video Processing Service Tests"
    )

    echo
    print_header "🏃 RUNNING INDIVIDUAL TEST SUITES"

    # Run each test file individually for better reporting
    for test_entry in "${test_files[@]}"; do
        IFS=':' read -r test_file test_name <<< "$test_entry"

        if [[ -f "$test_file" ]]; then
            # Extract emoji from test name
            local emoji=$(echo "$test_name" | cut -d' ' -f1)
            local clean_name=$(echo "$test_name" | cut -d' ' -f2-)

            if ! run_test_file "$test_file" "$clean_name" "$emoji"; then
                ((total_failed++))
            fi
            echo "─────────────────────────────────────────────────────────────────"
        else
            print_warning "Test file not found: $test_file"
        fi
    done

    # Run full test suite for final summary
    print_header "🔄 RUNNING COMPLETE TEST SUITE"
    print_step "🚀" "Executing full pytest run..."

    # Capture pytest output and parse results
    local pytest_output
    local pytest_exit_code

    pytest_output=$(python -m pytest tests/ --tb=short --color=no -q 2>&1) || pytest_exit_code=$?

    # Parse results from pytest output
    local total_tests=$(echo "$pytest_output" | grep -o '[0-9]\+ passed\|[0-9]\+ failed\|[0-9]\+ skipped' | awk '{sum += $1} END {print sum+0}')
    local passed_tests=$(echo "$pytest_output" | grep -o '[0-9]\+ passed' | cut -d' ' -f1)
    local failed_tests=$(echo "$pytest_output" | grep -o '[0-9]\+ failed' | cut -d' ' -f1)
    local skipped_tests=$(echo "$pytest_output" | grep -o '[0-9]\+ skipped' | cut -d' ' -f1)

    # Set defaults if not found
    [[ -z "$passed_tests" ]] && passed_tests=0
    [[ -z "$failed_tests" ]] && failed_tests=0
    [[ -z "$skipped_tests" ]] && skipped_tests=0
    [[ -z "$total_tests" ]] && total_tests=$((passed_tests + failed_tests + skipped_tests))

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Generate summary
    generate_summary "$total_tests" "$passed_tests" "$failed_tests" "$skipped_tests" "$duration"

    # Save detailed log
    local log_file="test-results-$(date +%Y%m%d-%H%M%S).log"
    echo "$pytest_output" > "$log_file"
    print_step "📝" "Detailed results saved to: $log_file"

    # Exit with appropriate code
    if [[ $failed_tests -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
