# Oriane Extraction Pipeline API

A FastAPI-based service for processing video extraction pipeline tasks including video cropping, scene frames extraction and deduplication, S3 storage, and frame embeddings extraction to remote Qdrant watched_frames collection.

## Table of Contents

- [Overview](#overview)
- [API Endpoints](#api-endpoints)
- [Request/Response Examples](#requestresponse-examples)
- [Job States & Logs](#job-states--logs)
- [Environment Variables](#environment-variables)
- [Authentication](#authentication)
- [Getting Started](#getting-started)
- [Docker Deployment](#docker-deployment)

## Overview

The Oriane Extraction Pipeline API provides a RESTful interface for processing video content through a sophisticated pipeline that includes:

- **Video Cropping**: Automatic border detection and removal using GPU-accelerated FFMPEG
- **Scene Detection**: Intelligent frame extraction based on scene changes
- **Frame Deduplication**: Perceptual hashing (dHash) to remove duplicate frames
- **S3 Storage**: Secure upload of processed frames to AWS S3
- **Vector Embeddings**: CLIP model-based frame embeddings stored in Qdrant vector database

## API Endpoints

### Core Processing Endpoints

#### `POST /process`
Submit a batch of videos for processing.

**Request Headers:**
- `X-API-Key`: Your API key for authentication
- `Content-Type: application/json`

**Request Body:**
```json
{
  "items": [
    {
      "platform": "instagram",
      "code": "DHrbLqfv-ka"
    },
    {
      "platform": "youtube", 
      "code": "dQw4w9WgXcQ"
    }
  ]
}
```

**Response (202 Accepted):**
```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### `GET /status/{jobId}`
Get job status and execution logs.

**Request Headers:**
- `X-API-Key`: Your API key for authentication

**Query Parameters:**
- `tail` (optional): Number of log lines to return (default: all)

**Response:**
```json
{
  "status": "running",
  "progress": 45,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:35:00Z",
  "items": [
    {
      "platform": "instagram",
      "code": "DHrbLqfv-ka"
    }
  ],
  "log_tail": "2024-01-15T10:35:00 [INFO] Processing video 1/2\n2024-01-15T10:35:15 [INFO] Extracting frames..."
}
```

### Jobs Management Endpoints

#### `GET /jobs`
List all processing jobs with pagination.

**Query Parameters:**
- `page` (default: 1): Page number
- `page_size` (default: 10): Number of jobs per page

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:40:00Z",
      "items": [...],
      "progress": {
        "completed": 2,
        "total": 2
      }
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 10
}
```

#### `POST /jobs`
Create a new processing job with advanced options.

**Request Body:**
```json
{
  "items": [
    {
      "platform": "instagram",
      "code": "DHrbLqfv-ka"
    }
  ],
  "batch_size": 10,
  "sleep_between_batches": 1.0,
  "local_mode": false,
  "skip_upload": false
}
```

#### `GET /jobs/{job_id}`
Get detailed information about a specific job.

#### `DELETE /jobs/{job_id}`
Delete a job from the system.

#### `POST /jobs/{job_id}/start`
Start or restart a job.

#### `POST /jobs/{job_id}/stop`
Stop a running job.

#### `GET /jobs/{job_id}/logs`
Get execution logs for a specific job.

#### `GET /jobs/{job_id}/progress`
Get detailed progress information for a job.

### Utility Endpoints

#### `GET /`
Health check and API information.

**Response:**
```json
{
  "status": "ok",
  "message": "Welcome to the Oriane Extraction Pipeline API",
  "version": "1.0.0",
  "api_name": "Oriane Extraction Pipeline API"
}
```

#### `GET /health`
Simple health check endpoint.

#### `GET /config`
Get current API configuration (non-sensitive values).

**Response:**
```json
{
  "api_name": "Oriane Extraction Pipeline API",
  "api_port": 8000,
  "max_workers": 4,
  "batch_size": 8,
  "sample_fps": 0.1,
  "crop_enabled": true,
  "dedup_enabled": true,
  "collection": "watched_frames",
  "clip_model": "jinaai/jina-clip-v2",
  "max_videos_per_request": 1000,
  "pipeline_max_parallel_jobs": 2
}
```

#### `GET /concurrency/stats`
Get concurrency manager statistics.

**Response:**
```json
{
  "active_jobs": 2,
  "max_parallel_jobs": 2,
  "pending_jobs": 0,
  "completed_jobs": 15,
  "failed_jobs": 1
}
```

## Request/Response Examples

### Process Instagram Videos

```bash
curl -X POST "http://localhost:8000/process" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "platform": "instagram",
        "code": "DHrbLqfv-ka"
      },
      {
        "platform": "instagram", 
        "code": "DI3l1xMJOyR"
      }
    ]
  }'
```

### Check Job Status

```bash
curl -X GET "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key-here"
```

### Get Job Status with Limited Logs

```bash
curl -X GET "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000?tail=50" \
  -H "X-API-Key: your-api-key-here"
```

### List All Jobs

```bash
curl -X GET "http://localhost:8000/jobs?page=1&page_size=20" \
  -H "X-API-Key: your-api-key-here"
```

### Create Advanced Job

```bash
curl -X POST "http://localhost:8000/jobs" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "platform": "youtube",
        "code": "dQw4w9WgXcQ"
      }
    ],
    "batch_size": 16,
    "sleep_between_batches": 0.5,
    "local_mode": false,
    "skip_upload": false
  }'
```

### Get Configuration

```bash
curl -X GET "http://localhost:8000/config" \
  -H "X-API-Key: your-api-key-here"
```

### Get Concurrency Statistics

```bash
curl -X GET "http://localhost:8000/concurrency/stats" \
  -H "X-API-Key: your-api-key-here"
```

## Job States & Logs

### Job States

The processing pipeline supports the following job states:

| State | Description |
|-------|-------------|
| `pending` | Job has been created and is waiting to be processed |
| `running` | Job is currently being processed |
| `completed` | Job has finished successfully |
| `failed` | Job encountered an error and could not complete |

### Job State Transitions

```
pending → running → completed
    ↓        ↓
    └── failed ←┘
```

### Log Format

Logs are structured with timestamps and log levels:

```
2024-01-15T10:30:00 [INFO] Created processing job 550e8400-e29b-41d4-a716-446655440000 with 2 items
2024-01-15T10:30:01 [INFO] Starting video processing pipeline
2024-01-15T10:30:05 [INFO] Processing video 1/2: instagram/DHrbLqfv-ka
2024-01-15T10:30:10 [INFO] Crop detection: 1920x1080 → 1680x1050 (12.5% reduction)
2024-01-15T10:30:15 [INFO] Scene detection: 24 scenes found
2024-01-15T10:30:20 [INFO] Frame extraction: 156 frames extracted
2024-01-15T10:30:25 [INFO] Deduplication: 156 → 142 frames (9.0% reduction)
2024-01-15T10:30:30 [INFO] S3 upload: 142 frames uploaded to oriane-frames/
2024-01-15T10:30:35 [INFO] Vector embedding: 142 embeddings stored in Qdrant
2024-01-15T10:30:40 [INFO] Processing video 2/2: instagram/DI3l1xMJOyR
2024-01-15T10:35:00 [INFO] Pipeline completed successfully
```

### Error Handling

When jobs fail, detailed error information is included in the logs:

```json
{
  "status": "failed",
  "progress": 25,
  "log_tail": "2024-01-15T10:30:00 [INFO] Processing video 1/2\n2024-01-15T10:30:15 [ERROR] Failed to download video: HTTP 404 Not Found\n2024-01-15T10:30:15 [ERROR] Pipeline execution failed"
}
```

## Environment Variables

### API Configuration

| Variable | Description | Default |
|----------|-------------|---------||
| `API_NAME` | API service name | `"Oriane Search API"` |
| `API_PORT` | Port for the API server | `8000` |
| `API_USERNAME` | Basic auth username | `""` |
| `API_PASSWORD` | Basic auth password | `""` |
| `API_KEY` | API key for authentication | `""` |
| `MAX_VIDEOS_PER_REQUEST` | Maximum videos per request | `1000` |
| `PIPELINE_MAX_PARALLEL_JOBS` | Maximum parallel jobs | `2` |
| `CORS_ORIGINS` | Allowed CORS origins | `"*"` |

### Pipeline Configuration

| Variable | Description | Default |
|----------|-------------|---------||
| `VP_OUTPUT_DIR` | Base output directory | `".output"` |
| `VP_TMP_DIR` | Temporary files directory | `".output/tmp/videos"` |
| `VP_FRAMES_DIR` | Extracted frames directory | `".output/tmp/frames"` |
| `VP_LOGS_DIR` | Pipeline logs directory | `".output/logs"` |
| `VP_REPORTS_DIR` | Processing reports directory | `".output/reports"` |

### Performance Tuning

| Variable | Description | Default |
|----------|-------------|---------||
| `VP_MAX_WORKERS` | FFMPEG crop threads | `4` |
| `VP_BATCH_SIZE` | CLIP micro-batch size | `8` |
| `VP_SAMPLE_FPS` | Fallback uniform sampling FPS | `0.1` |

### Feature Switches

| Variable | Description | Default |
|----------|-------------|---------||
| `VP_ENABLE_CROP` | Enable border crop detection | `1` |
| `VP_ENABLE_DEDUP` | Enable frame deduplication | `1` |

### AWS & S3 Configuration

| Variable | Description | Default |
|----------|-------------|---------||
| `AWS_REGION` | AWS region | `"us-east-1"` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `""` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `""` |
| `S3_BUCKET_NAME` | Main S3 bucket | `"oriane-contents"` |
| `S3_APP_BUCKET` | App content bucket | `"oriane-app"` |
| `S3_FRAMES_BUCKET` | Frames storage bucket | `"oriane-frames"` |

### Vector Database (Qdrant)

| Variable | Description | Default |
|----------|-------------|---------||
| `QDRANT_URL` | Qdrant server URL | `""` |
| `QDRANT_KEY` | Qdrant API key | `""` |
| `QDRANT_COLLECTION` | Collection name | `"watched_frames"` |
| `QDRANT_DIM` | Vector dimensions | `512` |
| `CLIP_MODEL` | CLIP model for embeddings | `"jinaai/jina-clip-v2"` |

### Video Processing Parameters

| Variable | Description | Default |
|----------|-------------|---------||
| `VP_SCENE_THRESH` | Scene change threshold | `0.22` |
| `VP_MIN_FRAMES` | Minimum frames per video | `3` |
| `VP_TOLERANCE` | Border detection tolerance | `5` |
| `VP_EDGE_THRESH` | Edge detection threshold | `10` |
| `VP_DHASH_SIZE` | dHash resolution | `8` |
| `VP_SOLID_STD` | Solid color standard deviation | `5.0` |
| `VP_SOLID_MIN_DIM` | Solid color minimum dimension | `10` |

### FFMPEG Cropping

| Variable | Description | Default |
|----------|-------------|---------||
| `VP_CROP_PROBES` | Number of crop detection probes | `3` |
| `VP_CROP_CLIP_SECS` | Clip duration for crop detection | `2` |
| `VP_CROP_SAFE_MARGIN` | Safe margin for crop detection | `4` |
| `VP_CROP_HWACCEL` | Hardware acceleration | `"cuda"` |
| `VP_CROP_CROPDETECT` | Crop detection parameters | `"24:16:0"` |
| `VP_CROP_ENCODER` | Video encoder | `"h264_nvenc"` |
| `VP_CROP_PRESET` | Encoder preset | `"p5"` |
| `VP_CROP_TUNE` | Encoder tuning | `"hq"` |
| `VP_CROP_CQ` | Constant quality | `"23"` |
| `VP_MIN_CROP_RATIO` | Minimum crop ratio | `0.10` |
| `VP_DOWNSCALE` | Downscale factor | `0.5` |

### Development Flags

| Variable | Description | Default |
|----------|-------------|---------||
| `LOCAL_MODE` | Skip database writes | `0` |
| `SKIP_UPLOAD` | Skip S3 frame uploads | `0` |

## Authentication

The API supports two authentication methods:

### API Key Authentication

Include your API key in the `X-API-Key` header:

```bash
curl -X GET "http://localhost:8000/config" \
  -H "X-API-Key: your-api-key-here"
```

### Basic Authentication

For accessing documentation endpoints:

```bash
curl -X GET "http://localhost:8000/api/docs" \
  -u "username:password"
```

## Getting Started

### Prerequisites

- Python 3.8+
- CUDA-compatible GPU (for video processing)
- Docker (optional)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/your-org/oriane-pipeline.git
cd oriane-pipeline/api/pipeline
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.sample .env
# Edit .env with your configuration
```

4. **Run the server:**
```bash
python3 main.py
```

### Docker Deployment

1. **Build the image:**
```bash
docker build -t oriane-pipeline:latest .
```

2. **Run with environment file:**
```bash
docker run -p 8000:8000 --env-file .env oriane-pipeline:latest
```

3. **Run with GPU support:**
```bash
docker run --gpus all -p 8000:8000 --env-file .env oriane-pipeline:latest
```

## Performance Considerations

See [Performance Tuning Guide](docs/performance.md) for detailed performance optimization recommendations.

## Deployment

**Important**: Always run scripts from project root; ensure .env is present there.

### EKS Deployment

See [EKS Deployment Guide](docs/deploy_eks.md) for Kubernetes deployment instructions.

### EKS AMI Update Script

The `scripts/update_eks_ami.sh` helper script automates the process of updating EKS version and AMI family in the deployment configuration.

#### Usage

```bash
# Update to EKS 1.33 with Amazon Linux 2023
./scripts/update_eks_ami.sh --eks-version 1.33 --ami-family AmazonLinux2023

# Update to EKS 1.32 with Amazon Linux 2
./scripts/update_eks_ami.sh --eks-version 1.32 --ami-family AmazonLinux2
```

#### Features

- **Validation**: Checks EKS version and AMI family compatibility
- **In-place Updates**: Uses `sed` to update the `deploy_to_eks.sh` script
- **Git Integration**: Automatically commits changes with descriptive messages
- **Backup**: Creates backup files before making changes
- **Verification**: Validates changes were applied correctly

#### Supported Parameters

| Parameter | Description | Valid Values |
|-----------|-------------|-------------|
| `--eks-version` | Target EKS version | `1.32`, `1.33`, etc. |
| `--ami-family` | AMI family to use | `AmazonLinux2023`, `AmazonLinux2` |

#### Compatibility Matrix

| EKS Version | AmazonLinux2 | AmazonLinux2023 |
|-------------|--------------|----------------|
| 1.32 | ✅ Supported | ✅ Supported |
| 1.33 | ❌ Not Available | ✅ Supported |

#### Example Output

```
[2024-01-15 10:30:00] Starting EKS AMI update process...
[2024-01-15 10:30:00] EKS Version: 1.33
[2024-01-15 10:30:00] AMI Family: AmazonLinux2023
[2024-01-15 10:30:00] Deploy Script: /path/to/deploy_to_eks.sh
[2024-01-15 10:30:01] Created backup: /path/to/deploy_to_eks.sh.backup
[SUCCESS] Updated EKS version references to 1.33
[SUCCESS] Updated AMI_FAMILY default to AmazonLinux2023
[SUCCESS] Updated SSM parameter path to use EKS version 1.33
[2024-01-15 10:30:02] Verifying changes...
[SUCCESS] Changes applied successfully
[2024-01-15 10:30:03] Changes committed to git
[2024-01-15 10:30:03] EKS AMI update completed successfully!
```

**Note**: The script requires a clean git working directory and will prompt for confirmation if uncommitted changes are detected.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
