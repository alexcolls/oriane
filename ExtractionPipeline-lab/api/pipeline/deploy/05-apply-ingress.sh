#!/bin/bash
# Script 05-apply-ingress.sh – Apply existing Ingress manifest

# This script applies the fastapi-ingress.yaml manifest and monitors for ALB address

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INGRESS_MANIFEST="${SCRIPT_DIR}/k8s/ingress/fastapi-ingress.yaml"

echo -e "${BLUE}=== Starting Ingress Application Process ===${NC}"

# Step 1: Verify the ingress manifest exists
echo -e "${YELLOW}Step 1: Verifying ingress manifest exists...${NC}"
if [ ! -f "$INGRESS_MANIFEST" ]; then
    echo -e "${RED}Error: Ingress manifest not found at $INGRESS_MANIFEST${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Ingress manifest found at $INGRESS_MANIFEST${NC}"

# Step 2: Check if required environment variables are set
echo -e "${YELLOW}Step 2: Checking required environment variables...${NC}"
if [ -z "$ALB_CERTIFICATE_ARN" ]; then
    echo -e "${RED}Error: ALB_CERTIFICATE_ARN environment variable is not set${NC}"
    exit 1
fi
if [ -z "$ALB_DOMAIN" ]; then
    echo -e "${RED}Error: ALB_DOMAIN environment variable is not set${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Required environment variables are set${NC}"

# Step 3: Substitute environment variables in the manifest
echo -e "${YELLOW}Step 3: Processing manifest with environment variables...${NC}"
TEMP_MANIFEST=$(mktemp)
envsubst < "$INGRESS_MANIFEST" > "$TEMP_MANIFEST"
echo -e "${GREEN}✓ Environment variables substituted in manifest${NC}"

# Step 4: Apply the ingress manifest
echo -e "${YELLOW}Step 4: Applying ingress manifest...${NC}"
kubectl apply -f "$TEMP_MANIFEST"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Ingress manifest applied successfully${NC}"
else
    echo -e "${RED}Error: Failed to apply ingress manifest${NC}"
    rm -f "$TEMP_MANIFEST"
    exit 1
fi

# Clean up temporary file
rm -f "$TEMP_MANIFEST"

# Step 5: Wait for ingress to be ready
echo -e "${YELLOW}Step 5: Waiting for ingress to be created...${NC}"
kubectl wait --for=condition=ready ingress/fastapi-ingress -n oriane-pipeline-api --timeout=60s
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Ingress is ready${NC}"
else
    echo -e "${YELLOW}Warning: Ingress may still be provisioning${NC}"
fi

# Step 6: Watch for ALB address
echo -e "${YELLOW}Step 6: Monitoring for ALB address...${NC}"
echo -e "${BLUE}Watching for ALB address (this may take a few minutes)...${NC}"
echo -e "${BLUE}Press Ctrl+C to stop watching${NC}"
echo ""

# Function to get and display ingress info
get_ingress_info() {
    local ingress_info
    ingress_info=$(kubectl get ingress fastapi-ingress -n oriane-pipeline-api -o wide 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Current Ingress Status:${NC}"
        echo "$ingress_info"
        
        # Extract the ALB address
        local alb_address
        alb_address=$(kubectl get ingress fastapi-ingress -n oriane-pipeline-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
        if [ -n "$alb_address" ]; then
            echo -e "${GREEN}🎉 ALB Address obtained: $alb_address${NC}"
            echo -e "${BLUE}You can access your API at: https://$alb_address${NC}"
            if [ -n "$ALB_DOMAIN" ]; then
                echo -e "${BLUE}Domain access: https://$ALB_DOMAIN${NC}"
            fi
            return 0
        else
            echo -e "${YELLOW}ALB address not yet available...${NC}"
            return 1
        fi
    else
        echo -e "${RED}Error getting ingress information${NC}"
        return 1
    fi
}

# Initial check
if get_ingress_info; then
    echo -e "${GREEN}✓ ALB address is already available!${NC}"
else
    # Watch for changes
    echo -e "${YELLOW}Watching for ALB address (use Ctrl+C to stop)...${NC}"
    kubectl get ingress fastapi-ingress -n oriane-pipeline-api -w
fi

echo -e "${BLUE}=== Ingress Application Process Complete ===${NC}"
