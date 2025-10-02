#!/bin/bash

# =============================================================================
# Create Oriane AI Cluster - EKS Setup Script
# =============================================================================
# This script creates a new EKS cluster named "oriane-ai-cluster" and 
# optionally deletes the old cluster
# =============================================================================

set -euo pipefail

# Configuration
CLUSTER_NAME="oriane-ai-cluster"
OLD_CLUSTER_NAME="oriane-search-api-cluster"
AWS_REGION="us-east-1"
CLUSTER_VERSION="1.28"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if eksctl is available
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v eksctl &> /dev/null; then
        log_error "eksctl is not installed. Installing..."
        curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
        sudo mv /tmp/eksctl /usr/local/bin
    fi
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create cluster configuration
create_cluster_config() {
    log_info "Creating cluster configuration..."
    
    cat > cluster-config.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: ${CLUSTER_NAME}
  region: ${AWS_REGION}
  version: "${CLUSTER_VERSION}"

vpc:
  cidr: "10.0.0.0/16"
  nat:
    gateway: Single
  clusterEndpoints:
    publicAccess: true
    privateAccess: true

cloudWatch:
  clusterLogging:
    enableTypes: ["*"]

addons:
  - name: vpc-cni
    version: latest
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest
  - name: aws-ebs-csi-driver
    version: latest

managedNodeGroups:
  - name: system-nodes
    instanceType: t3.medium
    minSize: 2
    maxSize: 4
    desiredCapacity: 2
    volumeSize: 50
    ssh:
      enableSsm: true
    labels:
      node-type: system
    tags:
      k8s.io/cluster-autoscaler/enabled: "true"
      k8s.io/cluster-autoscaler/${CLUSTER_NAME}: "owned"

  - name: api-nodes
    instanceType: t3.large
    minSize: 1
    maxSize: 6
    desiredCapacity: 2
    volumeSize: 100
    ssh:
      enableSsm: true
    labels:
      node-type: api
    tags:
      k8s.io/cluster-autoscaler/enabled: "true"
      k8s.io/cluster-autoscaler/${CLUSTER_NAME}: "owned"

iam:
  withOIDC: true
  serviceAccounts:
    - metadata:
        name: aws-load-balancer-controller
        namespace: kube-system
      wellKnownPolicies:
        awsLoadBalancerController: true
    - metadata:
        name: cluster-autoscaler
        namespace: kube-system
      wellKnownPolicies:
        autoScaling: true
EOF

    log_success "Cluster configuration created"
}

# Create the new cluster
create_cluster() {
    log_info "Creating new EKS cluster: ${CLUSTER_NAME}"
    log_warning "This process may take 15-20 minutes..."
    
    eksctl create cluster -f cluster-config.yaml
    
    if [ $? -eq 0 ]; then
        log_success "Cluster ${CLUSTER_NAME} created successfully"
    else
        log_error "Failed to create cluster ${CLUSTER_NAME}"
        exit 1
    fi
}

# Update kubeconfig
update_kubeconfig() {
    log_info "Updating kubeconfig for new cluster..."
    
    aws eks update-kubeconfig --region ${AWS_REGION} --name ${CLUSTER_NAME}
    
    log_success "Kubeconfig updated"
}

# Verify cluster
verify_cluster() {
    log_info "Verifying cluster..."
    
    kubectl get nodes
    kubectl get pods -n kube-system
    
    log_success "Cluster verification completed"
}

# Ask about deleting old cluster
ask_delete_old_cluster() {
    echo ""
    log_warning "Do you want to delete the old cluster '${OLD_CLUSTER_NAME}'? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Deleting old cluster: ${OLD_CLUSTER_NAME}"
        eksctl delete cluster --name ${OLD_CLUSTER_NAME} --region ${AWS_REGION}
        
        if [ $? -eq 0 ]; then
            log_success "Old cluster ${OLD_CLUSTER_NAME} deleted successfully"
        else
            log_error "Failed to delete old cluster ${OLD_CLUSTER_NAME}"
        fi
    else
        log_info "Keeping old cluster ${OLD_CLUSTER_NAME}"
        log_warning "You now have two clusters running. Remember to delete the old one when ready."
    fi
}

# Main execution
main() {
    log_info "Starting EKS cluster creation process..."
    echo "New cluster name: ${CLUSTER_NAME}"
    echo "Region: ${AWS_REGION}"
    echo "Version: ${CLUSTER_VERSION}"
    echo ""
    
    check_prerequisites
    create_cluster_config
    create_cluster
    update_kubeconfig
    verify_cluster
    ask_delete_old_cluster
    
    echo ""
    log_success "EKS cluster setup completed!"
    log_info "You can now deploy your applications to the new cluster: ${CLUSTER_NAME}"
    log_info "Update your deployment scripts to use the new cluster name."
}

# Run main function
main "$@"
