from __future__ import annotations

"""Image controller

Provides thin convenience wrappers around the central CLIP embedding
utilities that live under `core/py/pipeline/src` so that the API layer
can stay agnostic of the underlying module layout.
"""

import datetime
import io
import logging
import uuid
from typing import List

from fastapi import APIRouter, File, HTTPException, Path, UploadFile
from PIL import Image
from pydantic import BaseModel

# Import services
try:
    from services import (  # when 'services' is on PYTHONPATH
        embeddings_service,
        qdrant_service,
        upload_to_s3_service,
    )
except ImportError:  # pragma: no cover – fallback for package-relative layout
    from ....services import embeddings_service, qdrant_service, upload_to_s3_service

try:
    from config.env_config import settings
except ImportError:
    from ...config.env_config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ImageUploadResponse(BaseModel):
    message: str
    image_id: str
    image_url: str
    status: str


class BatchImageUploadResponse(BaseModel):
    message: str
    successful_uploads: List[dict]  # Changed to dict to include image_id, image_url, filename
    failed_uploads: List[dict]
    total_processed: int


@router.post("/{user_id}", response_model=ImageUploadResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(..., description="The image file to upload."),
    user_id: str = Path(..., description="The UUID of the user uploading the image."),
):
    """
    Accepts an image, uploads it to S3, generates embeddings, and stores metadata in Qdrant user_images collection.
    Returns the image ID and S3 URL.
    """

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        # Read and validate image
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Empty image file.")

        # Convert bytes to PIL Image for validation and processing
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if image.mode != "RGB":
            image = image.convert("RGB")
            # Convert back to bytes in PNG format for consistent storage
            img_buffer = io.BytesIO()
            image.save(img_buffer, format="PNG")
            image_bytes = img_buffer.getvalue()

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(exc)}")

    # Generate unique image ID and timestamp
    image_id = str(uuid.uuid4())
    upload_timestamp = datetime.datetime.now(datetime.timezone.utc)

    # Create S3 object path: users/<user-uuid>/img/<image-uuid>.png
    # File key pattern: users/<user_id>/img/<uuid>.png (UUID consistency: filename=<image_id>.png, Qdrant id=image_id)
    s3_object_key = f"users/{user_id}/img/{image_id}.png"

    try:
        # 1️⃣ Upload image to S3
        logger.info(f"Uploading image to S3: {s3_object_key}")
        upload_to_s3_service.upload_file_to_s3(
            file_bytes=image_bytes, object_name=s3_object_key, bucket_name=settings.s3_app_bucket
        )

        # Generate S3 URL
        image_url = f"https://{settings.s3_app_bucket}.s3.{settings.aws_region}.amazonaws.com/{s3_object_key}"

        # 2️⃣ Generate embedding for the image
        logger.info(f"Generating embeddings for image {image_id}")
        vector = embeddings_service.get_image_embedding(image)

        # 3️⃣ Prepare payload with metadata for user_images collection
        payload = {
            "id": image_id,
            "user_id": user_id,
            "image_id": image_id,
            "created_at": upload_timestamp.isoformat(),
            "path": s3_object_key,
            "filename": file.filename or "uploaded_image.png",
            "content_type": "image/png",  # Standardized to PNG
            "size_bytes": len(image_bytes),
            "image_size": f"{image.width}x{image.height}",
            "s3_url": image_url,
        }

        # 4️⃣ Store in Qdrant user_images collection
        logger.info(f"Storing metadata in Qdrant user_images collection for image {image_id}")
        from qdrant_client import models

        client = qdrant_service._client()

        # Create point for insertion
        point = models.PointStruct(id=image_id, vector=vector, payload=payload)

        # Insert the point into user_images collection
        client.upsert(collection_name="user_images", points=[point])

        logger.info(f"Successfully processed image {image_id} for user {user_id}")

    except Exception as exc:
        logger.error(f"Failed to process image {image_id}: {str(exc)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process and store image: {str(exc)}"
        )

    return {
        "message": "Image uploaded and processed successfully.",
        "image_id": image_id,
        "image_url": image_url,
        "status": "stored",
    }


@router.post("/batch/{user_id}", response_model=BatchImageUploadResponse, status_code=201)
async def upload_images_batch(
    files: List[UploadFile] = File(..., description="Multiple image files to upload."),
    user_id: str = Path(..., description="The UUID of the user uploading the images."),
):
    """
    Accepts multiple images, uploads them to S3, generates embeddings, and stores metadata in Qdrant user_images collection.
    Returns a summary of successful and failed uploads.
    """

    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    if len(files) > 50:  # Reasonable limit for batch uploads
        raise HTTPException(status_code=400, detail="Too many files. Maximum 50 images per batch.")

    successful_uploads = []
    failed_uploads = []

    for file in files:
        try:
            # Validate file type
            if not file.content_type or not file.content_type.startswith("image/"):
                failed_uploads.append(
                    {"filename": file.filename, "error": "File must be an image."}
                )
                continue

            # Read and validate image
            image_bytes = await file.read()
            if not image_bytes:
                failed_uploads.append({"filename": file.filename, "error": "Empty image file."})
                continue

            # Convert bytes to PIL Image for processing
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
                # Convert back to bytes in PNG format for consistent storage
                img_buffer = io.BytesIO()
                image.save(img_buffer, format="PNG")
                image_bytes = img_buffer.getvalue()

            # Generate unique image ID and timestamp
            image_id = str(uuid.uuid4())
            upload_timestamp = datetime.datetime.now(datetime.timezone.utc)

            # Create S3 object path: users/<user-uuid>/img/<image-uuid>.png
            # File key pattern: users/<user_id>/img/<uuid>.png (UUID consistency: filename=<image_id>.png, Qdrant id=image_id)
            s3_object_key = f"users/{user_id}/img/{image_id}.png"

            # Upload image to S3
            upload_to_s3_service.upload_file_to_s3(
                file_bytes=image_bytes,
                object_name=s3_object_key,
                bucket_name=settings.s3_app_bucket,
            )

            # Generate S3 URL
            image_url = f"https://{settings.s3_app_bucket}.s3.{settings.aws_region}.amazonaws.com/{s3_object_key}"

            # Generate embedding
            vector = embeddings_service.get_image_embedding(image)

            # Prepare payload with metadata for user_images collection
            payload = {
                "id": image_id,
                "user_id": user_id,
                "image_id": image_id,
                "created_at": upload_timestamp.isoformat(),
                "path": s3_object_key,
                "filename": file.filename or "uploaded_image.png",
                "content_type": "image/png",  # Standardized to PNG
                "size_bytes": len(image_bytes),
                "image_size": f"{image.width}x{image.height}",
                "s3_url": image_url,
                "upload_type": "batch_image",
            }

            # Store in Qdrant user_images collection
            from qdrant_client import models

            client = qdrant_service._client()

            # Create point for insertion
            point = models.PointStruct(id=image_id, vector=vector, payload=payload)

            # Insert the point into user_images collection
            client.upsert(collection_name="user_images", points=[point])

            successful_uploads.append(
                {"image_id": image_id, "image_url": image_url, "filename": file.filename}
            )

        except Exception as exc:
            logger.error(f"Failed to process image {file.filename}: {str(exc)}")
            failed_uploads.append({"filename": file.filename, "error": str(exc)})

    return {
        "message": f"Batch upload completed. {len(successful_uploads)} successful, {len(failed_uploads)} failed.",
        "successful_uploads": successful_uploads,
        "failed_uploads": failed_uploads,
        "total_processed": len(files),
    }
