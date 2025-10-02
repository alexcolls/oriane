# 🎬 Video Processing Pipeline Documentation

## Overview

The video processing pipeline handles user uploaded videos by extracting frames, uploading them to S3, generating embeddings, and storing metadata in Qdrant. This implementation integrates directly with the core pipeline functions from `core/py/pipeline/src/`.

## Architecture

### 🔄 Processing Workflow

```
1. 📤 Video Upload
   └── Upload .mp4 to oriane-app/users/{user_id}/vid/{timestamp}.mp4

2. 🎬 Frame Extraction
   └── Use core/py/pipeline/src/scene_framing.py
   └── Extract frames to temp directory
   └── Format: {frame_number}_{frame_seconds}.png

3. ☁️ Frame Upload to S3
   └── Upload to oriane-frames/users/{user_id}/vid/{timestamp}/
   └── With retry logic and error handling

4. 🧠 Embedding Generation
   └── Use core/py/pipeline/src/infer_embeds.py
   └── Generate 512-dimensional CLIP embeddings

5. 💾 Store in Qdrant
   └── Save to user_videos collection
   └── Include frame metadata and S3 paths
```

## Implementation Details

### 📁 File Structure

```
api/
├── services/
│   └── video_processing_service.py    # Main video processing logic
├── controllers/add_content/
│   └── video.py                       # Video upload endpoint
└── tests/
    ├── test_add_content.py           # Video processing tests
    └── assets/
        └── video.mp4                 # Test video file
```

### 🔧 Core Components

#### VideoProcessingService
- **Location**: `services/video_processing_service.py`
- **Purpose**: Orchestrates the entire video processing pipeline
- **Key Methods**:
  - `process_video()` - Main processing method
  - `_extract_video_frames()` - Frame extraction using core pipeline
  - `_upload_frames_to_s3()` - S3 upload with retry logic
  - `_generate_embeddings()` - CLIP embedding generation
  - `_store_embeddings_in_qdrant()` - Qdrant storage

#### Video Controller
- **Location**: `controllers/add_content/video.py`
- **Purpose**: FastAPI endpoint for video uploads
- **Features**:
  - Video validation and upload to S3
  - Automatic processing pipeline trigger
  - Graceful error handling (video saved even if processing fails)

## S3 Storage Structure

### Video Storage (oriane-app bucket)
```
users/
└── {user_id}/
    └── vid/
        └── {timestamp}.mp4
```

### Frame Storage (oriane-frames bucket)
```
users/
└── {user_id}/
    └── vid/
        └── {timestamp}/
            ├── 1_0.50.png
            ├── 2_2.15.png
            ├── 3_5.32.png
            └── ...
```

## Qdrant Storage Schema

### Collection: `user_videos`
```json
{
  "collection_name": "user_videos",
  "vector_params": {
    "size": 512,
    "distance": "Cosine"
  },
  "payload_schema": {
    "id": "string (UUID)",
    "user_id": "string (user UUID)",
    "video_id": "string (video UUID)",
    "created_at": "string (ISO datetime)",
    "path": "string (S3 path to frame)",
    "frame_number": "integer",
    "frame_second": "float",
    "s3_url": "string (full S3 URL)"
  }
}
```

## API Endpoints

### POST `/add-content/video/{user_id}`

**Request:**
```bash
curl -X POST "http://localhost:8000/add-content/video/user-123" \
  -H "X-API-Key: your_api_key" \
  -F "file=@video.mp4"
```

**Response (Success):**
```json
{
  "message": "Video uploaded and processed successfully. Extracted 15 frames, uploaded 15 to S3, stored 15 embeddings in Qdrant.",
  "video_id": "uuid-v4-string",
  "video_url": "https://oriane-app.s3.region.amazonaws.com/users/user-123/vid/timestamp.mp4",
  "status": "processed",
  "processing_details": {
    "frames_extracted": 15,
    "frames_uploaded": 15,
    "embeddings_stored": 15,
    "processing_status": "completed"
  }
}
```

**Response (Upload Success, Processing Failed):**
```json
{
  "message": "Video uploaded successfully but processing failed: [error details]",
  "video_id": "uuid-v4-string",
  "video_url": "https://oriane-app.s3.region.amazonaws.com/users/user-123/vid/timestamp.mp4",
  "status": "upload_completed_processing_failed",
  "processing_details": {
    "error": "Detailed error message"
  }
}
```

## Error Handling

### Upload Errors
- Invalid file type (non-video)
- Empty file
- S3 upload failures
- Authentication errors

### Processing Errors
- Frame extraction failures
- Core pipeline errors
- S3 frame upload failures (with retry)
- Embedding generation failures
- Qdrant storage failures

### Graceful Degradation
- Video upload succeeds even if processing fails
- Partial frame uploads are logged but don't stop processing
- Detailed error reporting for debugging

## Testing

### Test Coverage
- ✅ Video upload success (with processing)
- ✅ Authentication tests (API key required)
- ✅ File validation (type, emptiness)
- ✅ Error handling scenarios
- ✅ Integration with existing test suite

### Test Assets
- Uses real video file: `tests/assets/video.mp4`
- Comprehensive integration testing
- Processing pipeline validation

## Configuration

### Environment Variables
```env
# S3 Configuration
S3_APP_BUCKET=oriane-app          # User content bucket
S3_FRAMES_BUCKET=oriane-frames    # Extracted frames bucket
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Video Processing Settings
VP_MIN_FRAMES=3                   # Minimum frames to extract
VP_SCENE_THRESH=0.22              # Scene change threshold
VP_BATCH_SIZE=8                   # Embedding batch size

# Qdrant Configuration
QDRANT_URL=https://your-qdrant:6333
QDRANT_KEY=your_qdrant_key
QDRANT_DIM=512
```

## Dependencies

### Core Pipeline
- `scene_framing.py` - Frame extraction
- `infer_embeds.py` - CLIP embeddings
- OpenCV for video processing
- FFmpeg for scene detection

### Python Packages
- FastAPI for API endpoints
- Boto3 for S3 operations
- Qdrant-client for vector storage
- PIL for image processing
- NumPy for array operations

## Performance Considerations

### Processing Time
- Frame extraction: ~2-10 seconds per video
- S3 upload: ~1-5 seconds depending on frame count
- Embedding generation: ~5-15 seconds depending on frame count and GPU
- Total: ~10-30 seconds per video

### Resource Usage
- Temporary disk space for frame storage
- GPU memory for embedding generation
- CPU for video processing

### Optimization
- Batch embedding generation
- Parallel S3 uploads (with retry)
- Temporary file cleanup
- CUDA acceleration when available

## Monitoring & Logging

### Logging Levels
- INFO: Processing progress and success
- WARNING: Retry attempts and partial failures
- ERROR: Critical failures and exceptions

### Metrics to Monitor
- Processing success rate
- Frame extraction count
- S3 upload failures
- Embedding generation time
- Qdrant storage success rate

---

**Video processing pipeline is ready for production use! 🎬✨**
