#!/bin/bash

CERT_ARN="arn:aws:acm:us-east-1:509399609859:certificate/72c15dec-89cb-443a-a128-da3896c3b3d8"

echo "Monitoring certificate validation status..."
echo "Certificate ARN: $CERT_ARN"
echo ""

while true; do
    STATUS=$(aws acm describe-certificate --certificate-arn $CERT_ARN --region us-east-1 --query 'Certificate.Status' --output text)
    
    echo "$(date): Certificate status: $STATUS"
    
    if [ "$STATUS" = "ISSUED" ]; then
        echo ""
        echo "🎉 Certificate has been validated and issued!"
        echo "Updating ingress to use the new certificate..."
        
        kubectl patch ingress oriane-pipeline-api-ingress -n oriane-pipeline-api --type='merge' -p="{\"metadata\":{\"annotations\":{\"alb.ingress.kubernetes.io/certificate-arn\":\"$CERT_ARN\"}}}"
        
        if [ $? -eq 0 ]; then
            echo "✅ Ingress updated successfully!"
            echo "The ALB will now use the validated certificate. This may take a few minutes to propagate."
            echo ""
            echo "You can verify the certificate is working by visiting:"
            echo "https://pipeline.api.qdrant.admin.oriane.xyz/api/docs"
            echo ""
            echo "The connection should now show as secure! 🔐"
        else
            echo "❌ Failed to update ingress. Please check kubectl access."
        fi
        break
    elif [ "$STATUS" = "FAILED" ]; then
        echo "❌ Certificate validation failed. Please check the DNS record."
        break
    else
        echo "⏳ Still waiting for validation..."
        sleep 30
    fi
done
