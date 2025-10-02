#!/bin/bash

# Pipeline CI Test Environment Setup Script
# This script defines and exports all required variables for subsequent steps

echo "Setting up Pipeline CI Test Environment..."

# AWS Configuration
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_PROFILE="${AWS_PROFILE:-default}"

# Note: If using explicit credentials instead of AWS_PROFILE, uncomment and set:
# export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
# export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"

# ECR Configuration
# Replace 123456789012 with your actual AWS account ID
export ECR_URI="${ECR_URI:-123456789012.dkr.ecr.us-east-1.amazonaws.com}"

# Kubernetes Configuration
export CLUSTER_NAME="${CLUSTER_NAME:-pipeline-test-cluster}"
export K8S_NAMESPACE="pipeline"

# Repository root path (absolute path)
export REPO_ROOT="/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline"

# Artifacts directory for logs
export ARTIFACTS_DIR="/tmp/pipeline-ci-artifacts"

# Python command (enforce python3 usage)
export PYTHON_CMD="python3"

# Display configured variables
echo "Environment variables configured:"
echo "  AWS_REGION: $AWS_REGION"
echo "  AWS_PROFILE: $AWS_PROFILE"
echo "  ECR_URI: $ECR_URI"
echo "  CLUSTER_NAME: $CLUSTER_NAME"
echo "  K8S_NAMESPACE: $K8S_NAMESPACE"
echo "  REPO_ROOT: $REPO_ROOT"
echo "  ARTIFACTS_DIR: $ARTIFACTS_DIR"
echo "  PYTHON_CMD: $PYTHON_CMD"

# Create artifacts directory
echo "Creating artifacts directory: $ARTIFACTS_DIR"
mkdir -p "$ARTIFACTS_DIR"

if [ -d "$ARTIFACTS_DIR" ]; then
    echo "✓ Artifacts directory created successfully"
else
    echo "✗ Failed to create artifacts directory"
    exit 1
fi

# Verify python3 is available
if command -v python3 &> /dev/null; then
    echo "✓ python3 is available: $(which python3)"
    echo "✓ Python version: $(python3 --version)"
else
    echo "✗ python3 is not available in PATH"
    exit 1
fi

echo "Environment setup complete!"
echo ""
echo "To use these variables in your current shell, run:"
echo "  source setup-env.sh"
echo ""
echo "Or for other scripts, ensure they source this file:"
echo "  source /home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/setup-env.sh"
