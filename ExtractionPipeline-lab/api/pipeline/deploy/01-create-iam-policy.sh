#!/bin/bash


# =============================================================================
# ALB Controller IAM Policy Setup Script
# =============================================================================
# This script creates the IAM policy required for the AWS Load Balancer Controller
# to manage Application Load Balancers in EKS clusters.
# 
# The script:
# 1. Sources environment variables from .env file
# 2. Downloads the official AWS Load Balancer Controller IAM policy
# 3. Creates or updates the IAM policy
# 4. Stores the policy ARN for later use
# =============================================================================

set -euo pipefail

# Get the script directory
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env file
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    ENV_FILE="$PROJECT_ROOT/.env"
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] .env file not found at $SCRIPT_DIR/.env or $PROJECT_ROOT/.env" >&2
    exit 1
fi

source "$ENV_FILE"

# Set default values if not provided in .env
AWS_PROFILE="${AWS_PROFILE:-default}"
POLICY_NAME="${ALB_POLICY_NAME:-AWSLoadBalancerControllerIAMPolicy}"
POLICY_FILE="$SCRIPT_DIR/alb-iam-policy.json"
POLICY_ARN_FILE="$SCRIPT_DIR/alb-policy-arn.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

# Validate required environment variables
if [[ -z "${AWS_REGION:-}" ]]; then
    error "AWS_REGION is not set in .env file"
fi

# Official AWS Load Balancer Controller IAM policy URL
POLICY_URL="https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.8.1/docs/install/iam_policy.json"

log "Starting ALB Controller IAM Policy setup..."

# Download the official IAM policy
log "Downloading official AWS Load Balancer Controller IAM policy..."
if ! curl -s -o "$POLICY_FILE" "$POLICY_URL"; then
    error "Failed to download IAM policy from $POLICY_URL"
fi

# Verify the policy file was downloaded and is valid JSON
if [[ ! -f "$POLICY_FILE" ]]; then
    error "Policy file was not created: $POLICY_FILE"
fi

if ! python3 -m json.tool "$POLICY_FILE" > /dev/null 2>&1; then
    error "Downloaded policy file is not valid JSON: $POLICY_FILE"
fi

success "Downloaded IAM policy to $POLICY_FILE"

# Check if policy already exists
log "Checking if IAM policy '$POLICY_NAME' already exists..."
EXISTING_POLICY_ARN=$(aws iam list-policies \
    --scope Local \
    --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" \
    --output text \
    --profile "$AWS_PROFILE" 2>/dev/null || echo "")

if [[ -n "$EXISTING_POLICY_ARN" ]]; then
    warning "IAM policy '$POLICY_NAME' already exists with ARN: $EXISTING_POLICY_ARN"
    
    # Update the existing policy by creating a new version
    log "Creating new version of existing policy..."
    NEW_VERSION=$(aws iam create-policy-version \
        --policy-arn "$EXISTING_POLICY_ARN" \
        --policy-document "file://$POLICY_FILE" \
        --set-as-default \
        --query 'PolicyVersion.VersionId' \
        --output text \
        --profile "$AWS_PROFILE" 2>/dev/null || echo "")
    
    if [[ -n "$NEW_VERSION" ]]; then
        success "Updated IAM policy to version $NEW_VERSION"
        POLICY_ARN="$EXISTING_POLICY_ARN"
    else
        warning "Failed to update policy version, using existing policy"
        POLICY_ARN="$EXISTING_POLICY_ARN"
    fi
else
    # Create new policy
    log "Creating new IAM policy '$POLICY_NAME'..."
    POLICY_ARN=$(aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "file://$POLICY_FILE" \
        --description "IAM policy for AWS Load Balancer Controller" \
        --query 'Policy.Arn' \
        --output text \
        --profile "$AWS_PROFILE" 2>/dev/null || echo "")
    
    if [[ -z "$POLICY_ARN" ]]; then
        error "Failed to create IAM policy '$POLICY_NAME'"
    fi
    
    success "Created new IAM policy '$POLICY_NAME' with ARN: $POLICY_ARN"
fi

# Store the policy ARN for later use
echo "$POLICY_ARN" > "$POLICY_ARN_FILE"
success "Policy ARN stored in $POLICY_ARN_FILE"

# Display policy information
log "Policy Information:"
echo "  Policy Name: $POLICY_NAME"
echo "  Policy ARN:  $POLICY_ARN"
echo "  Policy File: $POLICY_FILE"
echo "  ARN File:    $POLICY_ARN_FILE"

# Clean up downloaded policy file (optional)
if [[ "${CLEANUP_POLICY_FILE:-true}" == "true" ]]; then
    log "Cleaning up downloaded policy file..."
    rm -f "$POLICY_FILE"
fi

success "ALB Controller IAM Policy setup completed successfully!"
