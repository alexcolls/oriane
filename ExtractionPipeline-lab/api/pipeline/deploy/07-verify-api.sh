#!/bin/bash


# =============================================================================
# Verification Script for Oriane Pipeline API External Access
# =============================================================================
# This script verifies that the deployed API is accessible from external sources
# by testing the HTTPS endpoint and optionally opening it in a browser.
# 
# Usage:
#   bash 07-verify-api.sh [--open]
#
# Options:
#   --open    Automatically open the API docs in the default browser
#
# Configuration:
#   The script loads environment variables from .env file in the parent directory.
#   If ALB_DOMAIN is not set, it defaults to pipeline.api.qdrant.admin.oriane.xyz.
# =============================================================================

set -euo pipefail

# Parse command line arguments
OPEN_BROWSER=false
for arg in "$@"; do
    case $arg in
        --open)
            OPEN_BROWSER=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--open]"
            echo "  --open    Automatically open the API docs in the default browser"
            exit 0
            ;;
        *)
            ;;
    esac
done

# Load environment variables
ENV_FILE="$(dirname "$(realpath "$0")")/../.env"
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE"

# Use ALB_DOMAIN from environment or default
ALB_DOMAIN="${ALB_DOMAIN:-pipeline.api.qdrant.admin.oriane.xyz}"
API_URL="https://${ALB_DOMAIN}/docs"

echo "=== Verifying External Access to Oriane Pipeline API ==="
echo "Testing URL: $API_URL"
echo ""

# Test the API endpoint
echo "Checking API accessibility..."
HTTP_STATUS=$(curl -I -s -o /dev/null -w "%{http_code}" "$API_URL" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ SUCCESS: API is accessible (HTTP $HTTP_STATUS)"
    echo "   FastAPI documentation is available at: $API_URL"
    
    # Check if the response contains FastAPI documentation
    RESPONSE_CONTENT=$(curl -s "$API_URL" 2>/dev/null || echo "")
    if echo "$RESPONSE_CONTENT" | grep -q "FastAPI\|swagger\|OpenAPI" -i; then
        echo "✅ SUCCESS: FastAPI documentation is properly served"
    else
        echo "⚠️  WARNING: Received 200 OK but content may not be FastAPI docs"
    fi
    
    # Optionally open in browser
    if [ "$OPEN_BROWSER" = true ]; then
        echo ""
        echo "Opening API documentation in browser..."
        if command -v python3 &> /dev/null; then
            python3 -m webbrowser "$API_URL"
            echo "✅ Browser opened successfully"
        else
            echo "❌ python3 not found, cannot open browser automatically"
            echo "   Please manually open: $API_URL"
        fi
    fi
    
elif [ "$HTTP_STATUS" = "000" ]; then
    echo "❌ ERROR: Could not connect to $API_URL"
    echo "   This could indicate:"
    echo "   - DNS resolution issues"
    echo "   - Network connectivity problems"
    echo "   - ALB not properly configured"
    echo "   - Service is not running"
    
elif [ "$HTTP_STATUS" = "404" ]; then
    echo "❌ ERROR: API endpoint not found (HTTP 404)"
    echo "   This could indicate:"
    echo "   - Ingress routing is not configured correctly"
    echo "   - Service is not exposing the /docs endpoint"
    echo "   - Application is not running properly"
    
elif [ "$HTTP_STATUS" = "502" ] || [ "$HTTP_STATUS" = "503" ]; then
    echo "❌ ERROR: Service unavailable (HTTP $HTTP_STATUS)"
    echo "   This could indicate:"
    echo "   - Backend pods are not running"
    echo "   - Service is not healthy"
    echo "   - ALB cannot reach the backend"
    
elif [ "$HTTP_STATUS" = "403" ]; then
    echo "❌ ERROR: Access forbidden (HTTP 403)"
    echo "   This could indicate:"
    echo "   - Security group restrictions"
    echo "   - WAF rules blocking access"
    echo "   - Authentication/authorization issues"
    
else
    echo "❌ ERROR: Unexpected HTTP status: $HTTP_STATUS"
fi

echo ""
echo "=== Additional Verification Commands ==="
echo "To further diagnose issues, you can run:"
echo "  kubectl get pods -n oriane-pipeline-api"
echo "  kubectl get services -n oriane-pipeline-api"
echo "  kubectl get ingress -n oriane-pipeline-api"
echo "  kubectl describe ingress -n oriane-pipeline-api"
echo "  kubectl logs -f deployment/oriane-pipeline-api -n oriane-pipeline-api"

exit 0
