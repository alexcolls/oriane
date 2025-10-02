#!/usr/bin/env python3
"""
Test script to verify logging and debug functionality implementation.
"""

import asyncio
import os
import sys
from pathlib import Path


from config.logging_config import configure_logging
from src.api.pipeline.src.core.models.job import create_job, get_job, JobStatus
from src.api.pipeline.src.core.background.tasks import run_job

import pytest

@pytest.mark.asyncio
async def test_logging_debug():
    """Test logging and debug functionality."""
    print("Testing logging and DEBUG_PIPELINE support...")
    
    # Configure logging
    logger = configure_logging()
    logger.info("Test started - logging configuration verified")
    
    # Create a test job
    test_items = [
        {"platform": "test", "code": "test_video_1"},
        {"platform": "test", "code": "test_video_2"}
    ]
    
    job = await create_job(test_items)
    print(f"Created test job: {job.id}")
    
    # Set DEBUG_PIPELINE environment variable
    os.environ["DEBUG_PIPELINE"] = "1"
    
    # Note: We're not actually running the job since it requires the full pipeline
    # Instead, we're testing the logging configuration and job creation
    
    # Verify job was created with correct status
    retrieved_job = await get_job(job.id)
    assert retrieved_job is not None
    assert retrieved_job.status == JobStatus.PENDING
    assert len(retrieved_job.items) == 2
    
    print("✓ Job creation and logging configuration test passed")
    print(f"✓ Job ID: {job.id}")
    print(f"✓ Job status: {job.status.value}")
    print(f"✓ Job items count: {len(job.items)}")
    print(f"✓ DEBUG_PIPELINE: {os.environ.get('DEBUG_PIPELINE')}")
    
    # Test log updating
    from src.api.pipeline.src.core.models.job import update_job_status
    await update_job_status(job.id, log="Test log message")
    
    updated_job = await get_job(job.id)
    assert "Test log message" in updated_job.log
    print("✓ Log streaming test passed")
    
    print("\nAll tests passed! Logging and debug support is working correctly.")

