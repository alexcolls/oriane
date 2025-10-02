#!/bin/bash

# =============================================================================
# Resume Oriane APIs - EKS Deployment (For Pre-validated Certificates)
# =============================================================================
# This script resumes deployment when certificates are already validated
# =============================================================================

set -euo pipefail

# Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-"509399609859"}
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME:-"oriane-search-api-cluster"}
DOMAIN_BASE="qdrant.admin.oriane.xyz"
PIPELINE_DOMAIN="pipeline.api.${DOMAIN_BASE}"
SEARCH_DOMAIN="search.api.${DOMAIN_BASE}"

# SSL Certificate Configuration
# Use SSL_CERT_ARN for wildcard cert (preferred) or PIPELINE_CERT_ARN & SEARCH_CERT_ARN for separate certs
SSL_CERT_ARN=${SSL_CERT_ARN:-""}
PIPELINE_CERT_ARN=${PIPELINE_CERT_ARN:-""}
SEARCH_CERT_ARN=${SEARCH_CERT_ARN:-""}

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

# Help function
show_help() {
    cat << EOF
Resume Oriane APIs EKS Deployment

This script resumes deployment with existing certificate ARNs.

Usage: $0 [OPTIONS]

Options:
  -w, --wildcard-cert ARN    Wildcard certificate ARN for both APIs (preferred)
  -p, --pipeline-cert ARN    Pipeline API certificate ARN
  -s, --search-cert ARN      Search API certificate ARN
  -h, --help                 Show this help message

Environment Variables:
  SSL_CERT_ARN              Wildcard certificate ARN for both APIs (preferred)
  PIPELINE_CERT_ARN         Pipeline API certificate ARN
  SEARCH_CERT_ARN           Search API certificate ARN

Examples:
  # Using wildcard certificate (preferred):
  $0 -w arn:aws:acm:us-east-1:123:certificate/wildcard
  
  # Using separate certificates:
  $0 -p arn:aws:acm:us-east-1:123:certificate/abc -s arn:aws:acm:us-east-1:123:certificate/def
  
  # Or set environment variables:
  export SSL_CERT_ARN="arn:aws:acm:us-east-1:123:certificate/wildcard"
  $0
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--wildcard-cert)
            SSL_CERT_ARN="$2"
            shift 2
            ;;
        -p|--pipeline-cert)
            PIPELINE_CERT_ARN="$2"
            shift 2
            ;;
        -s|--search-cert)
            SEARCH_CERT_ARN="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Find certificates if not provided
find_certificates() {
    # SSL certificate strategy: single wildcard cert or explicit per-service
    if [[ -n "$SSL_CERT_ARN" ]]; then
        PIPELINE_CERT_ARN=$SSL_CERT_ARN
        SEARCH_CERT_ARN=$SSL_CERT_ARN
        log_info "Using provided wildcard certificate for both APIs."
    else
        if [[ -z "$PIPELINE_CERT_ARN" || -z "$SEARCH_CERT_ARN" ]]; then
            log_info "Looking for existing certificates..."
            
            # Search for certificates by domain name
            if [[ -z "$PIPELINE_CERT_ARN" ]]; then
                PIPELINE_CERT_ARN=$(aws acm list-certificates --region "$AWS_REGION" --query "CertificateSummaryList[?DomainName=='$PIPELINE_DOMAIN'].CertificateArn" --output text)
            fi
            
            if [[ -z "$SEARCH_CERT_ARN" ]]; then
                SEARCH_CERT_ARN=$(aws acm list-certificates --region "$AWS_REGION" --query "CertificateSummaryList[?DomainName=='$SEARCH_DOMAIN'].CertificateArn" --output text)
            fi
        fi
        
        # Validate certificate ARNs
        if [[ -z "$PIPELINE_CERT_ARN" ]]; then
            log_error "Pipeline certificate ARN not found. Please specify with -p option or PIPELINE_CERT_ARN environment variable."
            log_error "Alternatively, use -w option or SSL_CERT_ARN environment variable for wildcard certificate."
            exit 1
        fi
        
        if [[ -z "$SEARCH_CERT_ARN" ]]; then
            log_error "Search certificate ARN not found. Please specify with -s option or SEARCH_CERT_ARN environment variable."
            log_error "Alternatively, use -w option or SSL_CERT_ARN environment variable for wildcard certificate."
            exit 1
        fi
        
        log_info "Using individual certificates for each API."
    fi
    
    log_info "Pipeline Certificate ARN: $PIPELINE_CERT_ARN"
    log_info "Search Certificate ARN: $SEARCH_CERT_ARN"
}

# Source the main deployment functions
source_deployment_functions() {
    # Get the directory of this script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Source functions from the main deployment script
    source <(grep -A 50 "^check_prerequisites()" "$SCRIPT_DIR/deploy-with-domains.sh")
    source <(grep -A 50 "^configure_kubectl()" "$SCRIPT_DIR/deploy-with-domains.sh")
    source <(grep -A 50 "^install_load_balancer_controller()" "$SCRIPT_DIR/deploy-with-domains.sh")
    source <(grep -A 50 "^update_ingress_files()" "$SCRIPT_DIR/deploy-with-domains.sh")
    source <(grep -A 50 "^deploy_pipeline_api()" "$SCRIPT_DIR/deploy-with-domains.sh")
    source <(grep -A 50 "^deploy_search_api()" "$SCRIPT_DIR/deploy-with-domains.sh")
    source <(grep -A 50 "^get_ingress_endpoints()" "$SCRIPT_DIR/deploy-with-domains.sh")
}

# Main execution
main() {
    log_info "Resuming EKS deployment with existing certificates..."
    echo "Pipeline Domain: $PIPELINE_DOMAIN"
    echo "Search Domain: $SEARCH_DOMAIN"
    echo ""
    
    find_certificates
    
    # Run the main deployment script with existing certificates
    export PIPELINE_CERT_ARN
    export SEARCH_CERT_ARN
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Run the deployment directly using the main script but skip certificate creation
    log_info "Starting deployment with validated certificates..."
    
    # Source and execute deployment functions from main script
    . "$SCRIPT_DIR/deploy-with-domains.sh"
    
    check_prerequisites
    configure_kubectl
    install_load_balancer_controller
    update_ingress_files
    deploy_pipeline_api
    deploy_search_api
    get_ingress_endpoints
    
    echo ""
    log_success "Deployment completed successfully!"
    log_info "Remember to configure DNS records as shown above"
    log_info "Pipeline Certificate ARN: $PIPELINE_CERT_ARN"
    log_info "Search Certificate ARN: $SEARCH_CERT_ARN"
}

# Run main function
main "$@"
