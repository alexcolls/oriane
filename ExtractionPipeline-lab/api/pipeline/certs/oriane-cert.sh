#!/bin/bash


# =============================================================================
# Oriane Inc Certificate Generator
# =============================================================================
# This script generates a self-signed SSL certificate for Oriane Inc that can
# be used with AWS ALB and imported into AWS Certificate Manager.
# 
# The certificate includes:
# - Subject Alternative Names (SANs) for common Oriane domains
# - 2048-bit RSA key
# - SHA-256 signature algorithm
# - Valid for 365 days
# - Organization: Oriane Inc
# 
# Usage:
#   bash oriane-cert.sh [--domain DOMAIN] [--output-dir DIR]
#
# Options:
#   --domain DOMAIN     Primary domain name (default: pipeline.api.qdrant.admin.oriane.xyz)
#   --output-dir DIR    Output directory for certificates (default: ./certs)
#   --organization ORG  Organization name (default: Oriane Inc)
#   --country CC        Country code (default: US)
#   --state STATE       State/Province (default: California)
#   --city CITY         City (default: San Francisco)
#   --validity DAYS     Certificate validity in days (default: 365)
#   -h, --help          Show this help message
# =============================================================================

set -euo pipefail

# Default values
DEFAULT_DOMAIN="pipeline.api.qdrant.admin.oriane.xyz"
DEFAULT_OUTPUT_DIR="./certs"
DEFAULT_ORGANIZATION="Oriane Inc"
DEFAULT_COUNTRY="US"
DEFAULT_STATE="California"
DEFAULT_CITY="San Francisco"
DEFAULT_VALIDITY="365"

# Parse command line arguments
DOMAIN="$DEFAULT_DOMAIN"
OUTPUT_DIR="$DEFAULT_OUTPUT_DIR"
ORGANIZATION="$DEFAULT_ORGANIZATION"
COUNTRY="$DEFAULT_COUNTRY"
STATE="$DEFAULT_STATE"
CITY="$DEFAULT_CITY"
VALIDITY="$DEFAULT_VALIDITY"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
    cat << EOF
Oriane Inc Certificate Generator

Usage: $0 [OPTIONS]

Generate a self-signed SSL certificate for Oriane Inc domains.

Options:
    --domain DOMAIN     Primary domain name (default: $DEFAULT_DOMAIN)
    --output-dir DIR    Output directory for certificates (default: $DEFAULT_OUTPUT_DIR)
    --organization ORG  Organization name (default: $DEFAULT_ORGANIZATION)
    --country CC        Country code (default: $DEFAULT_COUNTRY)
    --state STATE       State/Province (default: $DEFAULT_STATE)
    --city CITY         City (default: $DEFAULT_CITY)
    --validity DAYS     Certificate validity in days (default: $DEFAULT_VALIDITY)
    -h, --help          Show this help message

Examples:
    $0                                      # Use default settings
    $0 --domain api.oriane.xyz              # Custom domain
    $0 --output-dir /tmp/certs --validity 730  # Custom output dir and 2-year validity

Output Files:
    oriane-private-key.pem     # Private key
    oriane-certificate.pem     # Certificate
    oriane-certificate.csr     # Certificate Signing Request
    oriane-certificate.conf    # OpenSSL configuration
    aws-import-command.txt     # AWS CLI command to import certificate

Environment Variables:
    The script will read ALB_DOMAIN from .env file if present and no --domain is specified.

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --organization)
            ORGANIZATION="$2"
            shift 2
            ;;
        --country)
            COUNTRY="$2"
            shift 2
            ;;
        --state)
            STATE="$2"
            shift 2
            ;;
        --city)
            CITY="$2"
            shift 2
            ;;
        --validity)
            VALIDITY="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Try to read domain from .env file if not specified
