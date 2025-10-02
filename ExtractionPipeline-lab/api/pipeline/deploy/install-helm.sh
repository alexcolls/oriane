#!/bin/bash


# =============================================================================
# Helm Installation Script for ALB Controller Deployment
# =============================================================================
# This script installs Helm 3 on Ubuntu/Linux systems, which is required
# for deploying the AWS Load Balancer Controller via Helm charts.
# =============================================================================

set -euo pipefail

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

# Check if Helm is already installed
if command -v helm &> /dev/null; then
    HELM_VERSION=$(helm version --short 2>/dev/null || echo "unknown")
    warning "Helm is already installed: $HELM_VERSION"
    
    # Check if it's Helm 3.x
    if helm version --short | grep -q "v3\." 2>/dev/null; then
        success "Helm 3.x is already installed and ready to use"
        exit 0
    else
        warning "Helm 2.x detected. Will install Helm 3.x alongside"
    fi
fi

log "Starting Helm 3 installation..."

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case $ARCH in
    x86_64)
        ARCH="amd64"
        ;;
    aarch64)
        ARCH="arm64"
        ;;
    armv7l)
        ARCH="arm"
        ;;
    *)
        error "Unsupported architecture: $ARCH"
        ;;
esac

log "Detected OS: $OS, Architecture: $ARCH"

# Set Helm version and download URL
HELM_VERSION="v3.13.3"
HELM_FILENAME="helm-${HELM_VERSION}-${OS}-${ARCH}.tar.gz"
HELM_URL="https://get.helm.sh/${HELM_FILENAME}"

log "Downloading Helm ${HELM_VERSION}..."

# Create temporary directory
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

# Download Helm
if ! curl -fsSL "$HELM_URL" -o "$HELM_FILENAME"; then
    error "Failed to download Helm from $HELM_URL"
fi

success "Downloaded Helm ${HELM_VERSION}"

# Extract and install
log "Extracting and installing Helm..."
tar -zxf "$HELM_FILENAME"

# Move to /usr/local/bin
if ! sudo mv "${OS}-${ARCH}/helm" /usr/local/bin/helm; then
    error "Failed to install Helm to /usr/local/bin/helm"
fi

# Set permissions
sudo chmod +x /usr/local/bin/helm

# Clean up
cd - > /dev/null
rm -rf "$TMP_DIR"

# Verify installation
if ! command -v helm &> /dev/null; then
    error "Helm installation failed - command not found"
fi

INSTALLED_VERSION=$(helm version --short 2>/dev/null || echo "unknown")
success "Helm installed successfully: $INSTALLED_VERSION"

# Add EKS repository (commonly needed for ALB controller)
log "Adding EKS Helm repository..."
if helm repo add eks https://aws.github.io/eks-charts 2>/dev/null; then
    success "EKS Helm repository added"
else
    warning "Failed to add EKS repository (may already exist)"
fi

# Update repositories
log "Updating Helm repositories..."
if helm repo update 2>/dev/null; then
    success "Helm repositories updated"
else
    warning "Failed to update repositories"
fi

# Display installation summary
log "Installation Summary:"
echo "  Helm Version:     $INSTALLED_VERSION"
echo "  Installation Path: /usr/local/bin/helm"
echo "  OS/Architecture:  $OS/$ARCH"

success "Helm installation completed successfully!"
