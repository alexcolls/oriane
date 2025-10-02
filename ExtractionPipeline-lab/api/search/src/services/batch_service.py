from __future__ import annotations

"""Batch service

Provides thin convenience wrappers around the central CLIP embedding
utilities that live under `core/py/pipeline/src` so that the API layer
can stay agnostic of the underlying module layout.
"""

import boto3
from config.env_config import settings
from fastapi import HTTPException

batch_client = boto3.client(
    "batch",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.aws_region,
)


def trigger_video_pipeline_job(video_code: str, platform: str = "s3_upload"):
    """
    Submits a job to AWS Batch to process a video.

    :param video_code: The unique identifier for the video (e.g., the filename in S3).
    :param platform: The platform identifier.
    """
    try:
        # The command here is what your Docker container in AWS Batch will run.
        # It uses your core pipeline's CLI capabilities.
        command = [
            "python",
            "-m",
            "pipeline_runner",  # A new runner script
            "process_single",
            "--platform",
            platform,
            "--code",
            video_code,
        ]

        response = batch_client.submit_job(
            jobName=f"video-processing-{platform}-{video_code.replace('.', '-')}",
            jobQueue=settings.BATCH_JOB_QUEUE,
            jobDefinition=settings.BATCH_JOB_DEFINITION,
            containerOverrides={"command": command},
        )
        job_id = response["jobId"]
        print(f"Submitted Batch job {job_id} for video {video_code}")
        return job_id
    except Exception as e:
        print(f"Error submitting Batch job: {e}")
        raise HTTPException(status_code=500, detail="Failed to start video processing job.")
