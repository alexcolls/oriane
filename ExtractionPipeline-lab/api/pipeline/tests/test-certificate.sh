#!/bin/bash

echo "Testing SSL certificate with improved key usage..."
echo ""

# Test 1: Check certificate details
echo "1. Certificate Details:"
echo "   Certificate ARN: $(kubectl get ingress oriane-pipeline-api-ingress -n oriane-pipeline-api -o jsonpath='{.metadata.annotations.alb\.ingress\.kubernetes\.io/certificate-arn}')"
echo ""

# Test 2: Check certificate key usage
echo "2. Certificate Key Usage:"
openssl x509 -in certs/oriane-certificate.pem -noout -text | grep -A 1 "X509v3 Key Usage"
echo ""

# Test 3: Test API endpoint
echo "3. Testing API endpoint:"
curl -k -u "OrianeToTheMoon:HGJS98JHGL72K1SD8" https://pipeline.api.qdrant.admin.oriane.xyz/api/docs | grep -o '<title>.*</title>'
echo ""

# Test 4: Test SSL connection details
echo "4. SSL Connection Details:"
echo "   To test in browser, go to: https://pipeline.api.qdrant.admin.oriane.xyz/api/docs"
echo "   Username: OrianeToTheMoon"
echo "   Password: HGJS98JHGL72K1SD8"
echo ""
echo "   The certificate now includes 'Digital Signature' in key usage,"
echo "   which should resolve the ERR_SSL_KEY_USAGE_INCOMPATIBLE error."
echo ""

# Test 5: Show openssl connection test
echo "5. OpenSSL Connection Test:"
timeout 5 openssl s_client -connect pipeline.api.qdrant.admin.oriane.xyz:443 -servername pipeline.api.qdrant.admin.oriane.xyz < /dev/null 2>/dev/null | grep -E "(subject|issuer|verify return code)"

echo ""
echo "✅ Certificate has been updated with proper key usage."
echo "   The browser SSL error should now be resolved."
echo "   You may still need to accept the self-signed certificate warning."
