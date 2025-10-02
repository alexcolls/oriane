# Image Upload Controller

## Overview

The image upload controller (`controllers/add_content/image.py`) provides endpoints for uploading user images to S3 and storing their embeddings in the Qdrant `user_images` collection.

## Endpoints

### 1. Single Image Upload

**Endpoint:** `POST /add-content/image/{user_id}`

**Description:** Uploads a single image to S3, generates embeddings, and stores metadata in Qdrant.

**Parameters:**

- `user_id` (path): UUID of the user uploading the image
- `file` (form-data): The image file to upload

**Response:**

```json
{
  "message": "Image uploaded and processed successfully.",
  "image_id": "uuid-v4-string",
  "image_url": "https://oriane-app.s3.region.amazonaws.com/users/{user_id}/img/{timestamp}.png",
  "status": "stored"
}
```

### 2. Batch Image Upload

**Endpoint:** `POST /add-content/image/batch/{user_id}`

**Description:** Uploads multiple images to S3, generates embeddings, and stores metadata in Qdrant.

**Parameters:**

- `user_id` (path): UUID of the user uploading the images
- `files` (form-data): Multiple image files to upload (max 50)

**Response:**

```json
{
  "message": "Batch upload completed. X successful, Y failed.",
  "successful_uploads": [
    {
      "image_id": "uuid-v4-string",
      "image_url": "https://oriane-app.s3.region.amazonaws.com/users/{user_id}/img/{timestamp}.png",
      "filename": "original_filename.jpg"
    }
  ],
  "failed_uploads": [
    {
      "filename": "failed_file.txt",
      "error": "File must be an image."
    }
  ],
  "total_processed": 2
}
```

## Storage Details

### S3 Storage

- **Bucket:** `oriane-app` (configured via `S3_APP_BUCKET`)
- **Path Structure:** `users/{user_uuid}/img/{datetime}.png`
- **Format:** All images are standardized to PNG format
- **DateTime Format:** `YYYYMMDD_HHMMSS_microseconds`

### Qdrant Storage

- **Collection:** `user_images`
- **Vector Size:** 512 dimensions (CLIP embeddings)
- **Distance Metric:** Cosine

**Payload Structure:**

```json
{
  "id": "image_id",
  "user_id": "user_uuid",
  "image_id": "image_id",
  "created_at": "2023-12-27T19:30:45.123456+00:00",
  "path": "users/{user_id}/img/{timestamp}.png",
  "filename": "original_filename.jpg",
  "content_type": "image/png",
  "size_bytes": 1234567,
  "image_size": "1920x1080",
  "s3_url": "https://oriane-app.s3.region.amazonaws.com/...",
  "upload_type": "single_image" // or "batch_image"
}
```

## Authentication

Both endpoints require API key authentication via the `X-API-Key` header.

## Error Handling

- **400 Bad Request:** Invalid image file, empty file, or validation errors
- **401 Unauthorized:** Missing or invalid API key
- **500 Internal Server Error:** S3 upload failures, Qdrant storage failures, or embedding generation errors

## Dependencies

- **Services:**
  - `embeddings_service`: For generating CLIP embeddings
  - `qdrant_service`: For vector database operations
  - `upload_to_s3_service`: For S3 file uploads
- **Models:** CLIP model (jinaai/jina-clip-v2)
- **Storage:** AWS S3, Qdrant vector database

## Environment Variables Required

Add these to your `.env` file:

```env
# S3 Configuration
S3_APP_BUCKET=oriane-app
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Qdrant Configuration
QDRANT_URL=https://your-qdrant-endpoint:6333
QDRANT_KEY=your_qdrant_api_key
QDRANT_DIM=512
```
