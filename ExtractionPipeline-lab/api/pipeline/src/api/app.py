from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4, UUID
from datetime import datetime

# Load environment variables before importing settings
load_dotenv(".env", override=True)

from auth.apikey import verify_api_key
from auth.basic import verify_credentials
from config.env_config import settings
from config.logging_config import configure_logging
from src.api.controllers.jobs import router as jobs_router
from src.core.models.job import create_job, get_job
from src.core.background.tasks import run_job
from src.core.models.concurrency_manager import (
  initialize_concurrency_manager,
  shutdown_concurrency_manager,
  get_concurrency_manager
)
from src.core.models.model_preloader import preload_models, get_preloader

# Configure logging using consistent format
log = configure_logging()

# --- Pydantic Models for /process endpoint ---

class VideoItem(BaseModel):
    """Model for individual video processing items."""
    platform: str = Field(..., description="Platform name (e.g., 'instagram', 'youtube')")
    code: str = Field(..., description="Video code/ID")

class VideoItemWithStatus(BaseModel):
    """Model for individual video processing items with status."""
    platform: str = Field(..., description="Platform name (e.g., 'instagram', 'youtube')")
    code: str = Field(..., description="Video code/ID")
    status: str = Field(..., description="Item processing status: 'waiting', 'processing', 'success', 'failed'")

class ProcessRequest(BaseModel):
    """Model for POST /process request body."""
    items: List[VideoItem] = Field(..., description="List of video items to process")

class ProcessResponse(BaseModel):
    """Model for POST /process response."""
    jobId: str = Field(..., description="Unique job identifier")

class LogEntryResponse(BaseModel):
    """Model for log entry response."""
    ts: datetime = Field(..., description="Timestamp when log entry was created")
    level: str = Field(..., description="Log level (e.g., 'INFO', 'ERROR', 'DEBUG')")
    msg: str = Field(..., description="Log message content")

