#!/bin/bash

# Security & Compliance Gate Script
# This script runs security scans on the repository to identify HIGH/CRITICAL issues

set -e

REPO_ROOT="/home/quantium/labs/oriane/ExtractionPipeline"
CURRENT_DIR="/home/quantium/labs/oriane/ExtractionPipeline/api/search"
TERRAFORM_DIR="/home/quantium/labs/oriane/ExtractionPipeline/terraform"

echo "🔒 Starting Security & Compliance Gate Checks"
echo "============================================="

# Check if tools are installed
echo "🔍 Checking for required security tools..."

# Check for Trivy
if ! command -v trivy &> /dev/null; then
    echo "❌ Trivy not found. Installing..."
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
fi

# Check for Checkov
if ! command -v checkov &> /dev/null; then
    echo "❌ Checkov not found. Installing..."
    pip3 install checkov
fi

echo "✅ Security tools check complete"
echo ""

# 1. Run Trivy filesystem scan on the entire repository
echo "🔍 Running Trivy filesystem scan..."
echo "====================================="

trivy fs "$REPO_ROOT" \
    --format table \
    --severity HIGH,CRITICAL \
    --exit-code 1 \
    --no-progress \
    --ignore-unfixed \
    --output trivy-fs-report.txt

TRIVY_EXIT_CODE=$?

if [ $TRIVY_EXIT_CODE -eq 0 ]; then
    echo "✅ Trivy filesystem scan passed - No HIGH/CRITICAL vulnerabilities found"
else
    echo "❌ Trivy filesystem scan failed - HIGH/CRITICAL vulnerabilities detected"
    echo "📄 Full report saved to: trivy-fs-report.txt"
fi

echo ""

# 2. Run Checkov on Terraform files if they exist
echo "🔍 Running Checkov on Infrastructure as Code..."
echo "==============================================="

if [ -d "$TERRAFORM_DIR" ]; then
    echo "📁 Found Terraform files in: $TERRAFORM_DIR"
    
    checkov -d "$TERRAFORM_DIR" \
        --framework terraform \
        --severity HIGH,CRITICAL \
        --compact \
        --output cli \
        --output-file-path checkov-terraform-report.txt \
        --exit-code-from json
    
    CHECKOV_TERRAFORM_EXIT_CODE=$?
    
    if [ $CHECKOV_TERRAFORM_EXIT_CODE -eq 0 ]; then
        echo "✅ Checkov Terraform scan passed - No HIGH/CRITICAL issues found"
    else
        echo "❌ Checkov Terraform scan failed - HIGH/CRITICAL issues detected"
        echo "📄 Full report saved to: checkov-terraform-report.txt"
    fi
else
    echo "ℹ️  No Terraform directory found, skipping Terraform checks"
    CHECKOV_TERRAFORM_EXIT_CODE=0
fi

echo ""

