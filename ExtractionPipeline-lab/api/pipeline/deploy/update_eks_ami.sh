#!/bin/bash


# =============================================================================
# EKS AMI Update Helper Script
# =============================================================================
# This script updates the EKS version and AMI family in the deploy_to_eks.sh 
# script and commits the changes to version control.
# 
# Usage:
#   ./scripts/update_eks_ami.sh --eks-version 1.33 --ami-family AmazonLinux2023
#   ./scripts/update_eks_ami.sh --eks-version 1.32 --ami-family AmazonLinux2
# 
# Flags:
#   --eks-version    Target EKS version (e.g., 1.33, 1.32)
#   --ami-family     AMI family to use (AmazonLinux2023, AmazonLinux2)
# 
# The script will:
# 1. Validate the provided arguments
# 2. Update the deploy_to_eks.sh script in-place using sed
# 3. Commit the changes to git with a descriptive message
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script variables
EKS_VERSION=""
AMI_FAMILY=""
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_SCRIPT="$PROJECT_ROOT/deploy_to_eks.sh"

# Function to display usage
usage() {
    echo "Usage: $0 --eks-version <version> --ami-family <family>"
    echo ""
    echo "Options:"
    echo "  --eks-version    Target EKS version (e.g., 1.33, 1.32)"
    echo "  --ami-family     AMI family to use (AmazonLinux2023, AmazonLinux2)"
    echo ""
    echo "Examples:"
    echo "  $0 --eks-version 1.33 --ami-family AmazonLinux2023"
    echo "  $0 --eks-version 1.32 --ami-family AmazonLinux2"
    exit 1
}

# Function for logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --eks-version)
            EKS_VERSION="$2"
            shift 2
            ;;
        --ami-family)
            AMI_FAMILY="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$EKS_VERSION" || -z "$AMI_FAMILY" ]]; then
    error "Both --eks-version and --ami-family are required."
fi

# Validate EKS version format
if [[ ! "$EKS_VERSION" =~ ^[0-9]+\.[0-9]+$ ]]; then
    error "EKS version must be in format X.Y (e.g., 1.33)"
fi

# Validate AMI family
if [[ "$AMI_FAMILY" != "AmazonLinux2023" && "$AMI_FAMILY" != "AmazonLinux2" ]]; then
    error "AMI family must be either 'AmazonLinux2023' or 'AmazonLinux2'"
fi

# Check if deploy script exists
if [[ ! -f "$DEPLOY_SCRIPT" ]]; then
    error "Deploy script not found at: $DEPLOY_SCRIPT"
fi

# Validate EKS version and AMI family compatibility
if [[ "$AMI_FAMILY" == "AmazonLinux2" && "$EKS_VERSION" == "1.33" ]]; then
    error "Amazon Linux 2 GPU AMIs are not available for EKS 1.33. Please use AmazonLinux2023."
fi

# Check if git is available and we're in a git repository
if ! command -v git &> /dev/null; then
    error "Git is not installed or not available in PATH"
fi

if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    error "Not inside a git repository"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    warning "There are uncommitted changes in the repository."
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

log "Starting EKS AMI update process..."
log "EKS Version: $EKS_VERSION"
log "AMI Family: $AMI_FAMILY"
log "Deploy Script: $DEPLOY_SCRIPT"

# Create a backup of the original file
cp "$DEPLOY_SCRIPT" "$DEPLOY_SCRIPT.backup"
log "Created backup: $DEPLOY_SCRIPT.backup"

# Update the EKS version in the deploy script
# Look for lines that set EKS_VERSION or reference it in validation
if grep -q "EKS_VERSION" "$DEPLOY_SCRIPT"; then
    # Update any EKS_VERSION references in comments or validation
    sed -i "s/EKS [0-9]\+\.[0-9]\+/EKS $EKS_VERSION/g" "$DEPLOY_SCRIPT"
    sed -i "s/EKS version [0-9]\+\.[0-9]\+/EKS version $EKS_VERSION/g" "$DEPLOY_SCRIPT"
    success "Updated EKS version references to $EKS_VERSION"
else
    warning "No EKS_VERSION references found in deploy script"
fi

# Update the AMI family default value
if grep -q "AMI_FAMILY=" "$DEPLOY_SCRIPT"; then
    sed -i "s/AMI_FAMILY=\"\${AMI_FAMILY:-[^}]*}\"/AMI_FAMILY=\"\${AMI_FAMILY:-$AMI_FAMILY}\"/g" "$DEPLOY_SCRIPT"
    success "Updated AMI_FAMILY default to $AMI_FAMILY"
else
    warning "No AMI_FAMILY default found in deploy script"
fi

# Update AMI path references if they exist
if grep -q "amazon-linux-2023" "$DEPLOY_SCRIPT"; then
    if [[ "$AMI_FAMILY" == "AmazonLinux2" ]]; then
        sed -i "s/amazon-linux-2023/amazon-linux-2/g" "$DEPLOY_SCRIPT"
        success "Updated AMI path references to amazon-linux-2"
    fi
elif grep -q "amazon-linux-2" "$DEPLOY_SCRIPT"; then
    if [[ "$AMI_FAMILY" == "AmazonLinux2023" ]]; then
        sed -i "s/amazon-linux-2/amazon-linux-2023/g" "$DEPLOY_SCRIPT"
        success "Updated AMI path references to amazon-linux-2023"
    fi
fi

# Update the version in the SSM parameter path
sed -i "s|/aws/service/eks/optimized-ami/[0-9]\+\.[0-9]\+/|/aws/service/eks/optimized-ami/$EKS_VERSION/|g" "$DEPLOY_SCRIPT"
success "Updated SSM parameter path to use EKS version $EKS_VERSION"

# Update optimized for EKS version comment
sed -i "s/Optimized for EKS [0-9]\+\.[0-9]\+/Optimized for EKS $EKS_VERSION/g" "$DEPLOY_SCRIPT"

# Verify the changes were applied
log "Verifying changes..."
if grep -q "AMI_FAMILY.*$AMI_FAMILY" "$DEPLOY_SCRIPT" && grep -q "optimized-ami/$EKS_VERSION/" "$DEPLOY_SCRIPT"; then
    success "Changes applied successfully"
else
    error "Changes verification failed. Restoring backup..."
    mv "$DEPLOY_SCRIPT.backup" "$DEPLOY_SCRIPT"
    exit 1
fi

# Show the changes made
log "Changes made:"
git diff "$DEPLOY_SCRIPT" || true

# Commit the changes
COMMIT_MSG="Update EKS to version $EKS_VERSION with $AMI_FAMILY AMI family

- Updated EKS version from previous to $EKS_VERSION
- Updated AMI family to $AMI_FAMILY
- Updated SSM parameter paths for AMI discovery
- Automated update via update_eks_ami.sh script"

git add "$DEPLOY_SCRIPT"
git commit -m "$COMMIT_MSG"
success "Changes committed to git"

# Clean up backup
rm -f "$DEPLOY_SCRIPT.backup"

log "EKS AMI update completed successfully!"
log "Summary:"
log "  ✓ EKS version updated to: $EKS_VERSION"
log "  ✓ AMI family updated to: $AMI_FAMILY"
log "  ✓ Changes committed to git"
log "  ✓ Deploy script is ready for use"
