#!/bin/bash


# =============================================================================
# ALB Controller OIDC Provider and Service Account Setup Script
# =============================================================================
# This script ensures the IAM OIDC provider is enabled for the EKS cluster
# and creates the necessary IAM role and Kubernetes service account for the
# AWS Load Balancer Controller.
# 
# The script:
# 1. Sources environment variables from eks-alb.env
# 2. Enables IAM OIDC provider for the cluster if not present
# 3. Creates IAM role with trust relationship to OIDC
# 4. Attaches the policy ARN from step 1 to the role
# 5. Creates Kubernetes service account with IAM role annotation
# =============================================================================

set -euo pipefail

# Get the script directory
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# Load environment variables from env/eks-alb.env
ENV_FILE="$SCRIPT_DIR/env/eks-alb.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] Environment file not found at $ENV_FILE" >&2
    exit 1
fi

source "$ENV_FILE"

# Set default values if not provided in env file
AWS_PROFILE="${AWS_PROFILE:-default}"
ROLE_NAME="${ALB_ROLE_NAME:-AmazonEKSLoadBalancerControllerRole}"
SERVICE_ACCOUNT_NAME="${ALB_SERVICE_ACCOUNT_NAME:-aws-load-balancer-controller}"
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
if [[ -z "${CLUSTER_NAME:-}" ]]; then
    error "CLUSTER_NAME is not set in env/eks-alb.env"
fi

if [[ -z "${AWS_REGION:-}" ]]; then
    error "AWS_REGION is not set in env/eks-alb.env"
fi

if [[ -z "${K8S_NAMESPACE:-}" ]]; then
    error "K8S_NAMESPACE is not set in env/eks-alb.env"
fi

if [[ -z "${ACCOUNT_ID:-}" ]]; then
    error "ACCOUNT_ID is not set in env/eks-alb.env"
fi

# Check if policy ARN file exists from previous step
if [[ ! -f "$POLICY_ARN_FILE" ]]; then
    error "Policy ARN file not found: $POLICY_ARN_FILE. Please run 01-create-iam-policy.sh first."
fi

POLICY_ARN=$(cat "$POLICY_ARN_FILE")
if [[ -z "$POLICY_ARN" ]]; then
    error "Policy ARN is empty in $POLICY_ARN_FILE"
fi

log "Starting ALB Controller OIDC and Service Account setup..."

# Step 1: Enable IAM OIDC provider for the cluster if not present
log "Checking if IAM OIDC provider is enabled for cluster '$CLUSTER_NAME'..."

# Get the OIDC issuer URL
OIDC_ISSUER_URL=$(aws eks describe-cluster \
    --name "$CLUSTER_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "cluster.identity.oidc.issuer" \
    --output text 2>/dev/null || echo "")

if [[ -z "$OIDC_ISSUER_URL" ]]; then
    error "Failed to get OIDC issuer URL for cluster '$CLUSTER_NAME'"
fi

# Extract the OIDC ID from the issuer URL
OIDC_ID=$(echo "$OIDC_ISSUER_URL" | cut -d'/' -f5)

# Check if OIDC provider already exists
EXISTING_OIDC=$(aws iam list-open-id-connect-providers \
    --profile "$AWS_PROFILE" \
    --query "OpenIDConnectProviderList[?contains(Arn, '$OIDC_ID')].Arn" \
    --output text 2>/dev/null || echo "")

if [[ -n "$EXISTING_OIDC" ]]; then
    success "IAM OIDC provider already exists: $EXISTING_OIDC"
else
    log "Creating IAM OIDC provider for cluster '$CLUSTER_NAME'..."
    if eksctl utils associate-iam-oidc-provider \
        --cluster "$CLUSTER_NAME" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --approve 2>/dev/null; then
        success "IAM OIDC provider created successfully"
    else
        error "Failed to create IAM OIDC provider"
    fi
fi

# Step 2: Create IAM role with trust relationship to OIDC
log "Creating IAM role '$ROLE_NAME' with OIDC trust relationship..."

# Create trust policy document
TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_ISSUER_URL#https://}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${OIDC_ISSUER_URL#https://}:aud": "sts.amazonaws.com",
          "${OIDC_ISSUER_URL#https://}:sub": "system:serviceaccount:${K8S_NAMESPACE}:${SERVICE_ACCOUNT_NAME}"
        }
      }
    }
  ]
}
EOF
)

