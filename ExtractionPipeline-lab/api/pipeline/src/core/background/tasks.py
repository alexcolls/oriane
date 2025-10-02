"""
Background Tasks Module

This module provides background task processing functionality for the extraction pipeline.
Includes the main job processing function that runs video extraction jobs asynchronously.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
from uuid import UUID

from src.core.models.job import update_job_status, JobStatus, get_job
from src.core.models.concurrency_manager import get_concurrency_manager
from config.logging_config import configure_logging


# Configure logging using consistent format
logger = configure_logging()
uvicorn_logger = logging.getLogger("uvicorn")

# Define the absolute path to the entrypoint
ENTRYPOINT_PATH = Path(os.getenv("PIPELINE_ENTRYPOINT", Path(__file__).resolve().parents[5] / "core" / "py" / "pipeline" / "entrypoint.py"))

# Fail fast if the entrypoint does not exist
assert ENTRYPOINT_PATH.exists(), f"Pipeline entrypoint not found at {ENTRYPOINT_PATH}"


async def _execute_pipeline_async(job_id: UUID, job_items: List[Dict[str, Any]], env: Dict[str, str]) -> Tuple[int, str, str]:
    """
    Asynchronous pipeline execution function that streams output line-by-line.
    Updates Job.log in real-time and forwards to UVicorn logger when DEBUG_PIPELINE is true.
    Parses JSON status beacons and tracks progress.
    
    Args:
        job_id: UUID of the job being processed
        job_items: List of job items to process
        env: Environment variables for the pipeline
    
    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    try:
        logger.info(f"Executing pipeline with {len(job_items)} items using entrypoint: {ENTRYPOINT_PATH}")
        
        # Check if DEBUG_PIPELINE is enabled for UVicorn logging
        debug_pipeline = env.get("DEBUG_PIPELINE", "0") == "1"
        
        # Initialize progress tracking
        total_items = len(job_items)
        processed_items = 0
        checkmark_count = 0

        # Run the pipeline subprocess
        process = await asyncio.create_subprocess_exec(
            "python3", "-u", str(ENTRYPOINT_PATH),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout_lines, stderr_lines = [], []
        
        # Read stdout line by line
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line_str = line.decode().rstrip()
            if line_str:
                stdout_lines.append(line_str)
                
                # Stream to Job.log
                await update_job_status(job_id, level="info", msg=line_str)
                
                # Forward to logger
                logger.info(line_str)
                
                # Forward to UVicorn logger when DEBUG_PIPELINE is true
                if debug_pipeline:
                    uvicorn_logger.info(f"[Job {job_id}] {line_str}")
                
                # Parse JSON status beacons or count checkmarks for progress
                progress_updated = False
                
                # Try to parse JSON status beacon
                try:
                    # Look for JSON-like patterns in the line
                    if '{' in line_str and '}' in line_str:
                        # Extract potential JSON from the line
                        json_match = re.search(r'\{[^}]+\}', line_str)
                        if json_match:
                            json_str = json_match.group(0)
                            status_data = json.loads(json_str)
                            
                            # Check for item_done beacon
                            if 'item_done' in status_data:
                                new_processed = int(status_data['item_done'])
                                if new_processed > processed_items:
                                    delta = new_processed - processed_items
                                    processed_items = new_processed
                                    
                                    # Calculate progress percentage
                                    progress_delta = int(100 * delta / total_items) if total_items > 0 else 0
                                    progress_delta = min(progress_delta, 100 - (int(100 * (processed_items - delta) / total_items) if total_items > 0 else 0))
                                    
                                    if progress_delta > 0:
                                        await update_job_status(job_id, append_progress=progress_delta)
                                        logger.info(f"Progress updated: {processed_items}/{total_items} items processed")
                                        progress_updated = True
                                        
                except (json.JSONDecodeError, ValueError, KeyError):
                    # If JSON parsing fails, fall back to checkmark counting
                    pass
                
                # Fallback: count checkmarks if no JSON beacon was processed
                if not progress_updated and '✔' in line_str:
                    checkmark_count += line_str.count('✔')
                    if checkmark_count > processed_items:
                        delta = checkmark_count - processed_items
                        processed_items = checkmark_count
                        
                        # Calculate progress percentage
                        progress_delta = int(100 * delta / total_items) if total_items > 0 else 0
                        progress_delta = min(progress_delta, 100 - (int(100 * (processed_items - delta) / total_items) if total_items > 0 else 0))
                        
                        if progress_delta > 0:
                            await update_job_status(job_id, append_progress=progress_delta)
                            logger.info(f"Progress updated via checkmarks: {processed_items}/{total_items} items processed")

        # Read stderr
        stderr_data = await process.stderr.read()
        stderr_str = stderr_data.decode()
        
        if stderr_str:
            stderr_lines.append(stderr_str)
            
            # Stream stderr to Job.log
            await update_job_status(job_id, level="ERROR", msg=f"STDERR: {stderr_str}")
            
            # Forward to logger
            logger.error(stderr_str)
            
            # Forward to UVicorn logger when DEBUG_PIPELINE is true
            if debug_pipeline:
                uvicorn_logger.error(f"[Job {job_id}] STDERR: {stderr_str}")

        # Wait for process to complete
        await process.wait()

        return process.returncode, '\n'.join(stdout_lines), '\n'.join(stderr_lines)

    except Exception as e:
        error_msg = f"Pipeline execution encountered unexpected error: {str(e)}"
        logger.error(error_msg)
        
        # Update Job.log with error
        await update_job_status(job_id, level="ERROR", msg=error_msg)
        
        return -1, "", str(e)


def _execute_pipeline_with_status_updates(job_id: UUID, job_items: List[Dict[str, Any]], env: Dict[str, str]) -> Tuple[int, str, str]:
    """
    Wrapper function that executes the pipeline and handles job status transitions.
    This function is designed to be run in the ThreadPoolExecutor.
    
    Args:
        job_id: UUID of the job being processed
        job_items: List of job items to process
        env: Environment variables for the pipeline
        
    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    logger.info(f"Worker processing job {job_id} with {len(job_items)} items")
    
    try:
        # Execute the pipeline asynchronously with streaming output
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_execute_pipeline_async(job_id, job_items, env))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Pipeline execution failed for job {job_id}: {e}")
        return -1, "", str(e)


async def run_job(job_id: UUID) -> None:
    """
    Background task to execute a video processing job.
    
    This function processes a job by:
    1. Retrieving the job from storage
    2. Updating status to PENDING (queued)
    3. Submitting job to concurrency manager
    4. Updating status to RUNNING when processing starts
    5. Serializing Job.items to JSON and setting JOB_INPUT environment variable
    6. Setting DEBUG_PIPELINE="1" environment variable
    7. Calling subprocess.run(["python3", "-u", str(ENTRYPOINT_PATH)], ...) capturing stdout/stderr
    8. Parsing exit code: 0 → COMPLETED, else FAILED
    9. Persisting logs to Job.log and updating progress to 100 or leaving partial
    10. Using bounded ThreadPoolExecutor with GPU semaphore protection
    
    Args:
        job_id: UUID of the job to process
    """
    logger.info(f"Starting background job processing for job_id: {job_id}")
    
    try:
        # Get job from storage
        job = await get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found in storage")
            return
        
        # Update job status to pending (queued)
        await update_job_status(job_id, status=JobStatus.PENDING, level="INFO", msg=f"Job queued for processing with {len(job.items)} items")
        
        # Prepare environment variables for the pipeline
        env = os.environ.copy()
        env["JOB_INPUT"] = json.dumps(job.items)  # Serialize Job.items to JSON
        env["DEBUG_PIPELINE"] = "1"  # Set debug flag
        
        # Ensure AWS credentials are explicitly set in the subprocess environment
        # This fixes the boto3 ProfileNotFound error
        from config.env_config import settings
        if settings.AWS_ACCESS_KEY_ID:
            env["AWS_ACCESS_KEY_ID"] = settings.AWS_ACCESS_KEY_ID
        if settings.AWS_SECRET_ACCESS_KEY:
            env["AWS_SECRET_ACCESS_KEY"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.aws_region:
            env["AWS_REGION"] = settings.aws_region
        
        # Submit the job to the concurrency manager
        concurrency_manager = get_concurrency_manager()
        
        # Update status to running when job starts processing
        await update_job_status(job_id, status=JobStatus.RUNNING, level="INFO", msg=f"Started processing {len(job.items)} items")
        
        exit_code, stdout, stderr = await concurrency_manager.submit_job(
            _execute_pipeline_with_status_updates, job_id, job.items, env
        )
        
        # Parse exit code and update job status accordingly
        if exit_code == 0:
            log_message = f"Processing completed successfully. Processed {len(job.items)} items.\n\nStdout:\n{stdout}"
            status = JobStatus.COMPLETED
            # Get current job progress and set to 100
            current_job = await get_job(job_id)
            current_progress = current_job.progress if current_job else 0
            await update_job_status(job_id, status=status, level="INFO", msg=log_message, append_progress=100-current_progress)
        else:
            log_message = f"Pipeline execution failed with exit code {exit_code}.\n\nStderr:\n{stderr}\n\nStdout:\n{stdout}"
            status = JobStatus.FAILED
            # Update with structured logging, leave progress as is
            await update_job_status(job_id, status=status, level="ERROR", msg=log_message)
        
        logger.info(f"Pipeline job {job_id} completed with status: {status.value}")
        
    except Exception as e:
        logger.error(f"Pipeline job {job_id} encountered unexpected error: {str(e)}")
        error_message = f"Unexpected error during job processing: {str(e)}"
        await update_job_status(job_id, status=JobStatus.FAILED, level="ERROR", msg=error_message)
