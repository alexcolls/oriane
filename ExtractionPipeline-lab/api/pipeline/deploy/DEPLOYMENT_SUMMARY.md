# Oriane Pipeline API Deployment Summary

## Issue Resolution

The issue was that the API documentation was not accessible at the expected `/docs` endpoint. After investigation, it was found that:

1. **Certificate Issue**: The ALB was using a placeholder certificate ARN instead of the actual certificate
2. **Endpoint Configuration**: The API documentation is available at a custom endpoint with different authentication

## What Was Fixed

### 1. Certificate Generation and Import
- ✅ Generated self-signed certificate using `./oriane-cert.sh`
- ✅ Imported certificate into AWS Certificate Manager
- ✅ Updated `.env` file with real certificate ARN: `arn:aws:acm:us-east-1:509399609859:certificate/cbe6cbc2-e765-4673-a714-bf532ab01592`

### 2. Infrastructure Setup
- ✅ Created and installed Helm via `deploy/install-helm.sh`
- ✅ Installed AWS Load Balancer Controller
- ✅ Tagged EKS subnets with required ALB discovery tags
- ✅ Updated Kubernetes ingress to use real certificate and proper domain

### 3. DNS Configuration
- ✅ Created Route 53 CNAME record pointing to ALB: `oriane-pipeline-api-alb-621628749.us-east-1.elb.amazonaws.com`
- ✅ DNS propagation completed successfully

## API Documentation Access

The API documentation is **NOT** available at `/docs` as initially expected. Instead, it's available at:

### Correct Endpoint
- **URL**: `https://pipeline.api.qdrant.admin.oriane.xyz/api/docs`
- **Authentication**: Basic Authentication (username/password)
- **Username**: `OrianeToTheMoon`
- **Password**: `HGJS98JHGL72K1SD8`

### Why This Configuration?
Looking at the FastAPI application code (`src/api/app.py`):
- Lines 57-58: Default docs disabled with `docs_url=None` and `openapi_url=None`
- Lines 266-268: Custom docs endpoint at `/api/docs` with basic authentication
- Lines 270-272: Custom OpenAPI endpoint at `/api/openapi.json` with basic authentication

## API Endpoints Summary

### Public Endpoints (No Authentication)
- **Root**: `https://pipeline.api.qdrant.admin.oriane.xyz/`
- **Health**: `https://pipeline.api.qdrant.admin.oriane.xyz/health`
- **Config**: `https://pipeline.api.qdrant.admin.oriane.xyz/config`

### Basic Auth Required (Username/Password)
- **API Documentation**: `https://pipeline.api.qdrant.admin.oriane.xyz/api/docs`
- **OpenAPI JSON**: `https://pipeline.api.qdrant.admin.oriane.xyz/api/openapi.json`

### API Key Required (X-API-Key Header)
- **Process Videos**: `POST https://pipeline.api.qdrant.admin.oriane.xyz/process`
- **Job Status**: `GET https://pipeline.api.qdrant.admin.oriane.xyz/status/{jobId}`
- **Jobs Management**: `https://pipeline.api.qdrant.admin.oriane.xyz/jobs/*`

## Testing the API

### Using Browser
1. Go to: `https://pipeline.api.qdrant.admin.oriane.xyz/api/docs`
2. Accept the self-signed certificate warning
3. Enter credentials:
   - Username: `OrianeToTheMoon`
   - Password: `HGJS98JHGL72K1SD8`

### Using curl
```bash
# Test root endpoint
curl --insecure https://pipeline.api.qdrant.admin.oriane.xyz/

# Test API documentation
curl --insecure -u "OrianeToTheMoon:HGJS98JHGL72K1SD8" https://pipeline.api.qdrant.admin.oriane.xyz/api/docs

# Test API endpoints with API key
curl --insecure -H "X-API-Key: KgsG2H54dyu2SBCBWGiifqvcb230hkjaghKSjkDDfs72v4siAu689yGBhjkaH7saA6L7N001EGzXYZb0x" https://pipeline.api.qdrant.admin.oriane.xyz/config
```

## Security Notes

1. **Self-Signed Certificate**: The certificate will show security warnings in browsers
2. **Basic Authentication**: API docs are protected with HTTP Basic Auth
3. **API Key Authentication**: Main API endpoints require `X-API-Key` header
4. **HTTPS Redirect**: HTTP traffic is automatically redirected to HTTPS

## Files Created/Modified

### Created
- `deploy/install-helm.sh` - Helm installation script
- `deploy/env/eks-alb.env` - ALB controller environment file
- `certs/oriane-certificate.pem` - Self-signed certificate
- `certs/oriane-private-key.pem` - Private key
- `test-api-endpoints.sh` - API testing script

### Modified
- `.env` - Updated with real certificate ARN
- `deploy/06-update-dns.sh` - Fixed ingress name reference

## Next Steps

If you need to access the API documentation at `/docs` instead of `/api/docs`, you would need to:
1. Modify `src/api/app.py` to enable default docs: `docs_url="/docs"`
2. Rebuild and redeploy the application
3. Consider the authentication requirements for the docs endpoint

The current configuration appears to be intentionally secured with basic authentication for the documentation endpoints.
