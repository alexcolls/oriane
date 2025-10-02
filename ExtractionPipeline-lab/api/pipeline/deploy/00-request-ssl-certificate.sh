#!/bin/bash
# Script 00-request-ssl-certificate.sh – Request SSL certificate from AWS Certificate Manager

# This script requests an SSL certificate for the API domain and updates the .env file

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

echo -e "${BLUE}=== Starting SSL Certificate Request Process ===${NC}"

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

# Step 2: Check if certificate already exists
echo -e "${YELLOW}Step 2: Checking if certificate already exists...${NC}"
EXISTING_CERT=$(aws acm list-certificates --region $AWS_REGION --query "CertificateSummaryList[?DomainName=='$ALB_DOMAIN'].CertificateArn" --output text)

if [ -n "$EXISTING_CERT" ] && [ "$EXISTING_CERT" != "None" ]; then
    echo -e "${GREEN}✓ Certificate already exists: $EXISTING_CERT${NC}"
    CERTIFICATE_ARN="$EXISTING_CERT"
else
    # Step 3: Request new certificate
    echo -e "${YELLOW}Step 3: Requesting new SSL certificate...${NC}"
    CERTIFICATE_ARN=$(aws acm request-certificate \
        --domain-name "$ALB_DOMAIN" \
        --validation-method DNS \
        --region $AWS_REGION \
        --query 'CertificateArn' \
        --output text)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Certificate requested successfully${NC}"
        echo -e "${GREEN}✓ Certificate ARN: $CERTIFICATE_ARN${NC}"
    else
        echo -e "${RED}Error: Failed to request certificate${NC}"
        exit 1
    fi
fi

# Step 4: Update .env file with certificate ARN
echo -e "${YELLOW}Step 4: Updating .env file with certificate ARN...${NC}"
if grep -q "^ALB_CERTIFICATE_ARN=" .env; then
    # Update existing line
    sed -i "s|^ALB_CERTIFICATE_ARN=.*|ALB_CERTIFICATE_ARN=$CERTIFICATE_ARN|" .env
    echo -e "${GREEN}✓ Updated existing ALB_CERTIFICATE_ARN in .env${NC}"
else
    # Add new line
    echo "ALB_CERTIFICATE_ARN=$CERTIFICATE_ARN" >> .env
    echo -e "${GREEN}✓ Added ALB_CERTIFICATE_ARN to .env${NC}"
fi

# Step 5: Get DNS validation records
echo -e "${YELLOW}Step 5: Getting DNS validation records...${NC}"
echo -e "${BLUE}Waiting for certificate validation records to be generated...${NC}"
sleep 5

# Get the validation records
VALIDATION_RECORDS=$(aws acm describe-certificate \
    --certificate-arn "$CERTIFICATE_ARN" \
    --region $AWS_REGION \
    --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
    --output json)

if [ "$VALIDATION_RECORDS" != "null" ] && [ -n "$VALIDATION_RECORDS" ]; then
    VALIDATION_NAME=$(echo "$VALIDATION_RECORDS" | jq -r '.Name')
    VALIDATION_VALUE=$(echo "$VALIDATION_RECORDS" | jq -r '.Value')
    VALIDATION_TYPE=$(echo "$VALIDATION_RECORDS" | jq -r '.Type')
    
    echo -e "${GREEN}✓ DNS validation records obtained${NC}"
    echo -e "${BLUE}DNS Validation Record Details:${NC}"
    echo -e "${BLUE}Name: $VALIDATION_NAME${NC}"
    echo -e "${BLUE}Type: $VALIDATION_TYPE${NC}"
    echo -e "${BLUE}Value: $VALIDATION_VALUE${NC}"
