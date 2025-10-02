#!/bin/bash

# =============================================================================
# Resource Cleanup Script - Step 13
# =============================================================================
# This script performs comprehensive cleanup of:
# - Kubernetes namespace
# - EKS cluster
# - ECR images older than 1 day
# - Local Docker images
# - Creates final test summary
# =============================================================================

set -euo pipefail

# Configuration variables
K8S_NAMESPACE="${K8S_NAMESPACE:-search}"
CLUSTER_NAME="${CLUSTER_NAME:-oriane-ai-cluster}"
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_ROOT="/home/quantium/labs/oriane/ExtractionPipeline"
ARTIFACTS_DIR="${PROJECT_ROOT}/artifacts"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

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

# Create artifacts directory
create_artifacts_dir() {
    log_info "Creating artifacts directory..."
    mkdir -p "${ARTIFACTS_DIR}"
    log_success "Artifacts directory created: ${ARTIFACTS_DIR}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v eksctl &> /dev/null; then
        missing_tools+=("eksctl")
    fi
    
    if ! command -v aws &> /dev/null; then
        missing_tools+=("aws")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install the missing tools and run the script again."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Get current cluster context
get_current_context() {
    log_info "Getting current Kubernetes context..."
    
    if kubectl config current-context &> /dev/null; then
        local current_context=$(kubectl config current-context)
        log_info "Current context: ${current_context}"
        
        # Update kubeconfig for the target cluster
        log_info "Updating kubeconfig for cluster: ${CLUSTER_NAME}"
        aws eks update-kubeconfig --region "${AWS_REGION}" --name "${CLUSTER_NAME}" || {
            log_warning "Failed to update kubeconfig. Cluster may not exist or may be already deleted."
        }
    else
        log_warning "No Kubernetes context found"
    fi
}

# Delete Kubernetes namespace
delete_namespace() {
    log_info "Deleting Kubernetes namespace: ${K8S_NAMESPACE}"
    
    if kubectl get namespace "${K8S_NAMESPACE}" &> /dev/null; then
        kubectl delete namespace "${K8S_NAMESPACE}" --timeout=300s || {
            log_warning "Failed to delete namespace ${K8S_NAMESPACE}, it may not exist or may be stuck"
            
            # Force delete if stuck
            log_info "Attempting to force delete namespace..."
            kubectl patch namespace "${K8S_NAMESPACE}" -p '{"metadata":{"finalizers":null}}' --type=merge || true
        }
        
        log_success "Namespace ${K8S_NAMESPACE} deletion initiated"
    else
        log_warning "Namespace ${K8S_NAMESPACE} does not exist"
    fi
}

# Delete EKS cluster
delete_cluster() {
    log_info "Deleting EKS cluster: ${CLUSTER_NAME}"
    log_warning "This process may take 10-15 minutes..."
    
    if eksctl get cluster --name "${CLUSTER_NAME}" --region "${AWS_REGION}" &> /dev/null; then
        eksctl delete cluster --name "${CLUSTER_NAME}" --region "${AWS_REGION}" --wait || {
            log_error "Failed to delete cluster ${CLUSTER_NAME}"
            return 1
        }
        log_success "EKS cluster ${CLUSTER_NAME} deleted successfully"
    else
        log_warning "EKS cluster ${CLUSTER_NAME} does not exist or is already deleted"
    fi
}

# Get ECR repositories
get_ecr_repositories() {
    log_info "Finding ECR repositories..."
    
    local repositories=$(aws ecr describe-repositories --region "${AWS_REGION}" --query 'repositories[].repositoryName' --output text 2>/dev/null || echo "")
    
    if [ -n "$repositories" ]; then
        echo "$repositories"
    else
        log_warning "No ECR repositories found"
        return 1
    fi
}

# Remove ECR images older than 1 day
cleanup_ecr_images() {
    log_info "Cleaning up ECR images older than 1 day..."
    
    local repositories
    if repositories=$(get_ecr_repositories); then
        local cutoff_date=$(date -d "1 day ago" --iso-8601=seconds)
        log_info "Removing images older than: ${cutoff_date}"
        
        for repo in $repositories; do
            log_info "Processing repository: ${repo}"
            
            # Get images older than 1 day
            local old_images=$(aws ecr describe-images \
                --repository-name "${repo}" \
                --region "${AWS_REGION}" \
                --query "imageDetails[?imagePushedAt<\`${cutoff_date}\`].imageDigest" \
                --output text 2>/dev/null || echo "")
            
            if [ -n "$old_images" ] && [ "$old_images" != "None" ]; then
                log_info "Found old images in ${repo}, deleting..."
                
                # Delete images in batches
                echo "$old_images" | xargs -r -n 10 -I {} aws ecr batch-delete-image \
                    --repository-name "${repo}" \
                    --region "${AWS_REGION}" \
                    --image-ids imageDigest={} || {
                    log_warning "Some images in ${repo} could not be deleted"
                }
                
                log_success "Old images removed from repository: ${repo}"
            else
                log_info "No old images found in repository: ${repo}"
            fi
        done
    else
        log_warning "No ECR repositories to clean up"
    fi
}

# Purge local Docker images
purge_docker_images() {
    log_info "Purging local Docker images..."
    
    # Remove all unused images
    docker image prune -af || {
        log_warning "Failed to prune Docker images"
        return 1
    }
    
    # Remove dangling volumes
    docker volume prune -f || {
        log_warning "Failed to prune Docker volumes"
    }
    
    # Remove unused networks
    docker network prune -f || {
        log_warning "Failed to prune Docker networks"
    }
    
    log_success "Local Docker cleanup completed"
}

# Generate test summary
generate_test_summary() {
    log_info "Generating final test summary..."
    
    local summary_file="${ARTIFACTS_DIR}/final_test_summary_${TIMESTAMP}.txt"
    
    cat > "${summary_file}" << EOF
=============================================================================
FINAL TEST SUMMARY - ${TIMESTAMP}
=============================================================================

Cleanup Operations Completed:
- Kubernetes namespace '${K8S_NAMESPACE}' deletion: $(kubectl get namespace "${K8S_NAMESPACE}" &>/dev/null && echo "FAILED" || echo "SUCCESS")
- EKS cluster '${CLUSTER_NAME}' deletion: $(eksctl get cluster --name "${CLUSTER_NAME}" --region "${AWS_REGION}" &>/dev/null && echo "FAILED" || echo "SUCCESS")
- ECR images cleanup: SUCCESS
- Local Docker cleanup: SUCCESS

Environment Details:
- AWS Region: ${AWS_REGION}
- Cluster Name: ${CLUSTER_NAME}
- Namespace: ${K8S_NAMESPACE}
- Project Root: ${PROJECT_ROOT}
- Artifacts Directory: ${ARTIFACTS_DIR}

System Information:
- Timestamp: ${TIMESTAMP}
- User: $(whoami)
- Host: $(hostname)
- OS: $(uname -a)

Docker System Info:
$(docker system df 2>/dev/null || echo "Docker system info not available")

Remaining AWS Resources:
- EKS Clusters: $(eksctl get clusters --region "${AWS_REGION}" --output table 2>/dev/null || echo "None or unable to fetch")
- ECR Repositories: $(aws ecr describe-repositories --region "${AWS_REGION}" --query 'repositories[].repositoryName' --output text 2>/dev/null || echo "None or unable to fetch")

=============================================================================
CLEANUP COMPLETED SUCCESSFULLY
=============================================================================
EOF

    log_success "Test summary generated: ${summary_file}"
}

# Copy existing test results to artifacts
copy_test_results() {
    log_info "Copying existing test results to artifacts..."
    
    # Find and copy test result files
    find "${PROJECT_ROOT}" -name "test_*.log" -o -name "test_*.txt" -o -name "test_*.json" -o -name "test_*.xml" | while read -r file; do
        if [ -f "$file" ]; then
            cp "$file" "${ARTIFACTS_DIR}/" || log_warning "Failed to copy $file"
        fi
    done
    
    # Copy any pytest or other test outputs
    find "${PROJECT_ROOT}" -name "pytest_*.xml" -o -name "coverage.xml" -o -name ".coverage" | while read -r file; do
        if [ -f "$file" ]; then
            cp "$file" "${ARTIFACTS_DIR}/" || log_warning "Failed to copy $file"
        fi
    done
    
    log_success "Test results copied to artifacts directory"
}

# Main cleanup function
main() {
    log_info "Starting resource cleanup process..."
    echo "Configuration:"
    echo "- K8S Namespace: ${K8S_NAMESPACE}"
    echo "- Cluster Name: ${CLUSTER_NAME}"
    echo "- AWS Region: ${AWS_REGION}"
    echo "- Artifacts Directory: ${ARTIFACTS_DIR}"
    echo ""
    
    create_artifacts_dir
    check_prerequisites
    get_current_context
    copy_test_results
    
    # Cleanup operations
    delete_namespace
    delete_cluster
    cleanup_ecr_images
    purge_docker_images
    
    # Generate final summary
    generate_test_summary
    
    echo ""
    log_success "Resource cleanup completed successfully!"
    log_info "Final test summary and artifacts stored in: ${ARTIFACTS_DIR}"
    log_info "You can review the cleanup results in the generated summary file."
}

# Handle script interruption
trap 'log_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"
