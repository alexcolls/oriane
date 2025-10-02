#!/bin/bash

# =============================================================================
# Oriane APIs - EKS Deployment with Custom Domains
# =============================================================================
# This script deploys both pipeline and search APIs to EKS with custom domains:
# - pipeline.api.qdrant.admin.oriane.xyz
# - search.api.qdrant.admin.oriane.xyz
# =============================================================================

set -euo pipefail

# Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-"509399609859"}
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME:-"oriane-search-api-cluster"}
DOMAIN_BASE="qdrant.admin.oriane.xyz"
PIPELINE_DOMAIN="pipeline.api.${DOMAIN_BASE}"
SEARCH_DOMAIN="search.api.${DOMAIN_BASE}"
ORGANIZATION="Oriane Inc. US"

# SSL Certificate Configuration
# Use SSL_CERT_ARN for wildcard cert (preferred) or PIPELINE_CERT_ARN & SEARCH_CERT_ARN for separate certs
SSL_CERT_ARN=${SSL_CERT_ARN:-""}
PIPELINE_CERT_ARN=${PIPELINE_CERT_ARN:-""}
SEARCH_CERT_ARN=${SEARCH_CERT_ARN:-""}

# DNS Configuration (optional for automated DNS validation)
HOSTED_ZONE_ID=${HOSTED_ZONE_ID:-""}

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    # Check eksctl
    if ! command -v eksctl &> /dev/null; then
        log_error "eksctl is not installed. Please install it first."
        exit 1
    fi
    
    # Check Helm
    if ! command -v helm &> /dev/null; then
        log_error "Helm is not installed. Installing..."
        curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    fi
    
    log_success "Prerequisites check passed"
}

# Configure kubectl
configure_kubectl() {
    log_info "Configuring kubectl for EKS cluster..."
    
    aws eks update-kubeconfig \
        --region "$AWS_REGION" \
        --name "$EKS_CLUSTER_NAME"
    
    # Test kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Failed to connect to EKS cluster. Please check your configuration."
        exit 1
    fi
    
    log_success "kubectl configured successfully"
}

# Install AWS Load Balancer Controller
install_load_balancer_controller() {
    log_info "Installing AWS Load Balancer Controller..."
    
    # Check if controller is already installed
    if kubectl get deployment -n kube-system aws-load-balancer-controller &> /dev/null; then
        log_info "AWS Load Balancer Controller already installed"
        return 0
    fi
    
    # Create IAM policy for Load Balancer Controller
    curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json
    
    aws iam create-policy \
        --policy-name AWSLoadBalancerControllerIAMPolicy \
        --policy-document file://iam_policy.json \
        --region "$AWS_REGION" || log_warning "Policy may already exist"
    
    # Create IAM role and service account
    eksctl create iamserviceaccount \
        --cluster="$EKS_CLUSTER_NAME" \
        --namespace=kube-system \
        --name=aws-load-balancer-controller \
        --role-name AmazonEKSLoadBalancerControllerRole \
        --attach-policy-arn=arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
        --approve \
        --region "$AWS_REGION" || log_warning "Service account may already exist"
    
    # Install controller using Helm
    helm repo add eks https://aws.github.io/eks-charts
    helm repo update
    
    helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName="$EKS_CLUSTER_NAME" \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller \
        --set region="$AWS_REGION" \
        --set vpcId=$(aws eks describe-cluster --name "$EKS_CLUSTER_NAME" --query "cluster.resourcesVpcConfig.vpcId" --output text --region "$AWS_REGION")
    
    # Wait for controller to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=aws-load-balancer-controller -n kube-system --timeout=300s
    
    log_success "AWS Load Balancer Controller installed successfully"
}

# Update ingress files with correct certificate ARNs
update_ingress_files() {
    log_info "Updating ingress files with certificate ARNs..."
    
    # Update search API ingress with its specific certificate
    sed -i "s|arn:aws:acm:us-east-1:509399609859:certificate/YOUR_CERTIFICATE_ARN|${SEARCH_CERT_ARN}|g" "/home/quantium/labs/oriane/ExtractionPipeline/api/search/k8s/ingress.yaml"
    
    # Update pipeline API ingress with its specific certificate
    sed -i "s|arn:aws:acm:us-east-1:509399609859:certificate/YOUR_CERTIFICATE_ARN|${PIPELINE_CERT_ARN}|g" "/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/k8s/ingress.yaml"
    
    log_success "Ingress files updated with specific certificate ARNs"
}

# Deploy pipeline API
deploy_pipeline_api() {
    log_info "Deploying Pipeline API..."
    
    # Create namespace
    kubectl create namespace pipeline --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy pipeline API
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/k8s/configmap.yaml"
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/k8s/secret.yaml"
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/k8s/service.yaml"
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/k8s/deployment.yaml"
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/k8s/ingress.yaml"
    
    # Wait for deployment
    kubectl wait --for=condition=available --timeout=300s deployment/pipeline-api -n pipeline
    
    log_success "Pipeline API deployed successfully"
}

