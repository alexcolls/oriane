#!/bin/bash
# Script deploy-all.sh – Complete deployment pipeline for Oriane API

# This script runs all deployment steps in the correct order

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=== Starting Complete Deployment Pipeline ===${NC}"
echo -e "${BLUE}This will deploy the Oriane Pipeline API to AWS EKS with SSL and DNS${NC}"
echo ""

# Step 0: Request SSL Certificate
echo -e "${YELLOW}Step 0: Requesting SSL Certificate...${NC}"
if [ -f "${SCRIPT_DIR}/00-request-ssl-certificate.sh" ]; then
    bash "${SCRIPT_DIR}/00-request-ssl-certificate.sh"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ SSL Certificate setup completed${NC}"
    else
        echo -e "${RED}Error: SSL Certificate setup failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: 00-request-ssl-certificate.sh not found${NC}"
    exit 1
fi

echo ""

# Step 1: Deploy to EKS
echo -e "${YELLOW}Step 1: Deploying to EKS...${NC}"
if [ -f "${SCRIPT_DIR}/deploy_to_eks.sh" ]; then
    bash "${SCRIPT_DIR}/deploy_to_eks.sh"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ EKS deployment completed${NC}"
    else
        echo -e "${RED}Error: EKS deployment failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: deploy_to_eks.sh not found${NC}"
    exit 1
fi

echo ""

# Step 2: Apply Ingress
echo -e "${YELLOW}Step 2: Applying Ingress...${NC}"
if [ -f "${SCRIPT_DIR}/05-apply-ingress.sh" ]; then
    bash "${SCRIPT_DIR}/05-apply-ingress.sh"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Ingress application completed${NC}"
    else
        echo -e "${RED}Error: Ingress application failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: 05-apply-ingress.sh not found${NC}"
    exit 1
fi

echo ""

# Step 3: Update DNS
echo -e "${YELLOW}Step 3: Updating DNS records...${NC}"
if [ -f "${SCRIPT_DIR}/06-update-dns.sh" ]; then
    bash "${SCRIPT_DIR}/06-update-dns.sh"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ DNS update completed${NC}"
    else
        echo -e "${RED}Error: DNS update failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: 06-update-dns.sh not found${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}=== Complete Deployment Pipeline Finished ===${NC}"
echo -e "${GREEN}🎉 Your API is now deployed and accessible!${NC}"
echo ""

# Load environment variables to show the final URL
if [ -f "${SCRIPT_DIR}/.env" ]; then
    source "${SCRIPT_DIR}/.env"
    echo -e "${BLUE}Your API is accessible at: https://${ALB_DOMAIN}${NC}"
    echo -e "${BLUE}API Documentation: https://${ALB_DOMAIN}/docs${NC}"
    echo -e "${BLUE}OpenAPI Spec: https://${ALB_DOMAIN}/openapi.json${NC}"
else
    echo -e "${YELLOW}Could not load .env file to show final URL${NC}"
fi

echo ""
echo -e "${YELLOW}Note: It may take a few minutes for all services to be fully ready${NC}"
echo -e "${YELLOW}You can check the deployment status with:${NC}"
echo -e "${BLUE}kubectl get pods -n oriane-pipeline-api${NC}"
echo -e "${BLUE}kubectl get ingress -n oriane-pipeline-api${NC}"