else
    echo -e "${YELLOW}Validation records not yet available. Retrying in 10 seconds...${NC}"
    sleep 10
    VALIDATION_RECORDS=$(aws acm describe-certificate \
        --certificate-arn "$CERTIFICATE_ARN" \
        --region $AWS_REGION \
        --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
        --output json)
    
    if [ "$VALIDATION_RECORDS" != "null" ] && [ -n "$VALIDATION_RECORDS" ]; then
        VALIDATION_NAME=$(echo "$VALIDATION_RECORDS" | jq -r '.Name')
        VALIDATION_VALUE=$(echo "$VALIDATION_RECORDS" | jq -r '.Value')
        VALIDATION_TYPE=$(echo "$VALIDATION_RECORDS" | jq -r '.Type')
        
        echo -e "${GREEN}✓ DNS validation records obtained${NC}"
        echo -e "${BLUE}DNS Validation Record Details:${NC}"
        echo -e "${BLUE}Name: $VALIDATION_NAME${NC}"
        echo -e "${BLUE}Type: $VALIDATION_TYPE${NC}"
        echo -e "${BLUE}Value: $VALIDATION_VALUE${NC}"
    else
        echo -e "${RED}Error: Could not obtain DNS validation records${NC}"
        exit 1
    fi
fi

# Step 6: Automatically add DNS validation record to Route 53
echo -e "${YELLOW}Step 6: Adding DNS validation record to Route 53...${NC}"

# Extract the root domain (e.g., oriane.xyz from pipeline.api.qdrant.admin.oriane.xyz)
ROOT_DOMAIN=$(echo "$ALB_DOMAIN" | awk -F'.' '{print $(NF-1)"."$NF}')
echo -e "${GREEN}✓ Root domain: $ROOT_DOMAIN${NC}"

# Get hosted zone ID
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

# Create the DNS validation record
CHANGE_BATCH=$(cat <<EOF
{
    "Changes": [
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "$VALIDATION_NAME",
                "Type": "$VALIDATION_TYPE",
                "TTL": 300,
                "ResourceRecords": [
                    {
                        "Value": "$VALIDATION_VALUE"
                    }
                ]
            }
        }
    ]
}
EOF
)

CHANGE_ID=$(aws route53 change-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --change-batch "$CHANGE_BATCH" \
    --query 'ChangeInfo.Id' \
    --output text \
    --region $AWS_REGION)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ DNS validation record created successfully${NC}"
    echo -e "${GREEN}✓ Change ID: $CHANGE_ID${NC}"
else
    echo -e "${RED}Error: Failed to create DNS validation record${NC}"
    exit 1
fi

# Step 7: Wait for DNS propagation
echo -e "${YELLOW}Step 7: Waiting for DNS propagation...${NC}"
aws route53 wait resource-record-sets-changed --id $CHANGE_ID --region $AWS_REGION

echo -e "${GREEN}✓ DNS validation record propagated${NC}"

# Step 8: Wait for certificate validation
echo -e "${YELLOW}Step 8: Waiting for certificate validation...${NC}"
echo -e "${BLUE}This may take a few minutes. Please wait...${NC}"

# Poll certificate status
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    CERT_STATUS=$(aws acm describe-certificate \
        --certificate-arn "$CERTIFICATE_ARN" \
        --region $AWS_REGION \
        --query 'Certificate.Status' \
        --output text)
    
    if [ "$CERT_STATUS" = "ISSUED" ]; then
        echo -e "${GREEN}✓ Certificate validated and issued successfully!${NC}"
        break
    elif [ "$CERT_STATUS" = "FAILED" ]; then
        echo -e "${RED}Error: Certificate validation failed${NC}"
        exit 1
    else
        echo -e "${YELLOW}Certificate status: $CERT_STATUS (attempt $((ATTEMPT + 1))/$MAX_ATTEMPTS)${NC}"
        sleep 30
        ATTEMPT=$((ATTEMPT + 1))
    fi
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${YELLOW}Warning: Certificate validation is taking longer than expected${NC}"
    echo -e "${YELLOW}You can check the status later with: aws acm describe-certificate --certificate-arn $CERTIFICATE_ARN --region $AWS_REGION${NC}"
else
    echo -e "${GREEN}✓ Certificate is ready for use!${NC}"
fi

echo -e "${BLUE}=== SSL Certificate Request Process Complete ===${NC}"
echo -e "${GREEN}🎉 SSL Certificate configuration successful!${NC}"
echo -e "${GREEN}✓ Certificate ARN: $CERTIFICATE_ARN${NC}"
echo -e "${GREEN}✓ Updated .env file with certificate ARN${NC}"
echo -e "${BLUE}You can now proceed with the deployment using the other scripts.${NC}"