# Check if role already exists
EXISTING_ROLE_ARN=$(aws iam get-role \
    --role-name "$ROLE_NAME" \
    --profile "$AWS_PROFILE" \
    --query 'Role.Arn' \
    --output text 2>/dev/null || echo "")

if [[ -n "$EXISTING_ROLE_ARN" ]]; then
    warning "IAM role '$ROLE_NAME' already exists with ARN: $EXISTING_ROLE_ARN"
    
    # Update the trust policy
    log "Updating trust policy for existing role..."
    aws iam update-assume-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-document "$TRUST_POLICY" \
        --profile "$AWS_PROFILE" 2>/dev/null || error "Failed to update trust policy"
    
    ROLE_ARN="$EXISTING_ROLE_ARN"
else
    # Create new role
    log "Creating new IAM role '$ROLE_NAME'..."
    ROLE_ARN=$(aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document "$TRUST_POLICY" \
        --description "IAM role for AWS Load Balancer Controller" \
        --profile "$AWS_PROFILE" \
        --query 'Role.Arn' \
        --output text 2>/dev/null || echo "")
    
    if [[ -z "$ROLE_ARN" ]]; then
        error "Failed to create IAM role '$ROLE_NAME'"
    fi
    
    success "Created new IAM role '$ROLE_NAME' with ARN: $ROLE_ARN"
fi

# Step 3: Attach the policy ARN to the role
log "Attaching policy '$POLICY_ARN' to role '$ROLE_NAME'..."

# Check if policy is already attached
ATTACHED_POLICIES=$(aws iam list-attached-role-policies \
    --role-name "$ROLE_NAME" \
    --profile "$AWS_PROFILE" \
    --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" \
    --output text 2>/dev/null || echo "")

if [[ -n "$ATTACHED_POLICIES" ]]; then
    success "Policy is already attached to role"
else
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "$POLICY_ARN" \
        --profile "$AWS_PROFILE" 2>/dev/null || error "Failed to attach policy to role"
    
    success "Policy attached to role successfully"
fi

# Step 4: Create Kubernetes service account with IAM role annotation
log "Creating Kubernetes service account '$SERVICE_ACCOUNT_NAME' in namespace '$K8S_NAMESPACE'..."

# Create service account YAML
SERVICE_ACCOUNT_YAML=$(cat <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${SERVICE_ACCOUNT_NAME}
  namespace: ${K8S_NAMESPACE}
  annotations:
    eks.amazonaws.com/role-arn: ${ROLE_ARN}
EOF
)

# Apply service account using kubectl for idempotence
if echo "$SERVICE_ACCOUNT_YAML" | kubectl apply -f - 2>/dev/null; then
    success "Kubernetes service account '$SERVICE_ACCOUNT_NAME' created/updated successfully"
else
    error "Failed to create Kubernetes service account"
fi

# Display summary information
log "Setup Summary:"
echo "  Cluster Name:         $CLUSTER_NAME"
echo "  AWS Region:           $AWS_REGION"
echo "  K8s Namespace:        $K8S_NAMESPACE"
echo "  IAM Role Name:        $ROLE_NAME"
echo "  IAM Role ARN:         $ROLE_ARN"
echo "  Policy ARN:           $POLICY_ARN"
echo "  Service Account Name: $SERVICE_ACCOUNT_NAME"
echo "  OIDC Issuer URL:      $OIDC_ISSUER_URL"

success "ALB Controller OIDC and Service Account setup completed successfully!"
