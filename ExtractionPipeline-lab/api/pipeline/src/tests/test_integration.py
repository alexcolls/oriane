#!/usr/bin/env python3
"""
Integration test for background tasks with progress tracking.
This test demonstrates the real-time status and progress updates functionality.
"""

import asyncio
import json
import tempfile
import os
from pathlib import Path
from uuid import uuid4

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, '/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/src')

from src.core.models.job import create_job, get_job, JobStatus
from src.core.background.tasks import _execute_pipeline_async

async def test_json_beacon_progress():
    """Test that demonstrates JSON beacon progress tracking."""
    print("Testing JSON beacon progress tracking...")
    
    # Create test job items
    job_items = [
        {"id": 1, "video_url": "https://example.com/video1.mp4"},
        {"id": 2, "video_url": "https://example.com/video2.mp4"},
        {"id": 3, "video_url": "https://example.com/video3.mp4"}
    ]
    
    # Create a job in storage
    job = await create_job(job_items)
    job_id = job.id
    
    # Create a mock entrypoint script that outputs JSON beacons
    output_lines = [
        "Starting pipeline processing...",
        '{"item_done": 1}',  # First item completed
        "Processing item 2...",
        '{"item_done": 2}',  # Second item completed
        "Processing item 3...",
        '{"item_done": 3}',  # Third item completed
        "All items processed successfully!"
    ]
    
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        entrypoint_path = f.name
    
    try:
        # Mock environment
        env = {
            "DEBUG_PIPELINE": "1",
            "JOB_INPUT": json.dumps(job_items)
        }
        
        # Temporarily replace the ENTRYPOINT_PATH
        import src.core.background.tasks as tasks_module
        original_entrypoint = tasks_module.ENTRYPOINT_PATH
        tasks_module.ENTRYPOINT_PATH = Path(entrypoint_path)
        
        try:
            # Execute the pipeline
            exit_code, stdout, stderr = await _execute_pipeline_async(job_id, job_items, env)
            
            print(f"Exit code: {exit_code}")
            print(f"Stdout: {stdout}")
            print(f"Stderr: {stderr}")
            
            # Verify results
            final_job = await get_job(job_id)
            print(f"Final job status: {final_job.status}")
            print(f"Final job progress: {final_job.progress}")
            
            # Check logs
            log_messages = [log.msg for log in final_job.logs]
            print(f"Log messages: {log_messages}")
            
            # Verify expectations
            assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
            assert "All items processed successfully!" in stdout, "Expected success message in stdout"
            assert final_job.progress == 100, f"Expected progress 100, got {final_job.progress}"
            
            # Verify JSON beacons were processed
            assert '{"item_done": 1}' in log_messages, "Expected JSON beacon 1 in logs"
            assert '{"item_done": 2}' in log_messages, "Expected JSON beacon 2 in logs"
            assert '{"item_done": 3}' in log_messages, "Expected JSON beacon 3 in logs"
            
            print("✅ JSON beacon progress tracking test PASSED!")
            
        finally:
            # Restore original entrypoint
            tasks_module.ENTRYPOINT_PATH = original_entrypoint
            
    finally:
        # Clean up temporary file
        os.unlink(entrypoint_path)

async def test_checkmark_progress():
    """Test that demonstrates checkmark progress tracking."""
    print("\nTesting checkmark progress tracking...")
    
    # Create test job items
    job_items = [
        {"id": 1, "video_url": "https://example.com/video1.mp4"},
        {"id": 2, "video_url": "https://example.com/video2.mp4"},
        {"id": 3, "video_url": "https://example.com/video3.mp4"}
    ]
    
    # Create a job in storage
    job = await create_job(job_items)
    job_id = job.id
    
    # Create a mock entrypoint script that outputs checkmarks
    output_lines = [
        "Starting pipeline processing...",
        "Processing item 1... ✔",  # First item completed
        "Processing item 2... ✔",  # Second item completed
        "Processing item 3... ✔",  # Third item completed
        "All items processed successfully!"
    ]
    
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        entrypoint_path = f.name
    
    try:
        # Mock environment
        env = {
            "DEBUG_PIPELINE": "1",
            "JOB_INPUT": json.dumps(job_items)
        }
        
        # Temporarily replace the ENTRYPOINT_PATH
        import src.core.background.tasks as tasks_module
        original_entrypoint = tasks_module.ENTRYPOINT_PATH
        tasks_module.ENTRYPOINT_PATH = Path(entrypoint_path)
        
        try:
            # Execute the pipeline
            exit_code, stdout, stderr = await _execute_pipeline_async(job_id, job_items, env)
            
            print(f"Exit code: {exit_code}")
            print(f"Stdout: {stdout}")
            print(f"Stderr: {stderr}")
            
            # Verify results
            final_job = await get_job(job_id)
            print(f"Final job status: {final_job.status}")
            print(f"Final job progress: {final_job.progress}")
            
            # Check logs
            log_messages = [log.msg for log in final_job.logs]
            print(f"Log messages: {log_messages}")
            
            # Verify expectations
            assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
            assert "All items processed successfully!" in stdout, "Expected success message in stdout"
            assert final_job.progress == 100, f"Expected progress 100, got {final_job.progress}"
            
            # Verify checkmarks were processed
            checkmark_logs = [msg for msg in log_messages if "✔" in msg]
            assert len(checkmark_logs) == 3, f"Expected 3 checkmark logs, got {len(checkmark_logs)}"
            
            print("✅ Checkmark progress tracking test PASSED!")
            
        finally:
            # Restore original entrypoint
            tasks_module.ENTRYPOINT_PATH = original_entrypoint
            
    finally:
        # Clean up temporary file
        os.unlink(entrypoint_path)

async def main():
    """Run all tests."""
    print("Running integration tests for background tasks...")
    
    try:
        await test_json_beacon_progress()
        await test_checkmark_progress()
        print("\n🎉 All tests PASSED!")
        return True
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
