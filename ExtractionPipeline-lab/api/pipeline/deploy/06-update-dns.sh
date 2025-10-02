#!/bin/bash
# Script 06-update-dns.sh – Update Route 53 CNAME record to point to ALB

# This script retrieves the ALB DNS name from the ingress and updates Route 53 CNAME record

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    source .env
    echo -e "${GREEN}✓ Environment variables loaded from .env${NC}"
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

echo -e "${BLUE}=== Starting DNS Update Process ===${NC}"

# Step 1: Verify required environment variables
echo -e "${YELLOW}Step 1: Verifying required environment variables...${NC}"
if [ -z "$ALB_DOMAIN" ]; then
    echo -e "${RED}Error: ALB_DOMAIN environment variable is not set${NC}"
    exit 1
fi

if [ -z "$AWS_REGION" ]; then
    echo -e "${RED}Error: AWS_REGION environment variable is not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Domain: $ALB_DOMAIN${NC}"
echo -e "${GREEN}✓ AWS Region: $AWS_REGION${NC}"

# Step 2: Get ALB DNS name from ingress
echo -e "${YELLOW}Step 2: Retrieving ALB DNS name from ingress...${NC}"
ALB_DNS_NAME=$(kubectl get ingress oriane-pipeline-api-ingress -n oriane-pipeline-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)

if [ -z "$ALB_DNS_NAME" ]; then
    echo -e "${RED}Error: ALB DNS name not found. Make sure the ingress is deployed and has an address.${NC}"
    echo -e "${YELLOW}Run the following command to check ingress status:${NC}"
    echo -e "${BLUE}kubectl get ingress oriane-pipeline-api-ingress -n oriane-pipeline-api${NC}"
    exit 1
fi

echo -e "${GREEN}✓ ALB DNS name obtained: $ALB_DNS_NAME${NC}"

# Step 3: Extract hosted zone from domain
echo -e "${YELLOW}Step 3: Extracting hosted zone information...${NC}"
# Extract the root domain (e.g., oriane.xyz from pipeline.api.qdrant.admin.oriane.xyz)
ROOT_DOMAIN=$(echo "$ALB_DOMAIN" | awk -F'.' '{print $(NF-1)"."$NF}')
echo -e "${GREEN}✓ Root domain: $ROOT_DOMAIN${NC}"

# Step 4: Get hosted zone ID
echo -e "${YELLOW}Step 4: Getting hosted zone ID...${NC}"
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones --query "HostedZones[?Name=='${ROOT_DOMAIN}.'].Id" --output text --region $AWS_REGION)

if [ -z "$HOSTED_ZONE_ID" ]; then
    echo -e "${RED}Error: Hosted zone for $ROOT_DOMAIN not found${NC}"
    echo -e "${YELLOW}Available hosted zones:${NC}"
    aws route53 list-hosted-zones --query 'HostedZones[].Name' --output table --region $AWS_REGION
    exit 1
fi

# Remove the /hostedzone/ prefix
HOSTED_ZONE_ID=$(echo $HOSTED_ZONE_ID | sed 's|/hostedzone/||')
echo -e "${GREEN}✓ Hosted zone ID: $HOSTED_ZONE_ID${NC}"

# Step 5: Check if CNAME record already exists
echo -e "${YELLOW}Step 5: Checking if CNAME record already exists...${NC}"
EXISTING_RECORD=$(aws route53 list-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --query "ResourceRecordSets[?Name=='${ALB_DOMAIN}.' && Type=='CNAME'].ResourceRecords[0].Value" \
    --output text \
    --region $AWS_REGION)

if [ "$EXISTING_RECORD" != "None" ] && [ -n "$EXISTING_RECORD" ]; then
    echo -e "${YELLOW}CNAME record already exists: $ALB_DOMAIN -> $EXISTING_RECORD${NC}"
    if [ "$EXISTING_RECORD" = "$ALB_DNS_NAME" ]; then
        echo -e "${GREEN}✓ CNAME record is already correct!${NC}"
        echo -e "${BLUE}=== DNS Update Process Complete ===${NC}"
        exit 0
    else
        echo -e "${YELLOW}CNAME record needs to be updated${NC}"
        ACTION="UPSERT"
    fi
