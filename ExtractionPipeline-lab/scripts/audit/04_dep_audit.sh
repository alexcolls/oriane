#!/bin/bash

# 04_dep_audit.sh - Comprehensive Dependency Audit Script
# Consolidates Python requirements, C++ CMakeLists, Docker images, and Terraform AMIs
# Runs security audits and cross-references licenses
#
# Usage: ./04_dep_audit.sh [OPTIONS]
#
# This script performs a comprehensive dependency audit by:
# 1. Consolidating Python requirements.txt files
# 2. Extracting C++ dependencies from CMakeLists.txt
# 3. Identifying Docker base images from Dockerfiles
# 4. Extracting Terraform AMIs and resources from .tf files
# 5. Running security audits with pip-audit, safety, and npm audit
# 6. Cross-referencing licenses using licensecheck
# 7. Generating a comprehensive dependency_audit.md report
#
# Requirements:
# - Python 3.x with pip
# - Node.js with npm (optional, for npm audit)
# - pipx (recommended for tool installation)
#
# Output:
# - audit_results/dependency_audit.md: Main audit report
# - audit_results/temp/: Temporary files and consolidated dependencies

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIT_DIR="${SCRIPT_DIR}/audit_results"
TEMP_DIR="${AUDIT_DIR}/temp"
OUTPUT_FILE="${AUDIT_DIR}/dependency_audit.md"
CONSOLIDATED_REQUIREMENTS="${TEMP_DIR}/consolidated_requirements.txt"
CONSOLIDATED_DEPS="${TEMP_DIR}/all_dependencies.txt"

# Create audit directories
mkdir -p "${AUDIT_DIR}" "${TEMP_DIR}"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install missing tools
install_audit_tools() {
    log "Checking and installing required audit tools..."
    
    # Try to install using pipx first, then fall back to pip with --user
    install_python_tool() {
        local tool="$1"
        if command_exists "$tool"; then
            return 0
        fi
        
        log "Installing $tool..."
        
        # Try pipx first (recommended for externally managed environments)
        if command_exists pipx; then
            pipx install "$tool" 2>/dev/null && return 0
        fi
        
        # Try pip with --user flag
        python3 -m pip install --user "$tool" 2>/dev/null && return 0
        
        # Try with --break-system-packages as last resort
        python3 -m pip install --break-system-packages "$tool" 2>/dev/null && return 0
        
        warning "Failed to install $tool. Some audit features may be limited."
        return 1
    }
    
    # Install audit tools
    install_python_tool "pip-audit"
    install_python_tool "safety"
    install_python_tool "licensecheck"
    
    # Check for npm (for npm audit)
    if ! command_exists npm; then
        warning "npm not found. Node.js auditing will be skipped."
    fi
}

