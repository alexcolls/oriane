from __future__ import annotations

"""Video Processing Service

Handles video frame extraction, S3 upload, and Qdrant storage for user videos.
Uses the core pipeline functions for frame extraction and embedding generation.
"""

import datetime
import logging
import os
import shutil

# Import core pipeline functions
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException

# Add the core pipeline to Python path
core_path = os.path.join(os.path.dirname(__file__), "../../core/py/pipeline/src")
if core_path not in sys.path:
    sys.path.insert(0, core_path)

try:
    from infer_embeds import encode_directory
    from scene_framing import extract_frames
except ImportError as e:
    logging.error(f"Failed to import core pipeline functions: {e}")
    # Fallback for when core pipeline is not available
    extract_frames = None
    encode_directory = None

# Import local services
try:
    from services import qdrant_service, upload_to_s3_service
except ImportError:
    from . import qdrant_service, upload_to_s3_service

try:
    from config.env_config import settings
except ImportError:
    from ..config.env_config import settings

logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """Custom exception for video processing errors."""

    pass


class VideoProcessingService:
    """Service for processing user uploaded videos."""

    def __init__(self):
        self.max_retry_attempts = 3
        self.frames_upload_bucket = settings.s3_frames_bucket  # oriane-frames
        self.user_video_bucket = settings.s3_app_bucket  # oriane-app

    def process_video(
        self, video_path: str, user_id: str, video_folder: str, video_id: str
    ) -> Dict[str, Any]:
        """
        Process a video: extract frames, upload to S3, and store embeddings in Qdrant.

        Args:
            video_path: S3 path to the uploaded video
            user_id: UUID of the user
            video_folder: UUID folder name for organizing video files
            video_id: Unique identifier for this video

        Returns:
            Dict with processing results
        """
        if not extract_frames or not encode_directory:
            raise VideoProcessingError("Core pipeline functions not available")

        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                # Step 1: Download video from S3 to temp directory
                logger.info(f"Processing video for user {user_id}: {video_path}")
                local_video_path = self._download_video_from_s3(video_path, temp_path)

                # Step 2: Extract frames using core pipeline
                frames_dir = temp_path / "frames"
                frames_dir.mkdir(exist_ok=True)
                frame_paths = self._extract_video_frames(local_video_path, frames_dir)

                if not frame_paths:
                    raise VideoProcessingError("No frames extracted from video")

                logger.info(f"Extracted {len(frame_paths)} frames from video")

                # Step 3: Upload frames to S3 (oriane-frames bucket)
                s3_frame_info = self._upload_frames_to_s3(frame_paths, user_id, video_folder)

                # Step 4: Generate embeddings from local frames
                embeddings = self._generate_embeddings(frames_dir)

                # Step 5: Store embeddings in Qdrant user_videos collection
                stored_count = self._store_embeddings_in_qdrant(
                    embeddings, s3_frame_info, user_id, video_id, video_folder
                )

                return {
                    "frames_extracted": len(frame_paths),
                    "frames_uploaded": len(s3_frame_info),
                    "embeddings_stored": stored_count,
                    "processing_status": "completed",
                }

            except Exception as e:
                logger.error(f"Video processing failed for {video_path}: {str(e)}")
                raise VideoProcessingError(f"Video processing failed: {str(e)}")

    def _download_video_from_s3(self, s3_path: str, temp_dir: Path) -> Path:
        """Download video from S3 to local temporary directory."""
        try:
            import boto3
            from botocore.exceptions import ClientError

            # Initialize S3 client
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.aws_region,
            )

            # Extract bucket and key from s3_path
            # s3_path format: users/user_id/vid/video_id.mp4
            bucket = self.user_video_bucket
            key = s3_path

            # Download to temporary file
            local_video_path = temp_dir / "video.mp4"
            s3_client.download_file(bucket, key, str(local_video_path))

            logger.info(f"Downloaded video from s3://{bucket}/{key} to {local_video_path}")
            return local_video_path

        except ClientError as e:
            raise VideoProcessingError(f"Failed to download video from S3: {e}")
        except Exception as e:
            raise VideoProcessingError(f"Unexpected error downloading video: {e}")

    def _extract_video_frames(self, video_path: Path, frames_dir: Path) -> List[Path]:
        """Extract frames from video using core pipeline."""
        try:
            logger.info(f"Extracting frames from {video_path}")

            # Use core pipeline frame extraction
            frame_paths = extract_frames(
                video=video_path,
                outdir=frames_dir,
                min_frames=getattr(settings, "min_frames", 3),
                scene_thresh=getattr(settings, "scene_thresh", 0.22),
            )

            logger.info(f"Core pipeline extracted {len(frame_paths)} frames")
            return frame_paths

        except Exception as e:
            raise VideoProcessingError(f"Frame extraction failed: {e}")

    def _upload_frames_to_s3(
        self, frame_paths: List[Path], user_id: str, video_folder: str
    ) -> List[Dict[str, Any]]:
        """Upload frames to S3 and return frame metadata."""
        uploaded_frames = []
        failed_uploads = []

        # S3 path pattern: users/{user_id}/vid/{video_folder}/
        s3_base_path = f"users/{user_id}/vid/{video_folder}"

        for frame_path in frame_paths:
            frame_name = frame_path.name  # e.g., "1_12.34.png"
            s3_key = f"{s3_base_path}/{frame_name}"

            # Parse frame number and timestamp from filename
            frame_info = self._parse_frame_filename(frame_name)
            if not frame_info:
                logger.warning(f"Could not parse frame filename: {frame_name}")
                continue

            # Retry upload with exponential backoff
            upload_success = False
            for attempt in range(self.max_retry_attempts):
                try:
                    with open(frame_path, "rb") as f:
                        frame_bytes = f.read()

                    upload_to_s3_service.upload_file_to_s3(
                        file_bytes=frame_bytes,
                        object_name=s3_key,
                        bucket_name=self.frames_upload_bucket,
                    )

                    # Store frame metadata
                    frame_url = f"https://{self.frames_upload_bucket}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
                    uploaded_frames.append(
                        {
                            "frame_number": frame_info["frame_number"],
                            "frame_second": frame_info["frame_second"],
                            "s3_path": s3_key,
                            "s3_url": frame_url,
                            "local_path": str(frame_path),
                        }
                    )

                    upload_success = True
                    break

                except Exception as e:
                    logger.warning(f"Upload attempt {attempt + 1} failed for {frame_name}: {e}")
                    if attempt == self.max_retry_attempts - 1:
                        failed_uploads.append(
                            {
                                "frame_name": frame_name,
                                "error": str(e),
                                "frame_info": frame_info,
                                "local_path": str(frame_path),
                            }
                        )

        if failed_uploads:
            logger.error(
                f"Failed to upload {len(failed_uploads)} frames after {self.max_retry_attempts} attempts"
            )
            # Log failed uploads but continue with available frames
            for failed in failed_uploads:
                logger.error(f"Failed frame upload: {failed}")

        logger.info(f"Successfully uploaded {len(uploaded_frames)} frames to S3")
        return uploaded_frames

    def _parse_frame_filename(self, filename: str) -> Dict[str, Any] | None:
        """Parse frame filename to extract frame number and timestamp."""
        # Expected format: "1_12.34.png" -> frame_number=1, frame_second=12.34
        import re

        pattern = r"^(\d+)_(\d+\.\d+)\.png$"
        match = re.match(pattern, filename)

        if match:
            return {"frame_number": int(match.group(1)), "frame_second": float(match.group(2))}
        return None

    def _generate_embeddings(self, frames_dir: Path) -> List[List[float]]:
        """Generate embeddings from extracted frames."""
        try:
            logger.info(f"Generating embeddings for frames in {frames_dir}")

            # Use core pipeline embedding generation
            embeddings = encode_directory(
                frames_dir=frames_dir, batch_size=getattr(settings, "batch_size", 8), normalize=True
            )

            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            raise VideoProcessingError(f"Embedding generation failed: {e}")

    def _store_embeddings_in_qdrant(
        self,
        embeddings: List[List[float]],
        frame_info: List[Dict[str, Any]],
        user_id: str,
        video_id: str,
        video_folder: str,
    ) -> int:
        """Store embeddings in Qdrant user_videos collection."""
        try:
            import uuid

            from qdrant_client import models

            client = qdrant_service._client()
            points = []

            # Create timestamp for all entries
            created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

            for i, (embedding, frame_data) in enumerate(zip(embeddings, frame_info)):
                point_id = str(uuid.uuid4())

                payload = {
                    "id": point_id,
                    "user_id": user_id,
                    "video_id": video_id,
                    "created_at": created_at,
                    "path": frame_data["s3_path"],
                    "frame_number": frame_data["frame_number"],
                    "frame_second": frame_data["frame_second"],
                    "s3_url": frame_data["s3_url"],
                }

                point = models.PointStruct(id=point_id, vector=embedding, payload=payload)
                points.append(point)

            # Batch insert into Qdrant
            client.upsert(collection_name="user_videos", points=points)

            logger.info(f"Stored {len(points)} embeddings in Qdrant user_videos collection")
            return len(points)

        except Exception as e:
            raise VideoProcessingError(f"Failed to store embeddings in Qdrant: {e}")


# Singleton instance
video_processing_service = VideoProcessingService()


def process_user_video(
    video_s3_path: str, user_id: str, video_folder: str, video_id: str
) -> Dict[str, Any]:
    """
    Public API for processing user videos.

    Args:
        video_s3_path: S3 path to the uploaded video
        user_id: UUID of the user
        video_folder: UUID folder name for organizing video files
        video_id: Unique identifier for this video

    Returns:
        Dict with processing results
    """
    return video_processing_service.process_video(
        video_path=video_s3_path, user_id=user_id, video_folder=video_folder, video_id=video_id
    )
