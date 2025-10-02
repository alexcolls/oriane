# Video Extraction Pipeline API

**Author:** Alex Colls

A FastAPI-based video processing pipeline that extracts, crops, and processes video frames from various platforms. The API supports background job processing with structured logging and progress tracking.

## Features

- **Video Processing**: Extract and crop video frames from multiple platforms (Instagram, YouTube, etc.)
- **Background Jobs**: Asynchronous processing with job status tracking
- **Structured Logging**: Detailed logging with timestamps and log levels
- **Progress Tracking**: Real-time progress updates during processing
- **API Authentication**: Support for API key authentication
- **Scalable Architecture**: Built with FastAPI and supports concurrent processing

## Installation

### Prerequisites
- Python 3.8+
- Required environment variables (see Configuration section)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/video-extraction-pipeline.git
   cd video-extraction-pipeline/api/pipeline
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.sample .env
   # Edit .env with your configuration
   ```

4. Run the development server:
   ```bash
   ./scripts/start_dev.sh
   ```

## Configuration

### Environment Variables

The following environment variables are required:

- `API_KEY`: Authentication key for API access
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `MAX_VIDEOS_PER_REQUEST`: Maximum number of videos per request (default: 100)
- `DEBUG_PIPELINE`: Enable debug logging for pipeline execution (0 or 1)
- `PIPELINE_ENTRYPOINT`: Path to the pipeline entrypoint script
- `JOB_INPUT`: JSON string containing job items (set automatically)

### Database Configuration

- `DATABASE_URL`: Database connection string (if using persistent storage)
- `REDIS_URL`: Redis connection string (if using Redis for job storage)

## API Endpoints

### POST /process

Submit a batch of videos for processing.

**Request:**
```json
{
  "items": [
    {
      "platform": "instagram",
      "code": "ABC123"
    },
    {
      "platform": "youtube",
      "code": "XYZ789"
    }
  ]
}
```

**Response:**
```json
{
  "jobId": "123e4567-e89b-12d3-a456-426614174000"
}
```

### GET /status/{jobId}

Get job status and structured logs.

**Response:**
```json
{
  "status": "completed",
  "progress": 100,
  "createdAt": "2023-10-01T10:00:00Z",
  "updatedAt": "2023-10-01T10:05:00Z",
  "items": [
    {
      "platform": "instagram",
      "code": "ABC123"
    }
  ],
  "logs": [
    {
      "ts": "2023-10-01T10:00:05Z",
      "level": "INFO",
      "msg": "Starting video processing for item 1"
    },
    {
      "ts": "2023-10-01T10:00:10Z",
      "level": "INFO",
      "msg": "Processing completed successfully"
    }
  ]
}
```

## Scripts

### Migration Script

To migrate old log formats to the new structured logs array:

```bash
python3 scripts/migrate_logs.py
```

This script converts old `log` string fields to structured `logs[]` arrays for backward compatibility.

### Development Scripts

- `scripts/start_dev.sh`: Start development server
- `scripts/test.sh`: Run tests
- `scripts/docker_build.sh`: Build Docker image
- `scripts/run_gpu_container.sh`: Run GPU-enabled container
- `scripts/run_pipeline.sh`: Build and run container with environment variables

### Run Pipeline

To build and run the Docker container with the necessary environment variables, use:

```bash
./scripts/run_pipeline.sh
```

This script will:
1. Load environment variables from the `.env` file
2. Build the Docker image using the loaded configuration
3. Run the container with the `--env-file` flag to pass all environment variables

**Important**: Ensure you have the `.env` file set up with the required configurations before running the script. Copy `.env.sample` to `.env` and edit it with your credentials and settings.

## Development

### Running Tests

```bash
# Run all tests
./scripts/test.sh

# Run specific test file
python3 -m pytest tests/unit/test_api_functionality.py

# Run integration tests
python3 -m pytest tests/integration/
```

### Building for Production

```bash
# Build Docker image
./scripts/docker_build.sh

# Deploy to EKS
./deploy_to_eks.sh
```

## Logging

The API uses structured logging with the following format:

- **Timestamp**: ISO format with UTC timezone
- **Level**: INFO, ERROR, DEBUG, WARNING
- **Message**: Human-readable log message

Logs are stored in the job model and returned via the `/status/{jobId}` endpoint.

## Job Processing

Jobs are processed asynchronously with the following workflow:

1. **PENDING**: Job is queued for processing
2. **RUNNING**: Job is actively being processed
3. **COMPLETED**: Job finished successfully
4. **FAILED**: Job encountered an error

Progress is tracked as a percentage (0-100) and updated in real-time during processing.

## Deployment

The API can be deployed using:

- **Docker**: Use the provided Dockerfile
- **Kubernetes**: Use the deployment files in `deploy/kubernetes/`
- **AWS EKS**: Use the deployment scripts in `deploy/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Changelog

### v1.1.0
- Added structured logging with `logs[]` arrays
- Improved API response format
- Added migration script for backward compatibility
- Enhanced progress tracking
- Updated documentation with new examples