class JobStatusResponse(BaseModel):
    """Model for GET /status/{jobId} response."""
    status: str = Field(..., description="Current job status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    createdAt: str = Field(..., description="Job creation timestamp")
    updatedAt: str = Field(..., description="Job last update timestamp")
    items: List[VideoItemWithStatus] = Field(..., description="List of video items being processed with status")
    logs: List[LogEntryResponse] = Field(..., description="List of structured log entries from job execution")

app = FastAPI(
    title=settings.api_name,
    description="API for processing video extraction pipeline tasks including video cropping, scene frames extraction and deduplication, S3 storage, and frame embeddings extraction to remote Qdrant watched_frames collection.",
    version="1.0.0",
    docs_url=None,
    openapi_url=None,
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Startup/Shutdown Events ---
@app.on_event("startup")
async def startup_event():
    """Initialize the concurrency manager and preload models when the app starts."""
    await initialize_concurrency_manager()
    await preload_models()
    log.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up the concurrency manager when the app shuts down."""
    await shutdown_concurrency_manager()
    log.info("Application shutdown complete")

# --- POST /process endpoint ---

@app.post("/process", response_model=ProcessResponse, status_code=202, tags=["Processing"])
async def process_videos(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> ProcessResponse:
    """
    Process a batch of videos through the extraction pipeline.
    
    This endpoint accepts a JSON array of video items with platform and code,
    validates the request length against configured limits, creates a job with
    PENDING status, and kicks off background processing.
    
    Args:
        request: ProcessRequest containing list of video items
        background_tasks: FastAPI background tasks for async processing
        api_key: API key for authentication
        
    Returns:
        ProcessResponse with job ID and 202 Accepted status
        
    Raises:
        HTTPException: If request validation fails or exceeds limits
    """
    # Validate request length against settings
    if len(request.items) > settings.max_videos_per_request:
        raise HTTPException(
            status_code=400,
            detail=f"Request exceeds maximum allowed videos per request: {settings.max_videos_per_request}"
        )
    
    if len(request.items) == 0:
        raise HTTPException(
            status_code=400,
            detail="Request must contain at least one video item"
        )
    
    # Convert Pydantic models to dictionaries for job storage and add status
    job_items = []
    for item in request.items:
        item_dict = item.dict()
        item_dict['status'] = 'waiting'  # Initial status for all items
        job_items.append(item_dict)
    
    # Create job with PENDING status
    job = await create_job(job_items)
    
    # Kick off background task
    background_tasks.add_task(run_job, job.id)
    
    log.info(f"Created processing job {job.id} with {len(job_items)} items")
    
    # Return job ID with 202 Accepted
    return ProcessResponse(jobId=str(job.id))

# --- GET /status/{jobId} endpoint ---

@app.get("/status/{jobId}", response_model=JobStatusResponse, tags=["Processing"])
async def get_job_status(
    jobId: str,
    tail: Optional[int] = Query(None, description="Number of log lines to return (default: all)"),
    api_key: str = Depends(verify_api_key)
) -> JobStatusResponse:
    """
    Get job status and metadata.
    
    Returns full job metadata including status, progress, creation/update timestamps,
    items, and structured logs. Optionally supports limiting logs to last N entries.
    
    Args:
        jobId: Unique job identifier
        tail: Optional number of log entries to return (default: all)
        api_key: API key for authentication
        
    Returns:
        JobStatusResponse with job metadata and structured logs
        
    Raises:
        HTTPException: 404 if job_id is unknown
    """
    try:
        # Parse job ID as UUID
        job_uuid = UUID(jobId)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Fetch job from storage
    job = await get_job(job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Process log entries based on tail parameter
    # Return structured logs as LogEntryResponse objects
    log_entries = job.logs

    if tail is not None and tail > 0 and len(log_entries) > tail:
        log_entries = log_entries[-tail:]
        
    # Convert job items back to VideoItemWithStatus objects
    video_items = [VideoItemWithStatus(
        platform=item["platform"], 
        code=item["code"],
        status=item.get("status", "waiting")  # Default to waiting if status not present
    ) for item in job.items]
    
    log.info(f"Retrieved status for job {jobId}: {job.status.value}")
    
    return JobStatusResponse(
        status=job.status.value,
        progress=job.progress,
        createdAt=job.created_at.isoformat(),
        updatedAt=job.updated_at.isoformat(),
        items=video_items,
        logs=[LogEntryResponse(ts=log_entry.ts, level=log_entry.level, msg=log_entry.msg) for log_entry in log_entries]
    )

# --- Include Routers from Controllers ---

# Jobs Management Routes
app.include_router(
    jobs_router,
    prefix="/jobs",
    tags=["Extraction Jobs"],
    dependencies=[Depends(verify_api_key)],
)

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
def read_root():
    return {
        "status": "ok", 
        "message": f"Welcome to the {settings.api_name}",
        "version": "1.0.0",
        "api_name": settings.api_name
    }

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

# Debug endpoint for testing
@app.get("/debug/settings", tags=["Debug"])
def debug_settings():
    return {
        "api_username": settings.api_username,
        "api_password": "***" if settings.api_password else None,
        "api_key": "***" if settings.api_key else None,
        "api_name": settings.api_name,
        "output_root": str(settings.output_root),
        "max_workers": settings.max_workers,
        "batch_size": settings.batch_size,
        "sample_fps": settings.sample_fps,
        "crop_enabled": settings.crop_enabled,
        "dedup_enabled": settings.dedup_enabled,
        "collection": settings.collection,
        "dim": settings.dim,
        "clip_model": settings.clip_model,
        "max_videos_per_request": settings.max_videos_per_request,
        "pipeline_max_parallel_jobs": settings.pipeline_max_parallel_jobs
    }

# Configuration endpoint
@app.get("/config", tags=["Configuration"])
def get_config():
    """Get current configuration (non-sensitive values only)."""
    return {
        "api_name": settings.api_name,
        "api_port": settings.api_port,
        "output_root": str(settings.output_root),
        "max_workers": settings.max_workers,
        "batch_size": settings.batch_size,
        "sample_fps": settings.sample_fps,
        "crop_enabled": settings.crop_enabled,
        "dedup_enabled": settings.dedup_enabled,
        "collection": settings.collection,
        "dim": settings.dim,
        "clip_model": settings.clip_model,
        "max_videos_per_request": settings.max_videos_per_request,
        "pipeline_max_parallel_jobs": settings.pipeline_max_parallel_jobs
    }

# Concurrency stats endpoint
@app.get("/concurrency/stats", tags=["Monitoring"])
def get_concurrency_stats():
    """Get concurrency manager statistics."""
    manager = get_concurrency_manager()
    return manager.get_stats()

# Model status endpoint
@app.get("/models/status", tags=["Monitoring"])
def get_model_status():
    """Get model preloading status."""
    preloader = get_preloader()
    return {
        "clip_model_loaded": preloader.is_model_loaded(),
        "clip_model_name": settings.clip_model
    }

# Custom Swagger UI Route
@app.get("/api/docs", dependencies=[Depends(verify_credentials)])
def custom_swagger_ui():
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title=settings.api_name + " Pipeline Docs")

@app.get("/api/openapi.json", dependencies=[Depends(verify_credentials)])
def custom_openapi():
    return JSONResponse(app.openapi())