# Check for CloudFormation files
echo "🔍 Checking for CloudFormation files..."
CF_FILES=$(find "$REPO_ROOT" -name "*.template" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" | grep -i cloudformation || true)

if [ -n "$CF_FILES" ]; then
    echo "📁 Found CloudFormation files:"
    echo "$CF_FILES"
    
    for file in $CF_FILES; do
        checkov -f "$file" \
            --framework cloudformation \
            --severity HIGH,CRITICAL \
            --compact \
            --output cli \
            --output-file-path "checkov-cf-$(basename "$file")-report.txt" \
            --exit-code-from json
        
        CF_EXIT_CODE=$?
        
        if [ $CF_EXIT_CODE -ne 0 ]; then
            echo "❌ CloudFormation file $file has HIGH/CRITICAL issues"
            CHECKOV_CF_EXIT_CODE=1
        fi
    done
    
    if [ ${CHECKOV_CF_EXIT_CODE:-0} -eq 0 ]; then
        echo "✅ Checkov CloudFormation scan passed - No HIGH/CRITICAL issues found"
    fi
else
    echo "ℹ️  No CloudFormation files found, skipping CloudFormation checks"
    CHECKOV_CF_EXIT_CODE=0
fi

echo ""

# 3. Run Checkov on Kubernetes manifests
echo "🔍 Running Checkov on Kubernetes manifests..."
echo "============================================="

K8S_FILES=$(find "$REPO_ROOT" -path "*/k8s/*" -name "*.yaml" -o -path "*/k8s/*" -name "*.yml" || true)

if [ -n "$K8S_FILES" ]; then
    echo "📁 Found Kubernetes manifest files"
    
    checkov -f $K8S_FILES \
        --framework kubernetes \
        --severity HIGH,CRITICAL \
        --compact \
        --output cli \
        --output-file-path checkov-k8s-report.txt \
        --exit-code-from json
    
    CHECKOV_K8S_EXIT_CODE=$?
    
    if [ $CHECKOV_K8S_EXIT_CODE -eq 0 ]; then
        echo "✅ Checkov Kubernetes scan passed - No HIGH/CRITICAL issues found"
    else
        echo "❌ Checkov Kubernetes scan failed - HIGH/CRITICAL issues detected"
        echo "📄 Full report saved to: checkov-k8s-report.txt"
    fi
else
    echo "ℹ️  No Kubernetes manifest files found, skipping Kubernetes checks"
    CHECKOV_K8S_EXIT_CODE=0
fi

echo ""

# 4. OPA Gatekeeper test constraints (optional)
echo "🔍 OPA Gatekeeper test constraints (optional)..."
echo "==============================================="

if command -v opa &> /dev/null; then
    echo "✅ OPA found, running policy tests..."
    
    # Look for OPA policies in the repository
    OPA_POLICIES=$(find "$REPO_ROOT" -name "*.rego" || true)
    
    if [ -n "$OPA_POLICIES" ]; then
        echo "📁 Found OPA policies:"
        echo "$OPA_POLICIES"
        
        # Test OPA policies
        for policy in $OPA_POLICIES; do
            echo "Testing policy: $policy"
            opa test "$policy" || echo "⚠️  Warning: Policy test failed for $policy"
        done
    else
        echo "ℹ️  No OPA policies found in repository"
    fi
else
    echo "ℹ️  OPA not installed, skipping OPA Gatekeeper tests (optional)"
fi

echo ""

# Summary
echo "📊 Security & Compliance Gate Summary"
echo "====================================="

OVERALL_EXIT_CODE=0

if [ $TRIVY_EXIT_CODE -ne 0 ]; then
    echo "❌ Trivy filesystem scan: FAILED (HIGH/CRITICAL vulnerabilities found)"
    OVERALL_EXIT_CODE=1
else
    echo "✅ Trivy filesystem scan: PASSED"
fi

if [ ${CHECKOV_TERRAFORM_EXIT_CODE:-0} -ne 0 ]; then
    echo "❌ Checkov Terraform scan: FAILED (HIGH/CRITICAL issues found)"
    OVERALL_EXIT_CODE=1
else
    echo "✅ Checkov Terraform scan: PASSED"
fi

if [ ${CHECKOV_CF_EXIT_CODE:-0} -ne 0 ]; then
    echo "❌ Checkov CloudFormation scan: FAILED (HIGH/CRITICAL issues found)"
    OVERALL_EXIT_CODE=1
else
    echo "✅ Checkov CloudFormation scan: PASSED"
fi

if [ ${CHECKOV_K8S_EXIT_CODE:-0} -ne 0 ]; then
    echo "❌ Checkov Kubernetes scan: FAILED (HIGH/CRITICAL issues found)"
    OVERALL_EXIT_CODE=1
else
    echo "✅ Checkov Kubernetes scan: PASSED"
fi

echo ""

if [ $OVERALL_EXIT_CODE -eq 0 ]; then
    echo "🎉 SECURITY & COMPLIANCE GATE: PASSED"
    echo "   No HIGH/CRITICAL security issues found. Deployment can proceed."
else
    echo "🚨 SECURITY & COMPLIANCE GATE: FAILED"
    echo "   HIGH/CRITICAL security issues detected. Deployment is BLOCKED."
    echo "   Please review the generated reports and fix the issues before proceeding."
fi

echo ""
echo "📄 Generated reports:"
echo "   - trivy-fs-report.txt (Trivy filesystem scan)"
echo "   - checkov-*-report.txt (Checkov infrastructure scans)"

exit $OVERALL_EXIT_CODE