# Function to consolidate Python requirements
consolidate_python_requirements() {
    log "Consolidating Python requirements..."
    
    # Find all requirements files
    local req_files=($(find "${SCRIPT_DIR}" -name "requirements*.txt" -type f))
    
    if [[ ${#req_files[@]} -eq 0 ]]; then
        warning "No Python requirements files found"
        return 0
    fi
    
    # Create consolidated requirements file
    echo "# Consolidated Python Requirements" > "${CONSOLIDATED_REQUIREMENTS}"
    echo "# Generated on $(date)" >> "${CONSOLIDATED_REQUIREMENTS}"
    echo "" >> "${CONSOLIDATED_REQUIREMENTS}"
    
    # Process each requirements file
    for req_file in "${req_files[@]}"; do
        if [[ -f "$req_file" ]]; then
            echo "# From: $req_file" >> "${CONSOLIDATED_REQUIREMENTS}"
            # Remove comments and empty lines, then sort and deduplicate
            grep -v '^#' "$req_file" | grep -v '^$' | sort -u >> "${CONSOLIDATED_REQUIREMENTS}"
            echo "" >> "${CONSOLIDATED_REQUIREMENTS}"
        fi
    done
    
    # Remove duplicates while preserving order
    sort -u "${CONSOLIDATED_REQUIREMENTS}" -o "${CONSOLIDATED_REQUIREMENTS}"
    
    success "Consolidated $(wc -l < "${CONSOLIDATED_REQUIREMENTS}") Python dependencies"
}

# Function to extract C++ dependencies from CMakeLists.txt
extract_cpp_dependencies() {
    log "Extracting C++ dependencies from CMakeLists.txt..."
    
    local cmake_files=($(find "${SCRIPT_DIR}" -name "CMakeLists.txt" -type f))
    local cpp_deps_file="${TEMP_DIR}/cpp_dependencies.txt"
    
    if [[ ${#cmake_files[@]} -eq 0 ]]; then
        warning "No CMakeLists.txt files found"
        return 0
    fi
    
    echo "# C++ Dependencies from CMakeLists.txt" > "${cpp_deps_file}"
    echo "# Generated on $(date)" >> "${cpp_deps_file}"
    echo "" >> "${cpp_deps_file}"
    
    for cmake_file in "${cmake_files[@]}"; do
        if [[ -f "$cmake_file" ]]; then
            echo "# From: $cmake_file" >> "${cpp_deps_file}"
            # Extract find_package, target_link_libraries, and external project calls
            grep -E "(find_package|target_link_libraries|ExternalProject_Add|FetchContent_Declare)" "$cmake_file" | \
                sed 's/^[[:space:]]*//' >> "${cpp_deps_file}" || true
            echo "" >> "${cpp_deps_file}"
        fi
    done
    
    success "Extracted C++ dependencies from ${#cmake_files[@]} CMakeLists.txt files"
}

# Function to extract Docker base images
extract_docker_images() {
    log "Extracting Docker base images..."
    
    local docker_files=($(find "${SCRIPT_DIR}" -name "Dockerfile*" -type f))
    local docker_deps_file="${TEMP_DIR}/docker_dependencies.txt"
    
    if [[ ${#docker_files[@]} -eq 0 ]]; then
        warning "No Dockerfile found"
        return 0
    fi
    
    echo "# Docker Base Images" > "${docker_deps_file}"
    echo "# Generated on $(date)" >> "${docker_deps_file}"
    echo "" >> "${docker_deps_file}"
    
    for docker_file in "${docker_files[@]}"; do
        if [[ -f "$docker_file" ]]; then
            echo "# From: $docker_file" >> "${docker_deps_file}"
            # Extract FROM statements
            grep -E "^FROM" "$docker_file" | sed 's/^FROM[[:space:]]*//' >> "${docker_deps_file}" || true
            echo "" >> "${docker_deps_file}"
        fi
    done
    
    success "Extracted Docker images from ${#docker_files[@]} Dockerfile(s)"
}

# Function to extract Terraform AMIs
extract_terraform_amis() {
    log "Extracting Terraform AMIs..."
    
    local tf_files=($(find "${SCRIPT_DIR}" -name "*.tf" -type f))
    local tf_deps_file="${TEMP_DIR}/terraform_dependencies.txt"
    
    if [[ ${#tf_files[@]} -eq 0 ]]; then
        warning "No Terraform files found"
        return 0
    fi
    
    echo "# Terraform AMIs and Images" > "${tf_deps_file}"
    echo "# Generated on $(date)" >> "${tf_deps_file}"
    echo "" >> "${tf_deps_file}"
    
    for tf_file in "${tf_files[@]}"; do
        if [[ -f "$tf_file" ]]; then
            echo "# From: $tf_file" >> "${tf_deps_file}"
            # Extract AMI references and docker images
            grep -E "(ami-|image.*=|source.*=)" "$tf_file" | \
                sed 's/^[[:space:]]*//' >> "${tf_deps_file}" || true
            echo "" >> "${tf_deps_file}"
        fi
    done
    
    success "Extracted Terraform dependencies from ${#tf_files[@]} .tf files"
}

# Function to run Python security audits
run_python_security_audit() {
    log "Running Python security audits..."
    
    if [[ ! -f "${CONSOLIDATED_REQUIREMENTS}" ]]; then
        warning "No consolidated requirements file found, skipping Python audit"
        return 0
    fi
    
    local python_audit_file="${TEMP_DIR}/python_security_audit.txt"
    
    echo "# Python Security Audit Results" > "${python_audit_file}"
    echo "# Generated on $(date)" >> "${python_audit_file}"
    echo "" >> "${python_audit_file}"
    
    # Run pip-audit
    if command_exists pip-audit; then
        log "Running pip-audit..."
        echo "## pip-audit Results" >> "${python_audit_file}"
        echo '```' >> "${python_audit_file}"
        pip-audit --requirement "${CONSOLIDATED_REQUIREMENTS}" --format=columns >> "${python_audit_file}" 2>&1 || true
        echo '```' >> "${python_audit_file}"
        echo "" >> "${python_audit_file}"
    fi
    
    # Run safety
    if command_exists safety; then
        log "Running safety check..."
        echo "## Safety Check Results" >> "${python_audit_file}"
        echo '```' >> "${python_audit_file}"
        safety check --file "${CONSOLIDATED_REQUIREMENTS}" >> "${python_audit_file}" 2>&1 || true
        echo '```' >> "${python_audit_file}"
        echo "" >> "${python_audit_file}"
    fi
    
    success "Python security audit completed"
}

# Function to run npm audit
run_npm_audit() {
    log "Running npm audit..."
    
    # Find main package.json files (exclude node_modules)
    local package_json_files=($(find "${SCRIPT_DIR}" -name "package.json" -not -path "*/node_modules/*" -type f))
    local npm_audit_file="${TEMP_DIR}/npm_audit.txt"
    
    if [[ ${#package_json_files[@]} -eq 0 ]]; then
        warning "No package.json files found, skipping npm audit"
        return 0
    fi
    
    if ! command_exists npm; then
        warning "npm not found, skipping npm audit"
        return 0
    fi
    
    echo "# NPM Security Audit Results" > "${npm_audit_file}"
    echo "# Generated on $(date)" >> "${npm_audit_file}"
    echo "" >> "${npm_audit_file}"
    
    for package_json in "${package_json_files[@]}"; do
        local package_dir=$(dirname "$package_json")
        echo "## Audit for: $package_json" >> "${npm_audit_file}"
        echo '```' >> "${npm_audit_file}"
        
        # Change to package directory and run audit
        (cd "$package_dir" && {
            # Check if package-lock.json exists
            if [[ -f "package-lock.json" ]]; then
                npm audit --omit=dev --audit-level=moderate
            else
                echo "No package-lock.json found. Creating one for audit..."
                npm install --package-lock-only >/dev/null 2>&1 || true
                if [[ -f "package-lock.json" ]]; then
                    npm audit --omit=dev --audit-level=moderate
                else
                    echo "Unable to create package-lock.json. Skipping audit for this package."
                fi
            fi
        }) >> "${npm_audit_file}" 2>&1 || true
        
        echo '```' >> "${npm_audit_file}"
        echo "" >> "${npm_audit_file}"
    done
    
    success "npm audit completed"
}

# Function to run license check
run_license_check() {
    log "Running license check..."
    
    local license_file="${TEMP_DIR}/license_check.txt"
    
    echo "# License Check Results" > "${license_file}"
    echo "# Generated on $(date)" >> "${license_file}"
    echo "" >> "${license_file}"
    
    if [[ -f "${CONSOLIDATED_REQUIREMENTS}" ]] && command_exists licensecheck; then
        echo "## Python Package Licenses" >> "${license_file}"
        echo '```' >> "${license_file}"
        licensecheck --requirement "${CONSOLIDATED_REQUIREMENTS}" >> "${license_file}" 2>&1 || true
        echo '```' >> "${license_file}"
        echo "" >> "${license_file}"
    fi
    
    # Check for license files in the project
    echo "## Project License Files" >> "${license_file}"
    local license_files=($(find "${SCRIPT_DIR}" -name "LICENSE*" -o -name "COPYING*" -o -name "COPYRIGHT*" -type f))
    
    if [[ ${#license_files[@]} -gt 0 ]]; then
        for license_file_path in "${license_files[@]}"; do
            echo "### Found: $license_file_path" >> "${license_file}"
            echo '```' >> "${license_file}"
            head -10 "$license_file_path" >> "${license_file}"
            echo '```' >> "${license_file}"
            echo "" >> "${license_file}"
        done
    else
        echo "No license files found in the project." >> "${license_file}"
    fi
    
    success "License check completed"
}

# Function to generate consolidated dependency audit report
generate_audit_report() {
    log "Generating consolidated dependency audit report..."
    
    cat > "${OUTPUT_FILE}" << 'EOF'
# Dependency Audit Report

This report provides a comprehensive overview of all dependencies, their security status, and licensing information.

**Generated on:** $(date)
**Project:** $(basename "${SCRIPT_DIR}")

## Executive Summary

- **Python Dependencies:** Found in consolidated requirements
- **C++ Dependencies:** Extracted from CMakeLists.txt files
- **Docker Images:** Extracted from Dockerfile(s)
- **Terraform Resources:** Extracted from .tf files
- **Node.js Dependencies:** Audited from package.json files

## Dependency Inventory

### Python Dependencies
EOF
    
    # Add Python dependencies if available
    if [[ -f "${CONSOLIDATED_REQUIREMENTS}" ]]; then
        echo "" >> "${OUTPUT_FILE}"
        echo "| Package | Version | License | CVE Status |" >> "${OUTPUT_FILE}"
        echo "|---------|---------|---------|------------|" >> "${OUTPUT_FILE}"
        
        # Parse consolidated requirements and create table
        grep -v '^#' "${CONSOLIDATED_REQUIREMENTS}" | grep -v '^$' | while read -r line; do
            if [[ -n "$line" ]]; then
                # Extract package name and version
                package=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | cut -d'!' -f1)
                version=$(echo "$line" | grep -o '[0-9][0-9.]*' | head -1 || echo "Not specified")
                echo "| $package | $version | TBD | TBD |" >> "${OUTPUT_FILE}"
            fi
        done
    else
        echo "" >> "${OUTPUT_FILE}"
        echo "No Python dependencies found." >> "${OUTPUT_FILE}"
    fi
    
    # Add C++ dependencies section
    echo "" >> "${OUTPUT_FILE}"
    echo "### C++ Dependencies" >> "${OUTPUT_FILE}"
    if [[ -f "${TEMP_DIR}/cpp_dependencies.txt" ]]; then
        echo '```cmake' >> "${OUTPUT_FILE}"
        cat "${TEMP_DIR}/cpp_dependencies.txt" >> "${OUTPUT_FILE}"
        echo '```' >> "${OUTPUT_FILE}"
    else
        echo "No C++ dependencies found." >> "${OUTPUT_FILE}"
    fi
    
    # Add Docker images section
    echo "" >> "${OUTPUT_FILE}"
    echo "### Docker Base Images" >> "${OUTPUT_FILE}"
    if [[ -f "${TEMP_DIR}/docker_dependencies.txt" ]]; then
        echo '```dockerfile' >> "${OUTPUT_FILE}"
        cat "${TEMP_DIR}/docker_dependencies.txt" >> "${OUTPUT_FILE}"
        echo '```' >> "${OUTPUT_FILE}"
    else
        echo "No Docker images found." >> "${OUTPUT_FILE}"
    fi
    
    # Add Terraform resources section
    echo "" >> "${OUTPUT_FILE}"
    echo "### Terraform Resources" >> "${OUTPUT_FILE}"
    if [[ -f "${TEMP_DIR}/terraform_dependencies.txt" ]]; then
        echo '```hcl' >> "${OUTPUT_FILE}"
        cat "${TEMP_DIR}/terraform_dependencies.txt" >> "${OUTPUT_FILE}"
        echo '```' >> "${OUTPUT_FILE}"
    else
        echo "No Terraform resources found." >> "${OUTPUT_FILE}"
    fi
    
    # Add security audit results
    echo "" >> "${OUTPUT_FILE}"
    echo "## Security Audit Results" >> "${OUTPUT_FILE}"
    
    # Python security audit
    if [[ -f "${TEMP_DIR}/python_security_audit.txt" ]]; then
        echo "" >> "${OUTPUT_FILE}"
        echo "### Python Security Audit" >> "${OUTPUT_FILE}"
        cat "${TEMP_DIR}/python_security_audit.txt" >> "${OUTPUT_FILE}"
    fi
    
    # npm audit results
    if [[ -f "${TEMP_DIR}/npm_audit.txt" ]]; then
        echo "" >> "${OUTPUT_FILE}"
        echo "### Node.js Security Audit" >> "${OUTPUT_FILE}"
        cat "${TEMP_DIR}/npm_audit.txt" >> "${OUTPUT_FILE}"
    fi
    
    # License check results
    if [[ -f "${TEMP_DIR}/license_check.txt" ]]; then
        echo "" >> "${OUTPUT_FILE}"
        echo "## License Information" >> "${OUTPUT_FILE}"
        cat "${TEMP_DIR}/license_check.txt" >> "${OUTPUT_FILE}"
    fi
    
    # Add recommendations
    cat >> "${OUTPUT_FILE}" << 'EOF'

## Recommendations

1. **Regular Updates:** Keep all dependencies updated to their latest stable versions
2. **Security Monitoring:** Set up automated security scanning in CI/CD pipeline
3. **License Compliance:** Review all licenses for compatibility with your project
4. **Vulnerability Management:** Address any identified CVEs promptly
5. **Documentation:** Maintain up-to-date dependency documentation

## Next Steps

1. Review all identified vulnerabilities
2. Update vulnerable packages to safe versions
3. Verify license compatibility
4. Implement automated dependency scanning
5. Schedule regular dependency audits

---
*This report was generated by the automated dependency audit script.*
EOF
    
    success "Dependency audit report generated: ${OUTPUT_FILE}"
}

# Function to clean up temporary files
cleanup() {
    log "Cleaning up temporary files..."
    # Keep the main results but clean up working files
    rm -f "${TEMP_DIR}"/*.tmp 2>/dev/null || true
}

# Main function
main() {
    log "Starting comprehensive dependency audit..."
    
    # Install required tools
    install_audit_tools
    
    # Consolidate dependencies
    consolidate_python_requirements
    extract_cpp_dependencies
    extract_docker_images
    extract_terraform_amis
    
    # Run security audits
    run_python_security_audit
    run_npm_audit
    
    # Run license check
    run_license_check
    
    # Generate final report
    generate_audit_report
    
    # Clean up
    cleanup
    
    success "Dependency audit completed successfully!"
    success "Report available at: ${OUTPUT_FILE}"
    
    # Display summary
    echo ""
    echo "=== AUDIT SUMMARY ==="
    echo "Report location: ${OUTPUT_FILE}"
    echo "Temporary files: ${TEMP_DIR}"
    echo "Python requirements: ${CONSOLIDATED_REQUIREMENTS}"
    echo ""
    echo "Next steps:"
    echo "1. Review the generated report"
    echo "2. Address any security vulnerabilities"
    echo "3. Verify license compliance"
    echo "4. Update dependencies as needed"
}

# Trap for cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
