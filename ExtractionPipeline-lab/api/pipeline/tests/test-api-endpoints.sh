#!/bin/bash

# Test API endpoints for the Oriane Pipeline API
# This script tests the correctly configured endpoints

set -e

# Load environment variables
source .env

# Get one of the ALB IPs for testing
ALB_IP=$(dig +short pipeline.api.qdrant.admin.oriane.xyz | head -1)

echo "Testing Oriane Pipeline API endpoints..."
echo "ALB IP: $ALB_IP"
echo "Domain: pipeline.api.qdrant.admin.oriane.xyz"
echo "Username: $API_USERNAME"
echo "API Key: ${API_KEY:0:20}..."
echo ""

# Test 1: Root endpoint (no auth required)
echo "1. Testing root endpoint..."
curl --insecure -s https://$ALB_IP/ -H "Host: pipeline.api.qdrant.admin.oriane.xyz" | jq .

# Test 2: Health endpoint (no auth required)
echo -e "\n2. Testing health endpoint..."
curl --insecure -s https://$ALB_IP/health -H "Host: pipeline.api.qdrant.admin.oriane.xyz" | jq .

# Test 3: Config endpoint (no auth required)
echo -e "\n3. Testing config endpoint..."
curl --insecure -s https://$ALB_IP/config -H "Host: pipeline.api.qdrant.admin.oriane.xyz" | jq .

# Test 4: API Documentation endpoint (basic auth required)
echo -e "\n4. Testing API documentation endpoint..."
echo "   URL: https://pipeline.api.qdrant.admin.oriane.xyz/api/docs"
echo "   Authentication: Basic ($API_USERNAME:$API_PASSWORD)"
curl --insecure -s -u "$API_USERNAME:$API_PASSWORD" https://$ALB_IP/api/docs -H "Host: pipeline.api.qdrant.admin.oriane.xyz" | grep -o '<title>.*</title>'

# Test 5: OpenAPI JSON endpoint (basic auth required)
echo -e "\n5. Testing OpenAPI JSON endpoint..."
curl --insecure -s -u "$API_USERNAME:$API_PASSWORD" https://$ALB_IP/api/openapi.json -H "Host: pipeline.api.qdrant.admin.oriane.xyz" | jq '.info'

# Test 6: Process endpoint (API key required) - GET should fail
echo -e "\n6. Testing process endpoint without API key (should fail)..."
curl --insecure -s https://$ALB_IP/process -H "Host: pipeline.api.qdrant.admin.oriane.xyz" | jq .

# Test 7: Process endpoint with API key - GET should still fail (POST only)
echo -e "\n7. Testing process endpoint with API key (GET should fail - POST only)..."
curl --insecure -s -H "X-API-Key: $API_KEY" https://$ALB_IP/process -H "Host: pipeline.api.qdrant.admin.oriane.xyz" | jq .

echo -e "\n✅ API endpoint tests completed!"
echo -e "\nTo access the API documentation in your browser:"
echo "  1. Go to: https://pipeline.api.qdrant.admin.oriane.xyz/api/docs"
echo "  2. Accept the self-signed certificate warning"
echo "  3. Use basic authentication:"
echo "     Username: $API_USERNAME"
echo "     Password: $API_PASSWORD"
echo ""
echo "To make API calls, use the X-API-Key header:"
echo "  curl -H \"X-API-Key: $API_KEY\" https://pipeline.api.qdrant.admin.oriane.xyz/config"
