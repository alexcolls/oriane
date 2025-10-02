#!/bin/bash

# Wait for certificate to be validated and update ingress
CERT_ARN="arn:aws:acm:us-east-1:509399609859:certificate/72c15dec-89cb-443a-a128-da3896c3b3d8"

echo "Checking certificate status..."
aws acm describe-certificate --certificate-arn $CERT_ARN --region us-east-1 --query 'Certificate.Status' --output text

echo "Updating ingress to use real certificate..."
kubectl patch ingress oriane-pipeline-api-ingress -n oriane-pipeline-api --type='merge' -p="{\"metadata\":{\"annotations\":{\"alb.ingress.kubernetes.io/certificate-arn\":\"$CERT_ARN\"}}}"

echo "Certificate updated. The change will take a few minutes to propagate."
echo "You can check the status with: kubectl get ingress oriane-pipeline-api-ingress -n oriane-pipeline-api"
