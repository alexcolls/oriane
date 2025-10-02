# VideoFramesExtractorBulk-lambda

AWS Lambda function responsible for retrieving videos from the S3 bucket oriane-videos, extracting frames (by default one frame per second) using FFmpeg, and storing the images in the S3 bucket oriane-frames.

Overview
A high-performance, serverless solution for extracting frames from videos at scale. Built with AWS Lambda using Node.js and TypeScript, this service efficiently processes videos stored in S3, extracts frames using FFmpeg, and manages workloads through SQS queuing.

## Architecture
![Architecture Diagram]

## Key Features
- **Serverless Architecture**: Leverages AWS Lambda for scalable, cost-effective processing
- **Containerized Solution**: Docker-based deployment ensures consistent environments
- **Batch Processing**: Efficient handling of multiple videos through SQS queuing
- **Intelligent Frame Extraction**: 
  - Multiple extraction strategies (uniform/keyframe)
  - Configurable frame intervals
  - Quality control parameters
- **Progress Tracking**: Real-time logging and progress monitoring
- **Memory Optimization**: Efficient handling of large video files
- **State Management**: Supabase integration for reliable state tracking

## Technical Stack
- **AWS Services**: Lambda, S3, SQS, ECR
- **Database**: Supabase
- **Core Technologies**: Python 3.8+, OpenCV, FFmpeg
- **Container**: Docker
- **Dependencies**: boto3, opencv-python, ffmpeg-python

## Setup and Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed
- Python 3.8 or higher
- Supabase account and project

### Environment Configuration
1. Create `.env` file:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

2. Configure AWS resources:
```bash
# Create S3 buckets
aws s3 mb s3://oriane-videos
aws s3 mb s3://oriane-frames

# Create ECR repository
aws ecr create-repository --repository-name video-frames-extractor
```

### Installation
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Build and deploy Docker image:
```bash
./scripts/build_docker.sh
```

## Usage

### Running Batch Processing
```python
# Queue videos for processing
python run_sqs_batches.py
```

### Lambda Function Configuration
- Memory: 2048 MB (recommended)
- Timeout: 5 minutes
- Environment variables:
  - `S3_BUCKET_VIDEOS`
  - `S3_BUCKET_FRAMES`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`

### Customization Options
```python
# Frame extraction parameters
extract_frames(
    video_path,
    output_dir,
    frame_interval=1,    # Extract every nth frame
    quality=95,          # JPEG quality (1-100)
    max_frames=None,     # Limit total frames
    strategy='uniform'   # 'uniform' or 'keyframe'
)
```

## Project Structure
```
├── lambda_function.py        # Main Lambda handler
├── run_sqs_batches.py       # SQS batch processor
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── scripts/
│   └── build_docker.sh    # Docker build script
└── .env                   # Environment variables
```

## Database Schema

### Supabase Table: watched_content
| Column       | Type    | Description                    |
|-------------|---------|--------------------------------|
| code        | string  | Video identifier               |
| is_fetched  | boolean | Video download status          |
| is_extracted| boolean | Frame extraction status        |

## Error Handling
- Comprehensive error logging
- Automatic retries for transient failures
- Dead-letter queue support
- State management through Supabase

## Performance Optimization
- Memory-efficient frame processing
- Batch operations for SQS messages
- Configurable processing intervals
- Docker layer optimization

## Monitoring and Logging
- CloudWatch integration
- Progress tracking
- Performance metrics
- Error reporting

## Security
- IAM role-based access
- Environment variable encryption
- S3 bucket policies
- Network isolation

## Contributing
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

## Support
For issues and feature requests, please create an issue in the repository.

---
Maintained by Oriane XYZ