else
    echo -e "${YELLOW}CNAME record does not exist, will create new record${NC}"
    ACTION="CREATE"
fi

# Step 6: Create/Update CNAME record
echo -e "${YELLOW}Step 6: ${ACTION}ing CNAME record...${NC}"

# Create the change batch JSON
CHANGE_BATCH=$(cat <<EOF
{
    "Changes": [
        {
            "Action": "$ACTION",
            "ResourceRecordSet": {
                "Name": "$ALB_DOMAIN",
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [
                    {
                        "Value": "$ALB_DNS_NAME"
                    }
                ]
            }
        }
    ]
}
EOF
)

# Apply the change
CHANGE_ID=$(aws route53 change-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --change-batch "$CHANGE_BATCH" \
    --query 'ChangeInfo.Id' \
    --output text \
    --region $AWS_REGION)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ CNAME record ${ACTION}d successfully${NC}"
    echo -e "${GREEN}✓ Change ID: $CHANGE_ID${NC}"
else
    echo -e "${RED}Error: Failed to ${ACTION} CNAME record${NC}"
    exit 1
fi

# Step 7: Wait for DNS propagation
echo -e "${YELLOW}Step 7: Waiting for DNS propagation...${NC}"
aws route53 wait resource-record-sets-changed --id $CHANGE_ID --region $AWS_REGION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ DNS propagation completed${NC}"
else
    echo -e "${YELLOW}Warning: DNS propagation check timed out, but the change may still be propagating${NC}"
fi

# Step 8: Verify the CNAME record
echo -e "${YELLOW}Step 8: Verifying CNAME record...${NC}"
FINAL_RECORD=$(aws route53 list-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --query "ResourceRecordSets[?Name=='${ALB_DOMAIN}.' && Type=='CNAME'].ResourceRecords[0].Value" \
    --output text \
    --region $AWS_REGION)

if [ "$FINAL_RECORD" = "$ALB_DNS_NAME" ]; then
    echo -e "${GREEN}✓ CNAME record verified successfully${NC}"
    echo -e "${GREEN}✓ $ALB_DOMAIN -> $ALB_DNS_NAME${NC}"
else
    echo -e "${RED}Error: CNAME record verification failed${NC}"
    exit 1
fi

echo -e "${BLUE}=== DNS Update Process Complete ===${NC}"
echo -e "${GREEN}🎉 DNS configuration successful!${NC}"
echo -e "${BLUE}Your API should now be accessible at: https://$ALB_DOMAIN${NC}"
echo -e "${YELLOW}Note: It may take a few minutes for DNS changes to propagate globally${NC}"

# Step 9: Display manual CLI command template for reference
echo -e "${BLUE}=== Manual CLI Command Template ===${NC}"
echo -e "${YELLOW}For future reference, here's the manual CLI command to update this CNAME record:${NC}"
echo -e "${BLUE}# Get ALB DNS name:${NC}"
echo -e "ALB_DNS_NAME=\$(kubectl get ingress oriane-pipeline-api-ingress -n oriane-pipeline-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"
echo -e "${BLUE}# Update CNAME record:${NC}"
echo -e "aws route53 change-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID --change-batch '{\"Changes\":[{\"Action\":\"UPSERT\",\"ResourceRecordSet\":{\"Name\":\"$ALB_DOMAIN\",\"Type\":\"CNAME\",\"TTL\":300,\"ResourceRecords\":[{\"Value\":\"'\$ALB_DNS_NAME'\"}]}}]}' --region $AWS_REGION"

# Optional: Test DNS resolution
echo -e "${YELLOW}Testing DNS resolution...${NC}"
if command -v dig &> /dev/null; then
    echo -e "${BLUE}DNS resolution test:${NC}"
    dig +short $ALB_DOMAIN
elif command -v nslookup &> /dev/null; then
    echo -e "${BLUE}DNS resolution test:${NC}"
    nslookup $ALB_DOMAIN
else
    echo -e "${YELLOW}dig/nslookup not available, skipping DNS resolution test${NC}"
fi
