from __future__ import annotations

"""Upload to S3 service

Provides thin convenience wrappers around the central S3 utilities
that live under `core/py/pipeline/src` so that the API layer
can stay agnostic of the underlying module layout.
"""

import logging

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

try:
    from ..config.env_config import settings
except ImportError:
    from config.env_config import settings

logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.aws_region,
)


def upload_file_to_s3(file_bytes: bytes, object_name: str, bucket_name: str = None) -> bool:
    """
    Upload a file to an S3 bucket

    :param file_bytes: Bytes content of the file to upload
    :param object_name: S3 object name (key) where the file will be stored
    :param bucket_name: Bucket to upload to. If not specified, uses settings.s3_bucket_name
    :return: True if file was uploaded, else False
    """

    # Use default bucket if none specified
    if bucket_name is None:
        bucket_name = getattr(settings, "s3_bucket_name", None)
        if not bucket_name:
            raise HTTPException(status_code=500, detail="S3 bucket name not configured")

    try:
        # Upload the file
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=file_bytes)
        logger.info(f"File uploaded successfully to s3://{bucket_name}/{object_name}")
        return True

    except ClientError as e:
        logger.error(f"Failed to upload file to S3: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during S3 upload: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during upload: {str(e)}")


def upload_file_with_metadata(
    file_bytes: bytes, object_name: str, metadata: dict = None, bucket_name: str = None
) -> bool:
    """
    Upload a file to S3 with custom metadata

    :param file_bytes: Bytes content of the file to upload
    :param object_name: S3 object name (key) where the file will be stored
    :param metadata: Dictionary of metadata to attach to the object
    :param bucket_name: Bucket to upload to. If not specified, uses settings.s3_bucket_name
    :return: True if file was uploaded, else False
    """

    # Use default bucket if none specified
    if bucket_name is None:
        bucket_name = getattr(settings, "s3_bucket_name", None)
        if not bucket_name:
            raise HTTPException(status_code=500, detail="S3 bucket name not configured")

    try:
        # Prepare upload parameters
        upload_params = {"Bucket": bucket_name, "Key": object_name, "Body": file_bytes}

        # Add metadata if provided
        if metadata:
            upload_params["Metadata"] = metadata

        # Upload the file
        s3_client.put_object(**upload_params)
        logger.info(f"File with metadata uploaded successfully to s3://{bucket_name}/{object_name}")
        return True

    except ClientError as e:
        logger.error(f"Failed to upload file with metadata to S3: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during S3 upload with metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during upload: {str(e)}")


def delete_file_from_s3(object_name: str, bucket_name: str = None) -> bool:
    """
    Delete a file from S3 bucket

    :param object_name: S3 object name (key) to delete
    :param bucket_name: Bucket to delete from. If not specified, uses settings.s3_bucket_name
    :return: True if file was deleted, else False
    """

    # Use default bucket if none specified
    if bucket_name is None:
        bucket_name = getattr(settings, "s3_bucket_name", None)
        if not bucket_name:
            raise HTTPException(status_code=500, detail="S3 bucket name not configured")

    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        logger.info(f"File deleted successfully from s3://{bucket_name}/{object_name}")
        return True

    except ClientError as e:
        logger.error(f"Failed to delete file from S3: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file from S3: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during S3 deletion: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during deletion: {str(e)}")


def check_file_exists(object_name: str, bucket_name: str = None) -> bool:
    """
    Check if a file exists in S3 bucket

    :param object_name: S3 object name (key) to check
    :param bucket_name: Bucket to check in. If not specified, uses settings.s3_bucket_name
    :return: True if file exists, else False
    """

    # Use default bucket if none specified
    if bucket_name is None:
        bucket_name = getattr(settings, "s3_bucket_name", None)
        if not bucket_name:
            raise HTTPException(status_code=500, detail="S3 bucket name not configured")

    try:
        s3_client.head_object(Bucket=bucket_name, Key=object_name)
        return True
    except ClientError as e:
        # If the object doesn't exist, head_object raises a ClientError
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            # For other errors, re-raise the exception
            logger.error(f"Error checking if file exists in S3: {e}")
            raise HTTPException(status_code=500, detail=f"Error checking file existence: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error checking file existence: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
