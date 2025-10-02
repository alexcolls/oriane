#!/bin/bash

# 05_quality_metrics.sh
# Comprehensive code quality metrics and test coverage analysis

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_FILE="code_quality_report.md"
COVERAGE_HTML_DIR="htmlcov"
COVERAGE_TEXT_FILE="coverage.txt"
TEMP_DIR="$(mktemp -d)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}

trap cleanup EXIT

# Initialize report
initialize_report() {
    log "Initializing code quality report..."
    
    cat > "$REPORT_FILE" << EOF
# Code Quality Report

Generated on: $(date)

## Summary

This report provides a comprehensive analysis of code quality metrics, including:
- Linting and code style checks
- Type checking results
- Test coverage analysis
- Technical debt indicators

---

EOF
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get badge color based on score
get_badge_color() {
    local score=$1
    local threshold_good=${2:-80}
    local threshold_warning=${3:-60}
    
    if (( $(echo "$score >= $threshold_good" | bc -l) )); then
        echo "brightgreen"
    elif (( $(echo "$score >= $threshold_warning" | bc -l) )); then
        echo "yellow"
    else
        echo "red"
    fi
}

# Function to run Python linting with ruff
run_ruff_check() {
    log "Running ruff linting..."
    
    if ! command_exists ruff; then
        warning "ruff not found, skipping Python linting"
        return 1
    fi
    
    local ruff_output="$TEMP_DIR/ruff_output.txt"
    local ruff_exit_code=0
    
    # Run ruff check
    ruff check . --output-format=text > "$ruff_output" 2>&1 || ruff_exit_code=$?
    
    # Count issues
    local issue_count=0
    if [[ -s "$ruff_output" ]]; then
        issue_count=$(wc -l < "$ruff_output")
    fi
    
    # Determine status
    local status="PASS"
    local badge_color="brightgreen"
    if [[ $ruff_exit_code -ne 0 ]]; then
        status="FAIL"
        badge_color="red"
    fi
    
    # Add to report
    cat >> "$REPORT_FILE" << EOF
## Ruff Linting Results

![Ruff Status](https://img.shields.io/badge/Ruff-$status-$badge_color)
![Issues Found](https://img.shields.io/badge/Issues-$issue_count-$(get_badge_color $(echo "100 - $issue_count" | bc -l)))

**Status:** $status  
**Issues Found:** $issue_count

### Details

\`\`\`
$(cat "$ruff_output")
\`\`\`

**Recommended Threshold:** 0 issues for production code

---

EOF
    
    success "Ruff check completed: $issue_count issues found"
}

# Function to run Black code formatting check
run_black_check() {
    log "Running Black code formatting check..."
    
    if ! command_exists black; then
        warning "black not found, skipping Python formatting check"
        return 1
    fi
    
    local black_output="$TEMP_DIR/black_output.txt"
    local black_exit_code=0
    
    # Run black --check
    black --check --diff . > "$black_output" 2>&1 || black_exit_code=$?
    
    # Determine status
    local status="PASS"
    local badge_color="brightgreen"
    local files_to_format=0
    
    if [[ $black_exit_code -ne 0 ]]; then
        status="FAIL"
        badge_color="red"
        files_to_format=$(grep -c "would reformat" "$black_output" 2>/dev/null || echo "0")
    fi
    
    # Add to report
    cat >> "$REPORT_FILE" << EOF
## Black Code Formatting

![Black Status](https://img.shields.io/badge/Black-$status-$badge_color)
![Files to Format](https://img.shields.io/badge/Files_to_Format-$files_to_format-$(get_badge_color $(echo "100 - $files_to_format * 10" | bc -l)))

**Status:** $status  
**Files requiring formatting:** $files_to_format

### Details

\`\`\`
$(cat "$black_output")
\`\`\`

**Recommended Threshold:** All files should be properly formatted (0 files to reformat)

---

EOF
    
    success "Black check completed: $files_to_format files need formatting"
}

# Function to run MyPy type checking
run_mypy_check() {
    log "Running MyPy type checking..."
    
    if ! command_exists mypy; then
        warning "mypy not found, skipping Python type checking"
        return 1
    fi
    
    local mypy_output="$TEMP_DIR/mypy_output.txt"
    local mypy_exit_code=0
    
    # Run mypy
    mypy . --ignore-missing-imports --show-error-codes > "$mypy_output" 2>&1 || mypy_exit_code=$?
    
    # Count errors
    local error_count=0
    if [[ -s "$mypy_output" ]]; then
        error_count=$(grep -c "error:" "$mypy_output" 2>/dev/null || echo "0")
    fi
    
    # Determine status
    local status="PASS"
    local badge_color="brightgreen"
    if [[ $mypy_exit_code -ne 0 ]]; then
        status="FAIL"
        badge_color="red"
    fi
    
    # Add to report
    cat >> "$REPORT_FILE" << EOF
## MyPy Type Checking

![MyPy Status](https://img.shields.io/badge/MyPy-$status-$badge_color)
![Type Errors](https://img.shields.io/badge/Type_Errors-$error_count-$(get_badge_color $(echo "100 - $error_count * 5" | bc -l)))

**Status:** $status  
**Type errors found:** $error_count

### Details

\`\`\`
$(cat "$mypy_output")
\`\`\`

**Recommended Threshold:** 0 type errors for production code

---

EOF
    
    success "MyPy check completed: $error_count type errors found"
}

# Function to run clang-tidy for C++
run_clang_tidy_check() {
    log "Running clang-tidy for C++ code..."
    
    if ! command_exists clang-tidy; then
        warning "clang-tidy not found, skipping C++ linting"
        return 1
    fi
    
    # Find C++ files
    local cpp_files
    cpp_files=$(find . -name "*.cpp" -o -name "*.cc" -o -name "*.cxx" -o -name "*.c++" -o -name "*.hpp" -o -name "*.h" -o -name "*.hxx" -o -name "*.h++" 2>/dev/null || true)
    
    if [[ -z "$cpp_files" ]]; then
        warning "No C++ files found, skipping clang-tidy"
        return 1
    fi
    
    local clang_tidy_output="$TEMP_DIR/clang_tidy_output.txt"
    local clang_tidy_exit_code=0
    
    # Run clang-tidy on found files
    echo "$cpp_files" | xargs clang-tidy -checks="*" > "$clang_tidy_output" 2>&1 || clang_tidy_exit_code=$?
    
    # Count warnings/errors
    local warning_count=0
    local error_count=0
    if [[ -s "$clang_tidy_output" ]]; then
        warning_count=$(grep -c "warning:" "$clang_tidy_output" 2>/dev/null || echo "0")
        error_count=$(grep -c "error:" "$clang_tidy_output" 2>/dev/null || echo "0")
    fi
    
    local total_issues=$((warning_count + error_count))
    
    # Determine status
    local status="PASS"
    local badge_color="brightgreen"
    if [[ $clang_tidy_exit_code -ne 0 ]] || [[ $total_issues -gt 0 ]]; then
        status="FAIL"
        badge_color="red"
    fi
    
    # Add to report
    cat >> "$REPORT_FILE" << EOF
## Clang-Tidy C++ Analysis

![Clang-Tidy Status](https://img.shields.io/badge/Clang_Tidy-$status-$badge_color)
![Total Issues](https://img.shields.io/badge/Total_Issues-$total_issues-$(get_badge_color $(echo "100 - $total_issues" | bc -l)))

**Status:** $status  
**Warnings:** $warning_count  
**Errors:** $error_count  
**Total Issues:** $total_issues

### Details

\`\`\`
$(cat "$clang_tidy_output")
\`\`\`

**Recommended Threshold:** 0 errors, <10 warnings for production code

---

EOF
    
    success "Clang-tidy check completed: $total_issues issues found"
}

# Function to count TODO/FIXME tags
count_todo_fixme() {
    log "Counting TODO/FIXME tags..."
    
    local todo_count=0
    local fixme_count=0
    local todo_files="$TEMP_DIR/todo_files.txt"
    local fixme_files="$TEMP_DIR/fixme_files.txt"
    
    # Find TODO tags (excluding common dependency directories)
    grep -rn "TODO\|FIXME" . \
        --include="*.py" --include="*.js" --include="*.ts" --include="*.cpp" --include="*.hpp" --include="*.h" --include="*.c" --include="*.java" --include="*.go" --include="*.rs" --include="*.rb" --include="*.php" --include="*.md" \
        --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="env" --exclude-dir="node_modules" --exclude-dir="__pycache__" \
        --exclude-dir=".git" --exclude-dir="build" --exclude-dir="dist" --exclude-dir=".pytest_cache" \
        --exclude-dir="site-packages" --exclude-dir="lib" --exclude-dir="vendor" --exclude-dir="third_party" \
        2>/dev/null > "$TEMP_DIR/all_todos.txt" || true
    
    if [[ -s "$TEMP_DIR/all_todos.txt" ]]; then
        todo_count=$(grep -c "TODO" "$TEMP_DIR/all_todos.txt" 2>/dev/null || echo "0")
        fixme_count=$(grep -c "FIXME" "$TEMP_DIR/all_todos.txt" 2>/dev/null || echo "0")
        
        grep "TODO" "$TEMP_DIR/all_todos.txt" > "$todo_files" 2>/dev/null || true
        grep "FIXME" "$TEMP_DIR/all_todos.txt" > "$fixme_files" 2>/dev/null || true
    fi
    
    local total_debt=$((todo_count + fixme_count))
    
    # Add to report
    cat >> "$REPORT_FILE" << EOF
## Technical Debt Analysis

![TODO Count](https://img.shields.io/badge/TODO-$todo_count-$(get_badge_color $(echo "100 - $todo_count * 2" | bc -l)))
![FIXME Count](https://img.shields.io/badge/FIXME-$fixme_count-$(get_badge_color $(echo "100 - $fixme_count * 5" | bc -l)))
![Total Debt](https://img.shields.io/badge/Total_Debt-$total_debt-$(get_badge_color $(echo "100 - $total_debt * 2" | bc -l)))

**TODO tags:** $todo_count  
**FIXME tags:** $fixme_count  
**Total technical debt items:** $total_debt

### TODO Items

\`\`\`
$(cat "$todo_files" 2>/dev/null || echo "No TODO items found")
\`\`\`

### FIXME Items

\`\`\`
$(cat "$fixme_files" 2>/dev/null || echo "No FIXME items found")
\`\`\`

**Recommended Thresholds:**
- TODO: <20 items (informational debt)
- FIXME: <5 items (critical debt requiring attention)

---

EOF
    
    success "Technical debt analysis completed: $total_debt items found"
}

# Function to run pytest with coverage
run_pytest_coverage() {
    log "Running pytest with coverage analysis..."
    
    if ! command_exists pytest; then
        warning "pytest not found, skipping test coverage"
        return 1
    fi
    
    if ! python3 -c "import pytest_cov" 2>/dev/null; then
        warning "pytest-cov not found, installing..."
        pip3 install pytest-cov || {
            error "Failed to install pytest-cov"
            return 1
        }
    fi
    
    local pytest_output="$TEMP_DIR/pytest_output.txt"
    local pytest_exit_code=0
    
    # Run pytest with coverage
    pytest --cov=. --cov-report=html:"$COVERAGE_HTML_DIR" --cov-report=term-missing --cov-report=term > "$pytest_output" 2>&1 || pytest_exit_code=$?
    
    # Generate text coverage report
    pytest --cov=. --cov-report=term > "$COVERAGE_TEXT_FILE" 2>&1 || true
    
    # Extract coverage percentage
    local coverage_percent="0"
    if [[ -s "$pytest_output" ]]; then
        coverage_percent=$(grep -o "TOTAL.*[0-9]\+%" "$pytest_output" | grep -o "[0-9]\+%" | tr -d '%' || echo "0")
    fi
    
    # Count tests
    local tests_run=0
    local tests_failed=0
    local tests_passed=0
    
    if [[ -s "$pytest_output" ]]; then
        tests_run=$(grep -o "[0-9]\+ passed" "$pytest_output" | grep -o "[0-9]\+" || echo "0")
        tests_failed=$(grep -o "[0-9]\+ failed" "$pytest_output" | grep -o "[0-9]\+" || echo "0")
        tests_passed=$tests_run
    fi
    
    # Determine status
    local status="PASS"
    local badge_color="brightgreen"
    if [[ $pytest_exit_code -ne 0 ]]; then
        status="FAIL"
        badge_color="red"
    fi
    
    # Add to report
    cat >> "$REPORT_FILE" << EOF
## Test Coverage Analysis

![Test Status](https://img.shields.io/badge/Tests-$status-$badge_color)
![Coverage](https://img.shields.io/badge/Coverage-$coverage_percent%25-$(get_badge_color $coverage_percent))
![Tests Run](https://img.shields.io/badge/Tests_Run-$tests_run-blue)
![Tests Failed](https://img.shields.io/badge/Tests_Failed-$tests_failed-$(if [[ $tests_failed -eq 0 ]]; then echo "brightgreen"; else echo "red"; fi))

**Test Status:** $status  
**Coverage:** $coverage_percent%  
**Tests Run:** $tests_run  
**Tests Failed:** $tests_failed  
**Tests Passed:** $tests_passed

### Coverage Details

\`\`\`
$(cat "$COVERAGE_TEXT_FILE" 2>/dev/null || echo "Coverage report not available")
\`\`\`

### Test Output

\`\`\`
$(cat "$pytest_output")
\`\`\`

**Coverage Reports Generated:**
- HTML Report: \`$COVERAGE_HTML_DIR/index.html\`
- Text Report: \`$COVERAGE_TEXT_FILE\`

**Recommended Thresholds:**
- Minimum Coverage: 80%
- Good Coverage: 90%+
- Excellent Coverage: 95%+

---

EOF
    
    success "Test coverage analysis completed: $coverage_percent% coverage"
}

# Function to generate summary and recommendations
generate_summary() {
    log "Generating summary and recommendations..."
    
    cat >> "$REPORT_FILE" << 'EOF'
## Summary and Recommendations

### Quality Metrics Overview

| Metric | Status | Score/Count | Threshold | Action Required |
|--------|--------|-------------|-----------|-----------------|
| Ruff Linting | See above | See above | 0 issues | Fix linting issues |
| Black Formatting | See above | See above | 0 files | Run `black .` |
| MyPy Type Checking | See above | See above | 0 errors | Add type hints |
| Clang-Tidy (C++) | See above | See above | 0 errors, <10 warnings | Fix C++ issues |
| TODO Count | See above | See above | <20 items | Review and resolve |
| FIXME Count | See above | See above | <5 items | **Priority: Fix immediately** |
| Test Coverage | See above | See above | >80% | Write more tests |

### Recommended Actions

1. **High Priority:**
   - Fix all FIXME items immediately
   - Resolve any failing tests
   - Address critical linting errors

2. **Medium Priority:**
   - Improve test coverage to >80%
   - Fix type checking errors
   - Resolve C++ linting warnings

3. **Low Priority:**
   - Clean up TODO items
   - Improve code formatting consistency
   - Enhance documentation

### Quality Gates

For production deployment, ensure:
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] No FIXME items remain
- [ ] No critical linting errors
- [ ] Type checking passes
- [ ] Code is properly formatted

### Next Steps

1. Run individual tools to fix specific issues:
   ```bash
   # Fix Python formatting
   black .
   
   # Fix Python imports and basic issues
   ruff check --fix .
   
   # Run tests
   pytest --cov=.
   
   # Type check
   mypy .
   ```

2. Set up pre-commit hooks to maintain quality
3. Configure CI/CD pipeline with these quality checks
4. Regular quality reviews and technical debt cleanup

---

**Report Generated:** $(date)  
**Total Runtime:** $(date -d@$(($(date +%s) - START_TIME)) -u +%H:%M:%S)
EOF
}

# Main execution function
main() {
    local START_TIME=$(date +%s)
    
    log "Starting comprehensive code quality analysis..."
    
    # Initialize report
    initialize_report
    
    # Run all quality checks
    run_ruff_check || true
    run_black_check || true
    run_mypy_check || true
    run_clang_tidy_check || true
    count_todo_fixme
    run_pytest_coverage || true
    
    # Generate summary
    generate_summary
    
    success "Code quality analysis completed!"
    log "Report generated: $REPORT_FILE"
    
    if [[ -d "$COVERAGE_HTML_DIR" ]]; then
        log "HTML coverage report: $COVERAGE_HTML_DIR/index.html"
    fi
    
    if [[ -f "$COVERAGE_TEXT_FILE" ]]; then
        log "Text coverage report: $COVERAGE_TEXT_FILE"
    fi
    
    log "Quality metrics analysis completed in $(date -d@$(($(date +%s) - START_TIME)) -u +%H:%M:%S)"
}

# Run main function
main "$@"
