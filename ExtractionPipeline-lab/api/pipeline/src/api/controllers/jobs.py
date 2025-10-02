"""
Jobs Controller

This module provides the FastAPI router for job management endpoints
in the extraction pipeline API. It integrates with the core pipeline
entrypoint to execute video processing tasks.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config.env_config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# In-memory job storage (in production, use Redis/Database)
JOBS_STORE: Dict[str, Dict[str, Any]] = {}

# Pydantic models for request/response validation
class JobItem(BaseModel):
    platform: str = Field(..., description="Platform name (e.g., 'instagram', 'youtube')")
    code: str = Field(..., description="Video code/ID")

class JobCreateRequest(BaseModel):
    items: List[JobItem] = Field(..., description="List of videos to process")
    batch_size: Optional[int] = Field(None, description="Batch size for processing (default: from config)")
    sleep_between_batches: Optional[float] = Field(None, description="Sleep duration between batches")
    local_mode: Optional[bool] = Field(False, description="Run in local mode (skip DB writes)")
    skip_upload: Optional[bool] = Field(False, description="Skip S3 frame upload")

class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    updated_at: str
    items: List[JobItem]
    progress: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int


async def run_pipeline_job(job_id: str, request: JobCreateRequest):
    """
    Background task to execute the video processing pipeline.
    
    Args:
        job_id: Unique job identifier
        request: JobCreateRequest with processing parameters
    """
    logger.info(f"Running pipeline job {job_id}")
    job_info = JOBS_STORE[job_id]

    # Update job status
    job_info["status"] = "running"
    job_info["updated_at"] = datetime.utcnow().isoformat()
    
    try:
        # Prepare environment variables
        job_input = json.dumps([item.dict() for item in request.items])
        env = os.environ.copy()
        env["JOB_INPUT"] = job_input
        
        # Set pipeline configuration
        if request.batch_size:
            env["VP_BATCH_SIZE"] = str(request.batch_size)
        if request.sleep_between_batches:
            env["VP_SLEEP_BETWEEN_BATCHES"] = str(request.sleep_between_batches)
        env["LOCAL_MODE"] = "1" if request.local_mode else "0"
        env["SKIP_UPLOAD"] = "1" if request.skip_upload else "0"
        
        # Execute the pipeline entrypoint
        entrypoint_path = Path("../../core/py/pipeline/entrypoint.py").resolve()
        
        logger.info(f"Executing pipeline with {len(request.items)} items")
        result = subprocess.run(
            ["python3", str(entrypoint_path)],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Update job status on success
        job_info["status"] = "completed"
        job_info["results"] = {
            "message": "Processing completed successfully",
            "stdout": result.stdout,
            "processed_items": len(request.items)
        }
        logger.info(f"Pipeline job {job_id} completed successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline job {job_id} failed: {e}")
        job_info["status"] = "failed"
        job_info["error"] = f"Pipeline execution failed: {e.stderr}"
        job_info["results"] = {
            "stdout": e.stdout,
            "stderr": e.stderr,
            "return_code": e.returncode
        }
    except Exception as e:
        logger.error(f"Pipeline job {job_id} encountered unexpected error: {str(e)}")
        job_info["status"] = "failed"
        job_info["error"] = str(e)
    finally:
        job_info["updated_at"] = datetime.utcnow().isoformat()


@router.get("/", response_model=JobListResponse)
async def list_jobs(page: int = 1, page_size: int = 10) -> JobListResponse:
    """
    List all jobs in the pipeline.
    
    Args:
        page: Page number for pagination
        page_size: Number of jobs per page
        
    Returns:
        JobListResponse containing job list and status information
    """
    # Paginate jobs from the store
    total = len(JOBS_STORE)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    jobs = list(JOBS_STORE.values())[start_idx:end_idx]
    
    return JobListResponse(
        jobs=[JobResponse(**job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=JobResponse)
async def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks
) -> JobResponse:
    """
    Create a new processing job in the pipeline.
    
    Args:
        request: JobCreateRequest containing job parameters
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        JobResponse containing job creation response
    """
    job_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    updated_at = created_at
    status = "pending"

    # Store initial job info
    job_info = {
        "job_id": job_id,
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
        "items": [item.dict() for item in request.items],
        "progress": {
            "completed": 0,
            "total": len(request.items)
        }
    }
    JOBS_STORE[job_id] = job_info

    # Launch background task to process job
    background_tasks.add_task(run_pipeline_job, job_id, request)

    logger.info(f"Created new job with ID: {job_id}")

    return JobResponse(
        job_id=job_id,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        items=request.items
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """
    Get details of a specific job.
    
    Args:
        job_id: Unique identifier for the job
        
    Returns:
        JobResponse containing job details
    """
    job_info = JOBS_STORE.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Convert items back to JobItem objects if they're dicts
    items = job_info["items"]
    if items and isinstance(items[0], dict):
        items = [JobItem(**item) for item in items]
    
    return JobResponse(
        job_id=job_info["job_id"],
        status=job_info["status"],
        created_at=job_info["created_at"],
        updated_at=job_info["updated_at"],
        items=items,
        progress=job_info.get("progress"),
        results=job_info.get("results"),
        error=job_info.get("error")
    )


@router.delete("/{job_id}", response_model=Dict[str, Any])
async def delete_job(job_id: str) -> Dict[str, Any]:
    """
    Delete a specific job.
    
    Args:
        job_id: Unique identifier for the job
        
    Returns:
        Dict containing job deletion response
    """
    if job_id in JOBS_STORE:
        del JOBS_STORE[job_id]
        return {"status": "success", "message": "Job deleted successfully", "job_id": job_id}
    else:
        raise HTTPException(status_code=404, detail="Job not found")


@router.post("/{job_id}/start", response_model=Dict[str, Any])
async def start_job(job_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Start execution of a specific job.
    
    Args:
        job_id: Unique identifier for the job
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        Dict containing job start response
    """
    job_info = JOBS_STORE.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_info["status"] == "running":
        raise HTTPException(status_code=400, detail="Job is already running")
    
    if job_info["status"] == "completed":
        raise HTTPException(status_code=400, detail="Job has already completed")
    
    # Create a new request object from stored items
    items = [JobItem(**item) for item in job_info["items"]]
    request = JobCreateRequest(items=items)
    
    # Reset job status and start processing
    job_info["status"] = "pending"
    job_info["updated_at"] = datetime.utcnow().isoformat()
    job_info["error"] = None
    
    background_tasks.add_task(run_pipeline_job, job_id, request)
    
    return {
        "status": "success",
        "message": "Job started successfully",
        "job_id": job_id,
        "job_status": "running"
    }


