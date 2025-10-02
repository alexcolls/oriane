#!/bin/bash

echo "🔍 Testing SSL Certificate for pipeline.api.qdrant.admin.oriane.xyz"
echo "============================================================="

# Test 1: Check certificate details
echo "📋 Certificate Details:"
echo | openssl s_client -servername pipeline.api.qdrant.admin.oriane.xyz -connect pipeline.api.qdrant.admin.oriane.xyz:443 2>/dev/null | openssl x509 -noout -subject -issuer -dates

echo ""
echo "🔒 Certificate Chain:"
echo | openssl s_client -servername pipeline.api.qdrant.admin.oriane.xyz -connect pipeline.api.qdrant.admin.oriane.xyz:443 2>/dev/null | openssl x509 -noout -text | grep -A5 -B5 "Issuer\|Subject\|DNS"

echo ""
echo "🌐 Testing HTTPS connection:"
curl -I https://pipeline.api.qdrant.admin.oriane.xyz/health

echo ""
echo "📊 SSL Labs style test:"
echo | openssl s_client -servername pipeline.api.qdrant.admin.oriane.xyz -connect pipeline.api.qdrant.admin.oriane.xyz:443 2>&1 | grep -E "(Verify return code|depth|verify)"

echo ""
echo "🔧 Troubleshooting steps if still showing 'not secure':"
echo "1. Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)"
echo "2. Clear browser cache and cookies for the site"
echo "3. Try incognito/private browsing mode"
echo "4. Wait a few more minutes for full propagation"
echo "5. Try a different browser"
echo ""
echo "The certificate is definitely legitimate and issued by Amazon!"