# Deploy search API
deploy_search_api() {
    log_info "Deploying Search API..."
    
    # Create namespace
    kubectl create namespace search --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy search API
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/search/k8s/namespace.yaml"
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/search/k8s/configmap.yaml"
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/search/k8s/secret.yaml"
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/search/k8s/service.yaml"
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/search/k8s/deployment.yaml"
    kubectl apply -f "/home/quantium/labs/oriane/ExtractionPipeline/api/search/k8s/ingress.yaml"
    
    # Wait for deployment
    kubectl wait --for=condition=available --timeout=300s deployment/search-api -n search
    
    log_success "Search API deployed successfully"
}

# Get ingress endpoints
get_ingress_endpoints() {
    log_info "Getting ingress endpoints..."
    
    sleep 30  # Wait for ingress to be provisioned
    
    echo ""
    log_info "Ingress Status:"
    kubectl get ingress -n pipeline
    kubectl get ingress -n search
    
    echo ""
    log_info "Load Balancer Endpoints:"
    
    # Get ALB hostnames
    PIPELINE_ALB=$(kubectl get ingress pipeline-api-ingress -n pipeline -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not yet available")
    SEARCH_ALB=$(kubectl get ingress search-api-ingress -n search -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not yet available")
    
    log_info "Pipeline API ALB: $PIPELINE_ALB"
    log_info "Search API ALB: $SEARCH_ALB"
    
    echo ""
    log_warning "DNS Setup Required:"
    log_warning "Create CNAME records in Route 53 or your DNS provider:"
    log_warning "  ${PIPELINE_DOMAIN} -> ${PIPELINE_ALB}"
    log_warning "  ${SEARCH_DOMAIN} -> ${SEARCH_ALB}"
    
    echo ""
    log_info "Once DNS is configured, you can access:"
    log_info "  Pipeline API docs: https://${PIPELINE_DOMAIN}/docs"
    log_info "  Search API docs: https://${SEARCH_DOMAIN}/docs"
}

# Create or verify SSL certificates
create_or_verify_individual_certs() {
    log_info "Creating or verifying SSL certificates for API domains..."
    
    # Request or find Pipeline API certificate
    if [[ -n "$SSL_CERT_ARN" ]]; then
        PIPELINE_CERT_ARN=$SSL_CERT_ARN
        SEARCH_CERT_ARN=$SSL_CERT_ARN
        log_info "Using shared wildcard certificate for both APIs."
    else
        if [[ -z "$PIPELINE_CERT_ARN" ]]; then
            PIPELINE_CERT_ARN=$(aws acm request-certificate \
                --domain-name "$PIPELINE_DOMAIN" \
                --validation-method DNS \
                --idempotency-token pipelineapi \
                --region "$AWS_REGION" \
                --options CertificateTransparencyLoggingPreference=ENABLED \
                --subject-alternative-names "pipeline.admin.${DOMAIN_BASE}" \
                --tags Key=Project,Value=PipelineAPI \
                --query CertificateArn --output text)
            log_info "Requested new certificate for Pipeline API: $PIPELINE_CERT_ARN"
        fi
        
        if [[ -z "$SEARCH_CERT_ARN" ]]; then
            SEARCH_CERT_ARN=$(aws acm request-certificate \
                --domain-name "$SEARCH_DOMAIN" \
                --validation-method DNS \
                --idempotency-token searchapi \
                --region "$AWS_REGION" \
                --options CertificateTransparencyLoggingPreference=ENABLED \
                --subject-alternative-names "search.admin.${DOMAIN_BASE}" \
                --tags Key=Project,Value=SearchAPI \
                --query CertificateArn --output text)
            log_info "Requested new certificate for Search API: $SEARCH_CERT_ARN"
        fi
        
        if [[ -n "$HOSTED_ZONE_ID" ]]; then
            log_info "Setting up Route 53 CNAME records for DNS validation..."
            create_dns_validation_records
        else
            log_warning "HOSTED_ZONE_ID not provided. You must manually create DNS validation records."
            log_warning "Check the AWS ACM console for the required DNS validation records."
        fi
    fi
}

# Create DNS validation records in Route 53
create_dns_validation_records() {
    log_info "Creating DNS validation records for ACM certificates..."
    
    # Get validation options for pipeline certificate
    if [[ "$PIPELINE_CERT_ARN" != "$SEARCH_CERT_ARN" ]]; then
        # Different certificates - create validation records for both
        local pipeline_validation_options=$(aws acm describe-certificate --certificate-arn "$PIPELINE_CERT_ARN" --region "$AWS_REGION" --query 'Certificate.DomainValidationOptions' --output json)
        local search_validation_options=$(aws acm describe-certificate --certificate-arn "$SEARCH_CERT_ARN" --region "$AWS_REGION" --query 'Certificate.DomainValidationOptions' --output json)
        
        # Create validation records for pipeline certificate
        echo "$pipeline_validation_options" | jq -r '.[] | "\(.ResourceRecord.Name) \(.ResourceRecord.Value)"' | while read -r name value; do
            if [[ -n "$name" && -n "$value" ]]; then
                log_info "Creating DNS validation record for: $name"
                aws route53 change-resource-record-sets --hosted-zone-id "$HOSTED_ZONE_ID" --change-batch '{
                  "Changes": [{
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                      "Name": "'$name'",
                      "Type": "CNAME",
                      "TTL": 300,
                      "ResourceRecords": [{"Value": "'$value'"}]
                    }
                  }]
                }'
            fi
        done
        
        # Create validation records for search certificate
        echo "$search_validation_options" | jq -r '.[] | "\(.ResourceRecord.Name) \(.ResourceRecord.Value)"' | while read -r name value; do
            if [[ -n "$name" && -n "$value" ]]; then
                log_info "Creating DNS validation record for: $name"
                aws route53 change-resource-record-sets --hosted-zone-id "$HOSTED_ZONE_ID" --change-batch '{
                  "Changes": [{
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                      "Name": "'$name'",
                      "Type": "CNAME",
                      "TTL": 300,
                      "ResourceRecords": [{"Value": "'$value'"}]
                    }
                  }]
                }'
            fi
        done
    else
        # Same certificate (wildcard) - create validation records once
        local validation_options=$(aws acm describe-certificate --certificate-arn "$PIPELINE_CERT_ARN" --region "$AWS_REGION" --query 'Certificate.DomainValidationOptions' --output json)
        
        echo "$validation_options" | jq -r '.[] | "\(.ResourceRecord.Name) \(.ResourceRecord.Value)"' | while read -r name value; do
            if [[ -n "$name" && -n "$value" ]]; then
                log_info "Creating DNS validation record for: $name"
                aws route53 change-resource-record-sets --hosted-zone-id "$HOSTED_ZONE_ID" --change-batch '{
                  "Changes": [{
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                      "Name": "'$name'",
                      "Type": "CNAME",
                      "TTL": 300,
                      "ResourceRecords": [{"Value": "'$value'"}]
                    }
                  }]
                }'
            fi
        done
    fi
    
    log_success "DNS validation records created in Route 53"
}

