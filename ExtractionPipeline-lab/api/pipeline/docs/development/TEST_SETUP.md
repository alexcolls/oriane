# Testing & CI Setup

This document describes the testing and CI/CD setup for the Pipeline API.

## Local Testing

### test/test_locally.sh

The updated local test script now tests the full process endpoint flow:

1. **POST /process** - Submits a job and gets a job ID
2. **Status Polling** - Repeatedly calls `/status/{jobId}` until completion
3. **Assertion** - Verifies the final status is `COMPLETED`

#### Usage

```bash
# Make sure you're in the project root
cd /path/to/pipeline/api

# Run the local test
./test/test_locally.sh
```

#### Test Flow

1. Starts the API server locally
2. Tests health endpoint
3. Submits a job via POST /process
4. Polls job status until completion (max 5 minutes)
5. Verifies final status is COMPLETED
6. Tests job persistence and jobs listing

#### Environment Variables

The test creates a temporary `.env` file with test configuration:

```env
API_NAME=Pipeline API Test
API_PORT=8000
API_KEY=test-key-123
API_USERNAME=testuser
API_PASSWORD=testpass
MAX_VIDEOS_PER_REQUEST=10
VP_OUTPUT_DIR=/tmp/pipeline-test
DEBUG_PIPELINE=1
LOCAL_MODE=1
SKIP_UPLOAD=1
```

## GitHub Actions CI/CD

### Workflow Structure

The CI pipeline follows this sequence:

1. **Build** - Build and push Docker image to GitHub Container Registry
2. **Unit Tests** - Run Python unit tests and integration tests
3. **Security Scan** - Run Trivy vulnerability scanner

### .github/workflows/ci.yml

#### Build Job

- Uses Docker Buildx for multi-platform builds
- Pushes to GitHub Container Registry (ghcr.io)
- Caches layers for faster builds
- Tags images with branch names and SHA

#### Unit Tests Job

- Runs the Docker image as a service
- Waits for API health check
- Executes Python unit tests
- Runs integration tests that mirror the local test flow:
  - POST /process endpoint
  - Status polling until completion
  - Assertion of COMPLETED status

#### Security Scan Job

- Runs Trivy vulnerability scanner
- Uploads results to GitHub Security tab
- Provides security insights for the Docker image

### Test Configuration

The CI environment uses these settings:

```yaml
env:
  API_NAME: "Pipeline API CI Test"
  API_PORT: 8000
  API_KEY: "ci-test-key-123"
  API_USERNAME: "testuser"
  API_PASSWORD: "testpass"
  MAX_VIDEOS_PER_REQUEST: 10
  VP_OUTPUT_DIR: "/tmp/pipeline-test"
  DEBUG_PIPELINE: 1
  LOCAL_MODE: 1
  SKIP_UPLOAD: 1
```

### Trigger Conditions

The workflow runs on:

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

### Docker Image Management

Images are tagged with:

- Branch name for branch pushes
- PR number for pull requests
- Git SHA for unique identification
- `latest` tag for default branch

### Health Checks

Docker services include health checks:

```yaml
options: >-
  --health-cmd "curl -f http://localhost:8000/health || exit 1"
  --health-interval 30s
  --health-timeout 10s
  --health-retries 5
```

## Key Features

### Process Flow Testing

Both local and CI tests verify:

1. ✅ POST /process creates job successfully
2. ✅ Job ID is returned correctly
3. ✅ Status polling works as expected
4. ✅ Job completes with COMPLETED status
5. ✅ Job status persists after completion
6. ✅ Jobs listing includes completed job

### Error Handling

Tests handle various scenarios:

- **API Startup Failures** - Fail fast if health check fails
- **Job Failures** - Display logs and exit with error
- **Timeouts** - Fail if job doesn't complete within time limit
- **Invalid Responses** - Handle malformed JSON or missing fields

### Cleanup

Both test environments include cleanup:

- Kill background processes
- Remove temporary files
- Clean up Docker containers

## Running Tests

### Local Development

```bash
# Run the comprehensive local test
./test/test_locally.sh

# Run existing API tests
./test_api_local.sh

# Run Docker tests
./test_docker_simple.sh
```

### CI/CD Pipeline

The pipeline runs automatically on:

- Every push to main/develop
- Every pull request
- Manual workflow dispatch

### Manual Testing

To test specific endpoints manually:

```bash
# Start API locally
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Test process endpoint
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-123" \
  -d '{"items": [{"platform": "instagram", "code": "test123"}]}'

# Poll status (replace JOB_ID with actual job ID)
curl "http://localhost:8000/status/JOB_ID" \
  -H "X-API-Key: test-key-123"
```

## Monitoring

### CI Dashboard

Check the Actions tab in GitHub to monitor:

- Build status
- Test results
- Security scan results
- Deployment status

### Local Monitoring

Local tests provide detailed output:

- Health check status
- Job creation confirmation
- Polling progress
- Final status verification
- Error details if failures occur

## Troubleshooting

### Common Issues

1. **API Startup Timeout**
   - Increase sleep time in test scripts
   - Check for port conflicts
   - Verify dependencies are installed

2. **Job Timeout**
   - Increase MAX_ATTEMPTS in polling logic
   - Check LOCAL_MODE and SKIP_UPLOAD settings
   - Review job logs for processing issues

3. **Docker Build Failures**
   - Check Dockerfile syntax
   - Verify all dependencies are available
   - Review build logs in Actions tab

### Debug Mode

Enable debug mode by setting:

```env
DEBUG_PIPELINE=1
```

This provides additional logging for troubleshooting.

## Future Enhancements

1. **Parallel Testing** - Run multiple job types simultaneously
2. **Performance Testing** - Add load testing scenarios
3. **End-to-End Testing** - Test with real video processing
4. **Monitoring Integration** - Add metrics collection
5. **Test Coverage** - Add code coverage reporting
