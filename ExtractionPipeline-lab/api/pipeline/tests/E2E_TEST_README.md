# E2E Local Job Test

This directory contains the `e2e_local_job.sh` script that automates end-to-end testing of the pipeline API.

## What it does

The script performs the following actions:

1. **Spins up the dev container** - Builds and starts a Docker container with the pipeline API
2. **Creates a dummy job** - Submits a test job through the `/process` API endpoint
3. **Polls job status** - Continuously checks the job status via `/status/{jobId}` endpoint
4. **Prints final status** - Displays the final job results and details
5. **Cleanup** - Automatically stops and removes the Docker container

## Requirements

- Docker
- curl
- jq (for JSON parsing)
- lsof (for port checking)

## Usage

```bash
# Run the E2E test
./e2e_local_job.sh
```

## Configuration

The script uses environment variables from the `.env` file:

- `API_HOST` - API hostname (default: localhost)
- `API_PORT` - API port (default: 8000)
- `API_KEY` - API key for authentication
- `LOCAL_MODE` - Set to 1 to skip database writes
- `SKIP_UPLOAD` - Set to 1 to skip S3 uploads

## Features

- **Automatic cleanup** - Container is always cleaned up on exit
- **Port conflict handling** - Automatically kills processes using the API port
- **Health checks** - Waits for API to be ready before testing
- **Colorized output** - Uses colors for better visibility
- **Error handling** - Comprehensive error checking and reporting
- **Timeout protection** - Prevents infinite polling

## Sample Output

```
[2024-01-15 10:30:00] Starting E2E local job test...
[2024-01-15 10:30:01] Building Docker image...
[2024-01-15 10:30:30] Starting container: pipeline-api-dev
[2024-01-15 10:30:31] Waiting for API to be ready...
[SUCCESS] API is ready!
[2024-01-15 10:30:35] Creating test job...
[SUCCESS] Job created with ID: 12345678-1234-5678-9012-123456789012
[2024-01-15 10:30:36] Polling job status for ID: 12345678-1234-5678-9012-123456789012
[2024-01-15 10:30:36] Job status: pending (progress: 0%)
[2024-01-15 10:30:41] Job status: running (progress: 50%)
[2024-01-15 10:30:46] Job status: completed (progress: 100%)
[SUCCESS] Job completed successfully!
[2024-01-15 10:30:46] Final job details:
{
  "status": "completed",
  "progress": 100,
  "createdAt": "2024-01-15T10:30:35Z",
  "updatedAt": "2024-01-15T10:30:46Z",
  "items": [
    {
      "platform": "instagram",
      "code": "DHrbLqfv-ka"
    }
  ]
}
[2024-01-15 10:30:46] Cleaning up resources...
[2024-01-15 10:30:47] Stopping and removing container: pipeline-api-dev
[SUCCESS] Cleanup completed
[SUCCESS] E2E test completed successfully!
```

## Troubleshooting

### Port Already in Use
If port 8000 is already in use, the script will automatically attempt to kill the conflicting process.

### Docker Image Build Fails
Make sure you're running the script from the correct directory and that all dependencies are properly installed.

### API Key Issues
Ensure the `API_KEY` environment variable is set in the `.env` file.

### Container Startup Issues
Check Docker logs for detailed error messages:
```bash
docker logs pipeline-api-dev
```