@router.post("/{job_id}/stop", response_model=Dict[str, Any])
async def stop_job(job_id: str) -> Dict[str, Any]:
    """
    Stop execution of a specific job.
    
    Args:
        job_id: Unique identifier for the job
        
    Returns:
        Dict containing job stop response
    """
    job_info = JOBS_STORE.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_info["status"] != "running":
        raise HTTPException(status_code=400, detail="Job is not running")
    
    # Mark job as stopped
    job_info["status"] = "stopped"
    job_info["updated_at"] = datetime.utcnow().isoformat()
    
    return {
        "status": "success",
        "message": "Job stopped successfully",
        "job_id": job_id,
        "job_status": "stopped"
    }


@router.get("/{job_id}/logs", response_model=Dict[str, Any])
async def get_job_logs(job_id: str) -> Dict[str, Any]:
    """
    Get logs for a specific job.
    
    Args:
        job_id: Unique identifier for the job
        
    Returns:
        Dict containing job logs
    """
    job_info = JOBS_STORE.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # In a real implementation, this would read from log files
    # For now, return basic information
    return {
        "status": "success",
        "job_id": job_id,
        "logs": job_info.get("results", {}).get("stdout", "No logs available"),
        "error_logs": job_info.get("results", {}).get("stderr", "No error logs")
    }


@router.get("/{job_id}/progress", response_model=Dict[str, Any])
async def get_job_progress(job_id: str) -> Dict[str, Any]:
    """
    Get progress information for a specific job.
    
    Args:
        job_id: Unique identifier for the job
        
    Returns:
        Dict containing job progress information
    """
    job_info = JOBS_STORE.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    progress = job_info.get("progress", {"completed": 0, "total": 0})
    percentage = (progress["completed"] / progress["total"]) * 100 if progress["total"] > 0 else 0
    
    return {
        "status": "success",
        "job_id": job_id,
        "progress": progress,
        "percentage": round(percentage, 2),
        "job_status": job_info["status"]
    }