if [[ "$DOMAIN" == "$DEFAULT_DOMAIN" ]] && [[ -f ".env" ]]; then
    if grep -q "^ALB_DOMAIN=" .env; then
        ENV_DOMAIN=$(grep "^ALB_DOMAIN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ -n "$ENV_DOMAIN" ]]; then
            DOMAIN="$ENV_DOMAIN"
            echo -e "${BLUE}Using domain from .env file: $DOMAIN${NC}"
        fi
    fi
fi

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Validate inputs
if [[ -z "$DOMAIN" ]]; then
    error "Domain cannot be empty"
fi

if [[ ! "$VALIDITY" =~ ^[0-9]+$ ]]; then
    error "Validity must be a number (days)"
fi

if [[ "$VALIDITY" -lt 1 ]]; then
    error "Validity must be at least 1 day"
fi

# Check if openssl is installed
if ! command -v openssl &> /dev/null; then
    error "OpenSSL is not installed. Please install it first."
fi

# Create output directory
log "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# File paths
PRIVATE_KEY="$OUTPUT_DIR/oriane-private-key.pem"
CERTIFICATE="$OUTPUT_DIR/oriane-certificate.pem"
CSR="$OUTPUT_DIR/oriane-certificate.csr"
CONFIG="$OUTPUT_DIR/oriane-certificate.conf"
AWS_IMPORT_CMD="$OUTPUT_DIR/aws-import-command.txt"

# Generate OpenSSL configuration
log "Generating OpenSSL configuration..."
cat > "$CONFIG" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORGANIZATION
OU = Engineering
CN = $DOMAIN

[v3_req]
keyUsage = digitalSignature, keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
DNS.3 = api.oriane.xyz
DNS.4 = *.api.oriane.xyz
DNS.5 = admin.oriane.xyz
DNS.6 = *.admin.oriane.xyz
DNS.7 = app.oriane.xyz
DNS.8 = *.app.oriane.xyz
DNS.9 = oriane.xyz
DNS.10 = *.oriane.xyz
DNS.11 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

success "OpenSSL configuration created: $CONFIG"

# Generate private key
log "Generating private key (2048-bit RSA)..."
openssl genrsa -out "$PRIVATE_KEY" 2048
if [[ $? -eq 0 ]]; then
    success "Private key generated: $PRIVATE_KEY"
else
    error "Failed to generate private key"
fi

# Set secure permissions on private key
chmod 600 "$PRIVATE_KEY"

# Generate Certificate Signing Request
log "Generating Certificate Signing Request (CSR)..."
openssl req -new -key "$PRIVATE_KEY" -out "$CSR" -config "$CONFIG"
if [[ $? -eq 0 ]]; then
    success "CSR generated: $CSR"
else
    error "Failed to generate CSR"
fi

# Generate self-signed certificate
log "Generating self-signed certificate (valid for $VALIDITY days)..."
openssl x509 -req -in "$CSR" -signkey "$PRIVATE_KEY" -out "$CERTIFICATE" -days "$VALIDITY" -extensions v3_req -extfile "$CONFIG"
if [[ $? -eq 0 ]]; then
    success "Certificate generated: $CERTIFICATE"
else
    error "Failed to generate certificate"
fi

# Verify certificate
log "Verifying certificate..."
openssl x509 -in "$CERTIFICATE" -text -noout > /dev/null
if [[ $? -eq 0 ]]; then
    success "Certificate verification passed"
else
    error "Certificate verification failed"
fi

# Display certificate information
log "Certificate Information:"
echo -e "${BLUE}Subject:${NC}"
openssl x509 -in "$CERTIFICATE" -subject -noout | sed 's/^subject=/  /'
echo -e "${BLUE}Issuer:${NC}"
openssl x509 -in "$CERTIFICATE" -issuer -noout | sed 's/^issuer=/  /'
echo -e "${BLUE}Valid From:${NC}"
openssl x509 -in "$CERTIFICATE" -startdate -noout | sed 's/^notBefore=/  /'
echo -e "${BLUE}Valid To:${NC}"
openssl x509 -in "$CERTIFICATE" -enddate -noout | sed 's/^notAfter=/  /'
echo -e "${BLUE}Serial Number:${NC}"
openssl x509 -in "$CERTIFICATE" -serial -noout | sed 's/^serial=/  /'
echo -e "${BLUE}Fingerprint (SHA-256):${NC}"
openssl x509 -in "$CERTIFICATE" -fingerprint -sha256 -noout | sed 's/^SHA256 Fingerprint=/  /'

# Display Subject Alternative Names
echo -e "${BLUE}Subject Alternative Names:${NC}"
openssl x509 -in "$CERTIFICATE" -text -noout | grep -A 20 "Subject Alternative Name" | grep "DNS:" | sed 's/^[[:space:]]*/  /'

# Generate AWS import command
log "Generating AWS Certificate Manager import command..."
cat > "$AWS_IMPORT_CMD" << EOF
# AWS Certificate Manager Import Command
# Run this command to import the certificate into AWS ACM:

aws acm import-certificate \\
    --certificate fileb://$CERTIFICATE \\
    --private-key fileb://$PRIVATE_KEY \\
    --region us-east-1 \\
    --tags Key=Name,Value=oriane-inc-certificate \\
           Key=Organization,Value="$ORGANIZATION" \\
           Key=Domain,Value="$DOMAIN" \\
           Key=CreatedBy,Value=oriane-cert-script

# After importing, you can get the certificate ARN with:
# aws acm list-certificates --region us-east-1 --query 'CertificateSummaryList[?DomainName==\`$DOMAIN\`].CertificateArn' --output text

# To update your .env file with the certificate ARN:
# 1. Run the import command above
# 2. Get the ARN from the output
# 3. Update ALB_CERTIFICATE_ARN in your .env file
EOF

success "AWS import command created: $AWS_IMPORT_CMD"

# Summary
echo ""
echo -e "${GREEN}=== Certificate Generation Complete ===${NC}"
echo -e "${BLUE}Files created:${NC}"
echo "  Private Key:    $PRIVATE_KEY"
echo "  Certificate:    $CERTIFICATE"
echo "  CSR:            $CSR"
echo "  Config:         $CONFIG"
echo "  AWS Import Cmd: $AWS_IMPORT_CMD"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Review the AWS import command in: $AWS_IMPORT_CMD"
echo "2. Import the certificate into AWS ACM:"
echo "   ${YELLOW}aws acm import-certificate --certificate fileb://$CERTIFICATE --private-key fileb://$PRIVATE_KEY --region us-east-1${NC}"
echo "3. Get the certificate ARN and update ALB_CERTIFICATE_ARN in your .env file"
echo "4. Deploy your application with the new certificate"
echo ""
echo -e "${YELLOW}Security Note:${NC}"
echo "- Keep the private key secure and never share it"
echo "- This is a self-signed certificate - browsers will show warnings"
echo "- Consider using Let's Encrypt or AWS Certificate Manager for production"
echo ""
echo -e "${GREEN}Certificate successfully generated for $ORGANIZATION!${NC}"
