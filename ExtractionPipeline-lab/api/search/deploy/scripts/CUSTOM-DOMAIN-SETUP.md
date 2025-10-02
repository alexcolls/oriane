# Custom Domain Setup Guide

This guide explains how to deploy both Pipeline and Search APIs with custom domains on EKS.

## Target Domains

- **Pipeline API**: `pipeline.api.qdrant.admin.oriane.xyz`
- **Search API**: `search.api.qdrant.admin.oriane.xyz`

## Prerequisites

1. **SSL Certificate**: You need an SSL certificate in AWS Certificate Manager (ACM) for `*.qdrant.admin.oriane.xyz`
2. **DNS Control**: Access to modify DNS records for `qdrant.admin.oriane.xyz`
3. **AWS Permissions**: EKS, ALB, Route53, ACM permissions

## Step 1: Create SSL Certificate

First, create a wildcard SSL certificate in ACM:

```bash
# Request certificate
aws acm request-certificate \
    --domain-name "*.qdrant.admin.oriane.xyz" \
    --subject-alternative-names "qdrant.admin.oriane.xyz" \
    --validation-method DNS \
    --region us-east-1

# Note the CertificateArn from the output
```

Validate the certificate in the ACM console by adding the DNS records to your domain.

## Step 2: Set Environment Variables

```bash
export AWS_ACCOUNT_ID="509399609859"
export AWS_REGION="us-east-1"
export EKS_CLUSTER_NAME="oriane-search-api-cluster"
export SSL_CERT_ARN="arn:aws:acm:us-east-1:509399609859:certificate/YOUR_CERT_ID"
```

## Step 3: Run Deployment Script

```bash
./deploy-with-domains.sh
```

This script will:
1. Install AWS Load Balancer Controller
2. Deploy both APIs with ingress configurations
3. Create Application Load Balancers
4. Show you the ALB hostnames for DNS configuration

## Step 4: Configure DNS

After deployment, you'll get ALB hostnames. Create CNAME records:

```
pipeline.api.qdrant.admin.oriane.xyz -> k8s-oriane-pipelineapi-xxx.us-east-1.elb.amazonaws.com
search.api.qdrant.admin.oriane.xyz   -> k8s-oriane-searchapi-xxx.us-east-1.elb.amazonaws.com
```

## Step 5: Access APIs

Once DNS propagates (usually 5-15 minutes):

- Pipeline API docs: https://pipeline.api.qdrant.admin.oriane.xyz/docs
- Search API docs: https://search.api.qdrant.admin.oriane.xyz/docs

## Troubleshooting

### Check Ingress Status
```bash
kubectl get ingress -n pipeline
kubectl get ingress -n search
```

### Check Load Balancer Controller
```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

### Check ALB Target Groups
```bash
aws elbv2 describe-target-groups --region us-east-1
aws elbv2 describe-target-health --target-group-arn <target-group-arn>
```

### Verify Certificate
```bash
aws acm list-certificates --region us-east-1
aws acm describe-certificate --certificate-arn <cert-arn>
```

## Manual DNS Configuration

If you're using Route 53, you can create the records programmatically:

```bash
# Get ALB hostnames
PIPELINE_ALB=$(kubectl get ingress pipeline-api-ingress -n pipeline -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
SEARCH_ALB=$(kubectl get ingress search-api-ingress -n search -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Create Route 53 records (replace HOSTED_ZONE_ID)
aws route53 change-resource-record-sets --hosted-zone-id YOUR_HOSTED_ZONE_ID --change-batch '{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "pipeline.api.qdrant.admin.oriane.xyz",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{"Value": "'$PIPELINE_ALB'"}]
    }
  }, {
    "Action": "CREATE", 
    "ResourceRecordSet": {
      "Name": "search.api.qdrant.admin.oriane.xyz",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{"Value": "'$SEARCH_ALB'"}]
    }
  }]
}'
```

## Security Notes

- All traffic is HTTPS with SSL certificates
- APIs are accessible from the internet (adjust ingress annotations for private access if needed)
- Consider adding authentication/authorization for production use
