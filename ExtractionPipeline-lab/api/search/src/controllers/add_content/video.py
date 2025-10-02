from __future__ import annotations

"""Video controller

Provides thin convenience wrappers around the central CLIP embedding
utilities that live under `core/py/pipeline/src` so that the API layer
can stay agnostic of the underlying module layout.
"""

import datetime
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Path, UploadFile
from pydantic import BaseModel

# Import services
try:
    from services import upload_to_s3_service, video_processing_service
except ImportError:
    from ...services import upload_to_s3_service, video_processing_service

try:
    from config.env_config import settings
except ImportError:
    from ...config.env_config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class VideoUploadResponse(BaseModel):
    message: str
    video_id: str
    video_url: str
    status: str
    processing_details: dict = None


@router.post("/{user_id}", response_model=VideoUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(..., description="The video file to upload."),
    user_id: str = Path(..., description="The UUID of the user uploading the video."),
):
    """
    Accepts a video, uploads it to S3, and processes it for frame extraction and embedding generation.

    The video_id (UUID) is used as the video_folder identifier for organizing video files,
    while video_folder represents the UUID folder when the upload occurred.
    For full video processing, AWS Batch configuration is required.
    """

    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video.")

    try:
        # Read video file
        video_bytes = await file.read()
        if not video_bytes:
            raise HTTPException(status_code=400, detail="Empty video file.")

        # Get file extension
        file_extension = "mp4"  # Default to mp4
        if file.filename and "." in file.filename:
            file_extension = file.filename.split(".")[-1].lower()
            if file_extension not in ["mp4", "avi", "mov", "mkv", "webm"]:
                file_extension = "mp4"  # Fallback to mp4

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid video file: {str(exc)}")

    # Generate unique video ID and timestamp
    video_id = str(uuid.uuid4())
    video_folder = datetime.datetime.now(datetime.timezone.utc)

    # Create S3 object path: users/<user-uuid>/vid/<video-uuid>.mp4
    s3_object_key = f"users/{user_id}/vid/{video_id}.mp4"

    try:
        # Step 1: Upload video to S3
        logger.info(f"Uploading video to S3: {s3_object_key}")
        upload_to_s3_service.upload_file_to_s3(
            file_bytes=video_bytes, object_name=s3_object_key, bucket_name=settings.s3_app_bucket
        )

        # Generate S3 URL
        video_url = f"https://{settings.s3_app_bucket}.s3.{settings.aws_region}.amazonaws.com/{s3_object_key}"

        logger.info(f"Successfully uploaded video {video_id} for user {user_id}")

        # Step 2: Process video (extract frames, generate embeddings, store in Qdrant)
        try:
            logger.info(f"Starting video processing for {video_id}")
            processing_result = video_processing_service.process_user_video(
                video_s3_path=s3_object_key,
                user_id=user_id,
                video_folder=video_id,  # Use video_id as the video_folder identifier
                video_id=video_id,
            )

            status_message = f"Video uploaded and processed successfully. "
            status_message += f"Extracted {processing_result['frames_extracted']} frames, "
            status_message += f"uploaded {processing_result['frames_uploaded']} to S3, "
            status_message += (
                f"stored {processing_result['embeddings_stored']} embeddings in Qdrant."
            )

            return {
                "message": status_message,
                "video_id": video_id,
                "video_url": video_url,
                "status": "processed",
                "processing_details": processing_result,
            }

        except Exception as processing_error:
            logger.error(f"Video processing failed for {video_id}: {str(processing_error)}")

            # Video was uploaded successfully but processing failed
            status_message = (
                f"Video uploaded successfully but processing failed: {str(processing_error)}"
            )

            return {
                "message": status_message,
                "video_id": video_id,
                "video_url": video_url,
                "status": "upload_completed_processing_failed",
                "processing_details": {"error": str(processing_error)},
            }

    except Exception as exc:
        logger.error(f"Failed to upload video {video_id}: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload video: {str(exc)}")
