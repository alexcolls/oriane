"""
Unit tests for background tasks with real-time status and progress updates.

This test suite validates the status transitions and progress tracking functionality
in the background tasks module, including JSON beacon parsing and checkmark counting.
"""

import asyncio
import json
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from uuid import UUID, uuid4

from src.core.background.tasks import _execute_pipeline_async, run_job
from src.core.models.job import JobStatus, Job, create_job, get_job, update_job_status


class TestStatusTransitions:
    """Test job status transitions and progress tracking."""
    
    @pytest.fixture
    def mock_job_id(self):
        """Generate a mock job ID."""
        return uuid4()
    
    @pytest.fixture
    def mock_job_items(self):
        """Generate mock job items for testing."""
        return [
            {"id": 1, "video_url": "https://example.com/video1.mp4"},
            {"id": 2, "video_url": "https://example.com/video2.mp4"},
            {"id": 3, "video_url": "https://example.com/video3.mp4"}
        ]
    
    @pytest.fixture
    def mock_env(self):
        """Generate mock environment variables."""
        return {
            "DEBUG_PIPELINE": "1",
            "JOB_INPUT": json.dumps([
                {"id": 1, "video_url": "https://example.com/video1.mp4"},
                {"id": 2, "video_url": "https://example.com/video2.mp4"}, 
                {"id": 3, "video_url": "https://example.com/video3.mp4"}
            ])
        }
    
    def create_mock_entrypoint(self, output_lines):
        """Create a mock entrypoint script that outputs specified lines."""
        script_content = f'''#!/usr/bin/env python3
import sys
import time

# Output the specified lines
lines = {output_lines}
for line in lines:
    print(line)
    sys.stdout.flush()
    time.sleep(0.1)  # Small delay to simulate processing

# Exit successfully
sys.exit(0)
'''
        return script_content
    
    @pytest.mark.asyncio
    async def test_json_beacon_progress_tracking(self, mock_job_id, mock_job_items, mock_env):
        """Test progress tracking using JSON status beacons."""
        # Create a temporary script that outputs JSON beacons
        output_lines = [
            "Starting pipeline processing...",
            '{"item_done": 1}',  # First item completed
            "Processing item 2...",
            '{"item_done": 2}',  # Second item completed
            "Processing item 3...",
            '{"item_done": 3}',  # Third item completed
            "All items processed successfully!"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.create_mock_entrypoint(output_lines))
            entrypoint_path = f.name
        
        try:
            # Create a job in storage
            job = await create_job(mock_job_items)
            job_id = job.id
            
            # Mock the ENTRYPOINT_PATH
            with patch('src.core.background.tasks.ENTRYPOINT_PATH', Path(entrypoint_path)):
                # Execute the pipeline
                exit_code, stdout, stderr = await _execute_pipeline_async(job_id, mock_job_items, mock_env)
                
                # Verify successful execution
                assert exit_code == 0
                assert "All items processed successfully!" in stdout
                
                # Verify progress was updated
                final_job = await get_job(job_id)
                assert final_job is not None
                assert final_job.progress == 100  # Should be 100% complete
                
                # Verify all JSON beacons were processed
                log_messages = [log.msg for log in final_job.logs]
                assert '{"item_done": 1}' in log_messages
                assert '{"item_done": 2}' in log_messages
                assert '{"item_done": 3}' in log_messages
                
        finally:
            # Clean up temporary file
            os.unlink(entrypoint_path)
    
    @pytest.mark.asyncio
    async def test_checkmark_fallback_progress_tracking(self, mock_job_id, mock_job_items, mock_env):
        """Test progress tracking fallback using checkmark counting."""
        # Create a temporary script that outputs checkmarks
        output_lines = [
            "Starting pipeline processing...",
            "Processing item 1... ✔",  # First item completed
            "Processing item 2... ✔",  # Second item completed
            "Processing item 3... ✔",  # Third item completed
            "All items processed successfully!"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.create_mock_entrypoint(output_lines))
            entrypoint_path = f.name
        
        try:
            # Create a job in storage
            job = await create_job(mock_job_items)
            job_id = job.id
            
            # Mock the ENTRYPOINT_PATH
            with patch('src.core.background.tasks.ENTRYPOINT_PATH', Path(entrypoint_path)):
                # Execute the pipeline
                exit_code, stdout, stderr = await _execute_pipeline_async(job_id, mock_job_items, mock_env)
                
                # Verify successful execution
                assert exit_code == 0
                assert "All items processed successfully!" in stdout
                
                # Verify progress was updated
                final_job = await get_job(job_id)
                assert final_job is not None
                assert final_job.progress == 100  # Should be 100% complete
                
                # Verify all checkmarks were processed
                log_messages = [log.msg for log in final_job.logs]
                checkmark_logs = [msg for msg in log_messages if "✔" in msg]
                assert len(checkmark_logs) == 3
                
        finally:
            # Clean up temporary file
            os.unlink(entrypoint_path)
    
    @pytest.mark.asyncio
    async def test_mixed_progress_tracking(self, mock_job_id, mock_job_items, mock_env):
        """Test progress tracking with mixed JSON beacons and checkmarks."""
        # Create a temporary script that outputs both JSON and checkmarks
        output_lines = [
            "Starting pipeline processing...",
            '{"item_done": 1}',  # First item via JSON
            "Processing item 2... ✔",  # Second item via checkmark
            '{"item_done": 3}',  # Third item via JSON (should override checkmark count)
            "All items processed successfully!"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.create_mock_entrypoint(output_lines))
            entrypoint_path = f.name
        
        try:
            # Create a job in storage
            job = await create_job(mock_job_items)
            job_id = job.id
            
            # Mock the ENTRYPOINT_PATH
            with patch('src.core.background.tasks.ENTRYPOINT_PATH', Path(entrypoint_path)):
                # Execute the pipeline
                exit_code, stdout, stderr = await _execute_pipeline_async(job_id, mock_job_items, mock_env)
                
                # Verify successful execution
                assert exit_code == 0
                assert "All items processed successfully!" in stdout
                
                # Verify progress was updated
                final_job = await get_job(job_id)
                assert final_job is not None
                assert final_job.progress == 100  # Should be 100% complete
                
        finally:
            # Clean up temporary file
            os.unlink(entrypoint_path)
    
    @pytest.mark.asyncio
    async def test_run_job_status_transitions(self, mock_job_items):
        """Test complete job status transitions through run_job function."""
        # Create a successful mock pipeline
        output_lines = [
            "Starting pipeline processing...",
            '{"item_done": 1}',
            '{"item_done": 2}',
            '{"item_done": 3}',
            "All items processed successfully!"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.create_mock_entrypoint(output_lines))
            entrypoint_path = f.name
        
        try:
            # Create a job in storage
            job = await create_job(mock_job_items)
            job_id = job.id
            
            # Mock the ENTRYPOINT_PATH and concurrency manager
            with patch('src.core.background.tasks.ENTRYPOINT_PATH', Path(entrypoint_path)):
                with patch('src.core.background.tasks.get_concurrency_manager') as mock_concurrency:
                    # Mock the concurrency manager to directly execute the function
                    mock_concurrency.return_value.submit_job = AsyncMock(
                        side_effect=lambda func, *args: func(*args)
                    )
                    
                    # Execute the job
                    await run_job(job_id)
                    
                    # Verify final job state
                    final_job = await get_job(job_id)
                    assert final_job is not None
                    assert final_job.status == JobStatus.COMPLETED
                    assert final_job.progress == 100
                    
                    # Verify status transitions in logs
                    log_messages = [log.msg for log in final_job.logs]
                    
                    # Check for key status messages
                    assert any("Job queued for processing" in msg for msg in log_messages)
                    assert any("Started processing" in msg for msg in log_messages)
                    assert any("Processing completed successfully" in msg for msg in log_messages)
                    
        finally:
            # Clean up temporary file
            os.unlink(entrypoint_path)
    
    @pytest.mark.asyncio
    async def test_run_job_failure_status(self, mock_job_items):
        """Test job failure status transitions."""
        # Create a failing mock pipeline
        script_content = '''#!/usr/bin/env python3
import sys
print("Starting pipeline processing...")
print("Processing item 1...")
print("ERROR: Something went wrong!", file=sys.stderr)
sys.exit(1)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            entrypoint_path = f.name
        
        try:
            # Create a job in storage
            job = await create_job(mock_job_items)
            job_id = job.id
            
            # Mock the ENTRYPOINT_PATH and concurrency manager
            with patch('src.core.background.tasks.ENTRYPOINT_PATH', Path(entrypoint_path)):
                with patch('src.core.background.tasks.get_concurrency_manager') as mock_concurrency:
                    # Mock the concurrency manager to directly execute the function
                    mock_concurrency.return_value.submit_job = AsyncMock(
                        side_effect=lambda func, *args: func(*args)
                    )
                    
                    # Execute the job
                    await run_job(job_id)
                    
                    # Verify final job state
                    final_job = await get_job(job_id)
                    assert final_job is not None
                    assert final_job.status == JobStatus.FAILED
                    
                    # Verify failure message in logs
                    log_messages = [log.msg for log in final_job.logs]
                    assert any("Pipeline execution failed" in msg for msg in log_messages)
                    
        finally:
            # Clean up temporary file
            os.unlink(entrypoint_path)
    
    @pytest.mark.asyncio
    async def test_explicit_status_transitions(self, mock_job_items):
        """Test explicit status transitions: PENDING -> RUNNING -> COMPLETED."""
        # Create a successful mock pipeline
        output_lines = [
            "Starting pipeline processing...",
            '{"item_done": 1}',
            '{"item_done": 2}',
            '{"item_done": 3}',
            "All items processed successfully!"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.create_mock_entrypoint(output_lines))
            entrypoint_path = f.name
        
        try:
            # Create a job in storage
            job = await create_job(mock_job_items)
            job_id = job.id
            
            # Track status changes
            status_changes = []
            
            # Mock update_job_status to track calls
            original_update = update_job_status
            async def track_status_updates(job_id, status=None, **kwargs):
                if status is not None:
                    status_changes.append(status)
                return await original_update(job_id, status=status, **kwargs)
            
            with patch('src.core.background.tasks.update_job_status', side_effect=track_status_updates):
                with patch('src.core.background.tasks.ENTRYPOINT_PATH', Path(entrypoint_path)):
                    with patch('src.core.background.tasks.get_concurrency_manager') as mock_concurrency:
                        # Mock the concurrency manager to directly execute the function
                        mock_concurrency.return_value.submit_job = AsyncMock(
                            side_effect=lambda func, *args: func(*args)
                        )
                        
                        # Execute the job
                        await run_job(job_id)
                        
                        # Verify status transitions
                        assert JobStatus.PENDING in status_changes
                        assert JobStatus.RUNNING in status_changes
                        assert JobStatus.COMPLETED in status_changes
                        
                        # Verify order of transitions
                        pending_index = status_changes.index(JobStatus.PENDING)
                        running_index = status_changes.index(JobStatus.RUNNING)
                        completed_index = status_changes.index(JobStatus.COMPLETED)
                        
                        assert pending_index < running_index < completed_index
                        
        finally:
            # Clean up temporary file
            os.unlink(entrypoint_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