wait_for_certificate_validation() {
    log_info "Waiting for certificate validation..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        # Check pipeline certificate status
        PIPELINE_STATUS=$(aws acm describe-certificate --certificate-arn "$PIPELINE_CERT_ARN" --region "$AWS_REGION" --query 'Certificate.Status' --output text)
        
        # Check search certificate status (only if different from pipeline)
        if [[ "$PIPELINE_CERT_ARN" != "$SEARCH_CERT_ARN" ]]; then
            SEARCH_STATUS=$(aws acm describe-certificate --certificate-arn "$SEARCH_CERT_ARN" --region "$AWS_REGION" --query 'Certificate.Status' --output text)
            
            if [[ "$PIPELINE_STATUS" == "ISSUED" && "$SEARCH_STATUS" == "ISSUED" ]]; then
                log_success "Both certificates are validated and issued!"
                return 0
            fi
            
            log_info "Waiting for certificate validation... (Pipeline: $PIPELINE_STATUS, Search: $SEARCH_STATUS) - Attempt $((attempt + 1))/$max_attempts"
        else
            # Same certificate for both (wildcard)
            if [[ "$PIPELINE_STATUS" == "ISSUED" ]]; then
                log_success "Wildcard certificate is validated and issued!"
                return 0
            fi
            
            log_info "Waiting for certificate validation... (Wildcard: $PIPELINE_STATUS) - Attempt $((attempt + 1))/$max_attempts"
        fi
        
        sleep 60
        ((attempt++))
    done
    
    log_error "Certificate validation timed out. Please check DNS records and validate certificates manually."
    log_info "You can continue deployment later by setting the certificate ARNs and running the script again."
    exit 1
}

# Main execution
main() {
    log_info "Starting EKS deployment with custom domains..."
    echo "Pipeline Domain: $PIPELINE_DOMAIN"
    echo "Search Domain: $SEARCH_DOMAIN"
    echo "Organization: $ORGANIZATION"
    echo ""
    
    check_prerequisites
    configure_kubectl
    
    # SSL certificate strategy: single wildcard cert or explicit per-service
    if [[ -n "$SSL_CERT_ARN" ]]; then
        PIPELINE_CERT_ARN=$SSL_CERT_ARN
        SEARCH_CERT_ARN=$SSL_CERT_ARN
        log_info "Using provided wildcard certificate for both APIs."
    else
        create_or_verify_individual_certs
        log_info "Using individual certificates for each API."
    fi
    
    wait_for_certificate_validation
    
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
