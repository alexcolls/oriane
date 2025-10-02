# Scene-Based Video Frame Extractor (AWS Lambda)

A Python-based AWS Lambda function that extracts key frames from videos using scene detection technology. The service automatically processes videos stored in S3, detects scene changes, and extracts representative frames from each scene.

## Overview

This service is designed to:
1. Process videos from S3 buckets
2. Detect scene changes using PySceneDetect
3. Extract representative frames from each scene
4. Upload frames to S3
5. Track processing status in Supabase

## Architecture

- **Runtime**: Python on AWS Lambda
- **Storage**: AWS S3 for videos and frames
- **Database**: Supabase for status tracking
- **Queue**: SQS for processing requests
- **Container**: Deployed as a Docker container on ECR

## Environment Configuration

Create a `.env` file based on `.env.sample`. The configuration is organized into several sections:

### S3 Settings
```bash
S3_BUCKET_VIDEOS=oriane-contents    # Bucket for source videos
S3_BUCKET_FRAMES=oriane-contents    # Bucket for extracted frames
```

### Supabase Configuration
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-service-role-key
```

### Extraction Settings
```bash
MIN_FRAMES=3          # Minimum frames per video if scenes < MIN_FRAMES
SCENE_THRESHOLD=27.0  # PySceneDetect content-detector threshold
```

### Performance Tuning
```bash
CONCURRENCY_LIMIT=2   # How many videos to process in parallel
MIN_REMAINING_MS=60000  # Lambda timeout buffer (ms)
S3_RETRIES=3         # Number of retries for S3 operations
S3_RETRY_DELAY=1000  # Delay between retries (ms)
S3_CONNECT_TIMEOUT=10 # S3 connection timeout (seconds)
S3_READ_TIMEOUT=60   # S3 read timeout (seconds)
```

### Debug Settings
```bash
DEBUG=true           # Enable debug-level logging
```

## Core Features

- Scene-based frame extraction using content detection
- Fallback to evenly-spaced frames if minimum scene count not met
- Parallel frame upload to S3
- Comprehensive error handling and logging
- Configurable thresholds and limits

## Input Format

The Lambda function expects SQS messages in the following format:
```json
{
    "shortcode": "VIDEO_ID",
    "platform": "PLATFORM_NAME"
}
```

## Lambda Function Workflow

The Lambda function processes videos through several distinct steps:

### 1. Record Processing Initialization
- Receives SQS event containing video records
- Parses the record body to extract `shortcode` and `platform`
- Sets up logging context with the video's shortcode
- Checks remaining Lambda execution time to prevent timeouts

### 2. Video Status Verification
- Queries Supabase to check video status:
  - `is_downloaded`: Confirms video exists in S3
  - `is_extracted`: Prevents duplicate processing
- Skips processing if video isn't downloaded or already extracted
- Records status in extraction_errors table if needed

### 3. Video Download
- Constructs S3 key path: `{platform}/{code}/video.mp4`
- Downloads video to temporary local storage
- Implements retry logic with configurable attempts
- Verifies download success before proceeding

### 4. Frame Extraction
- Detects scene changes using PySceneDetect:
  - Uses ContentDetector with configurable threshold
  - Identifies major visual transitions
- Selects representative frames:
  - Takes middle frame from each detected scene
  - Falls back to evenly-spaced frames if scene count < MIN_FRAMES
- Saves frames as JPEG files in temporary directory

### 5. Frame Upload
- Uploads extracted frames to S3:
  - Destination path: `{platform}/{code}/frames/{index}.jpg`
  - Uses parallel upload with ThreadPoolExecutor
  - Implements retry logic for failed uploads
- Cleans up temporary files after upload

### 6. Status Updates
- Updates Supabase on successful extraction:
  - Sets `is_extracted = true`
  - Records the number of extracted frames
- Records any errors in extraction_errors table
- Cleans up all temporary files and resources

### 7. Concurrency Handling
- Processes multiple videos in parallel
- Respects CONCURRENCY_LIMIT setting
- Aggregates results from all processed videos
- Returns comprehensive status report

## Testing

A test suite (`test.py`) is provided for local testing and validation:

```bash
# Run all tests
python3 test.py
```

The test suite includes:
- Bulk extraction testing
- Single video processing
- Debug mode for detailed logging

## Deployment

Use the provided `push_image.sh` script to build and deploy to AWS ECR:

```bash
# Build and deploy Docker image
./push_image.sh
```

The script handles:
- ECR repository creation
- Docker image building
- Authentication
- Image pushing with timeout handling

## Error Handling

The service includes comprehensive error handling for:
- Missing or corrupted videos
- Scene detection failures
- S3 upload/download issues
- Database connection problems
- Lambda timeout prevention

## Dependencies

Main Python packages:
- `opencv-python`: Video frame extraction
- `scenedetect`: Scene change detection
- `boto3`: AWS SDK
- `supabase`: Database client

## Logging

The service provides detailed logging with:
- Configurable debug mode
- Shortcode-based context
- Operation tracking
- Error reporting

## Setup Instructions

1. Clone the repository
2. Copy `.env.sample` to `.env`
3. Update the environment variables in `.env` with your credentials
4. Install dependencies
5. Run tests to verify setup
6. Deploy using the deployment script

## Notes

- The service requires appropriate AWS IAM permissions for S3 and Lambda
- Supabase credentials must be configured before deployment
- Consider Lambda timeout limits when processing longer videos
- Monitor S3 costs for video and frame storage
- Keep your `.env` file secure and never commit it to version control

## Contributing

1. Ensure all tests pass locally
2. Maintain the existing error handling patterns
3. Update documentation for any new features
4. Follow the established logging conventions
5. Update `.env.sample` if adding new configuration options
