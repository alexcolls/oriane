#!/bin/bash

# =============================================================================
# KinD Cluster Cleanup Script for Search API
# =============================================================================
# This script cleans up the KinD cluster and associated resources
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLUSTER_NAME="search-api-test"

echo "=== KinD Cluster Cleanup for Search API ==="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if KinD is installed
if ! command_exists kind; then
    echo "KinD is not installed, nothing to cleanup"
    exit 0
fi

# Check if cluster exists
if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo "Cluster '${CLUSTER_NAME}' does not exist"
else
    echo "Deleting KinD cluster: ${CLUSTER_NAME}"
    kind delete cluster --name "${CLUSTER_NAME}"
fi

# Clean up Docker images
echo "Cleaning up Docker images..."
docker image rm search-api:latest 2>/dev/null || echo "Image search-api:latest not found"

# Clean up configuration files
echo "Cleaning up configuration files..."
rm -f "${PROJECT_ROOT}/kind-config.yaml"

# Clean up kubectl context
echo "Cleaning up kubectl context..."
kubectl config delete-context "kind-${CLUSTER_NAME}" 2>/dev/null || echo "Context not found"

# Prune Docker system (optional)
read -p "Do you want to prune Docker system (remove unused containers, networks, images)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Pruning Docker system..."
    docker system prune -f
fi

echo ""
echo "✓ Cleanup complete!"
echo "All KinD cluster resources for search API have been removed."
