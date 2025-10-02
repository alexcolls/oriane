#!/bin/bash
set -e

REGION="us-east-1"
SERVICE_NAME="OrianeSearchAPIv1_dev2"

# 1) Get the service ARN
SERVICE_ARN=$(aws apprunner list-services \
  --region "$REGION" \
  --query "ServiceSummaryList[?ServiceName=='${SERVICE_NAME}'].ServiceArn" \
  --output text)

echo "Waiting for App Runner service '$SERVICE_NAME' to become RUNNING..."

# 2) Poll until Status is RUNNING (or exit on FAILED)
while true; do
  STATUS=$(aws apprunner describe-service \
    --region "$REGION" \
    --service-arn "$SERVICE_ARN" \
    --query "Service.Status" \
    --output text)
  echo "  ➤ Current status: $STATUS"
  if [[ "$STATUS" == "RUNNING" ]]; then
    break
  elif [[ "$STATUS" == "FAILED" ]]; then
    echo "✖ Deployment failed."
    exit 1
  fi
  sleep 10
done

# 3) Fetch the public URL
SERVICE_URL=$(aws apprunner describe-service \
  --region "$REGION" \
  --service-arn "$SERVICE_ARN" \
  --query "Service.ServiceUrl" \
  --output text)

echo "✅ Service is RUNNING at: https://$SERVICE_URL"

# 4) Hit the health endpoint
echo "🩺 Testing /health..."
curl -v "https://$SERVICE_URL/health"
