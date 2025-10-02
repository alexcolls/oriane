#!/usr/bin/env python3
"""
Test script for JobMonitor functionality.
"""
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from job_monitor import JobMonitor, JobStatus
from config import Config


class MockAPIClient:
    """Mock API client for testing."""
    
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
    
    async def get_job_status(self, job_id):
        """Mock get_job_status method."""
        if job_id in self.responses:
            response = self.responses[job_id][self.call_count % len(self.responses[job_id])]
            self.call_count += 1
            return response
        return {"status": "unknown"}
    
    async def get_job_result(self, job_id):
        """Mock get_job_result method."""
        return {"job_id": job_id, "result": "success", "data": {"processed": True}}
    
    async def cancel_job(self, job_id):
        """Mock cancel_job method."""
        return True


class MockStateManager:
    """Mock state manager for testing."""
    
    async def mark_processed(self, code, job_id=None, result=None):
        print(f"Mock: Marked {code} as processed (job: {job_id})")
        return True
    
    async def mark_failed(self, code, job_id, error, retry_count=0):
        print(f"Mock: Marked {code} as failed (job: {job_id}, error: {error})")
        return True


async def test_successful_job():
    """Test successful job monitoring."""
    print("Testing successful job monitoring...")
    
    # Create mock responses
    mock_responses = {
        "job_123": [
            {"status": "pending"},
            {"status": "running"},
            {"status": "completed", "result": "success"}
        ]
    }
    
    # Create mocks
    config = Config(interval=1, timeout=30)  # Short interval for testing
    api_client = MockAPIClient(mock_responses)
    state_manager = MockStateManager()
    
    # Create job monitor
    job_monitor = JobMonitor(config, api_client, state_manager)
    
    # Test monitoring
    result = await job_monitor.monitor_job("job_123", timeout=10)
    
    print(f"Result: {result}")
    assert result["status"] == "completed"
    assert result["job_id"] == "job_123"
    
    # Check if response file was created
    response_file = Path("responses/batch-0.json")
    log_file = Path("logs/batch-0.log")
    
    if response_file.exists():
        print(f"Response file created: {response_file}")
        with open(response_file, 'r') as f:
            response_data = json.load(f)
            print(f"Response data: {response_data}")
    
    if log_file.exists():
        print(f"Log file created: {log_file}")
        with open(log_file, 'r') as f:
            log_data = f.read()
            print(f"Log data: {log_data}")
    
    print("✓ Successful job test passed")


async def test_failed_job():
    """Test failed job monitoring."""
    print("\nTesting failed job monitoring...")
    
    # Create mock responses for failed job
    mock_responses = {
        "job_456": [
            {"status": "pending"},
            {"status": "running"},
            {"status": "failed", "error": "Processing failed due to invalid input"}
        ]
    }
    
    # Create mocks
    config = Config(interval=1, timeout=30)  # Short interval for testing
    api_client = MockAPIClient(mock_responses)
    state_manager = MockStateManager()
    
    # Create job monitor
    job_monitor = JobMonitor(config, api_client, state_manager)
    
    # Test monitoring
    result = await job_monitor.monitor_job("job_456", timeout=10)
    
    print(f"Result: {result}")
    assert result["status"] == "failed"
    assert result["job_id"] == "job_456"
    
    # Check if response file was created
    response_file = Path("responses/batch-0.json")
    log_file = Path("logs/batch-0.log")
    
    if response_file.exists():
        print(f"Response file created: {response_file}")
        with open(response_file, 'r') as f:
            response_data = json.load(f)
            print(f"Response data: {response_data}")
    
    if log_file.exists():
        print(f"Log file created: {log_file}")
        with open(log_file, 'r') as f:
            log_data = f.read()
            print(f"Log data: {log_data}")
    
    print("✓ Failed job test passed")


async def test_multiple_jobs():
    """Test monitoring multiple jobs concurrently."""
    print("\nTesting multiple job monitoring...")
    
    # Create mock responses for multiple jobs
    mock_responses = {
        "job_001": [
            {"status": "pending"},
            {"status": "completed", "result": "success"}
        ],
        "job_002": [
            {"status": "running"},
            {"status": "failed", "error": "Network timeout"}
        ],
        "job_003": [
            {"status": "pending"},
            {"status": "running"},
            {"status": "completed", "result": "success"}
        ]
    }
    
    # Create mocks
    config = Config(interval=1, timeout=30)  # Short interval for testing
    api_client = MockAPIClient(mock_responses)
    state_manager = MockStateManager()
    
    # Create job monitor
    job_monitor = JobMonitor(config, api_client, state_manager)
    
    # Test monitoring multiple jobs
    results = await job_monitor.monitor_multiple_jobs(["job_001", "job_002", "job_003"], timeout=10)
    
    print(f"Results: {results}")
    assert len(results) == 3
    assert results["job_001"]["status"] == "completed"
    assert results["job_002"]["status"] == "failed"
    assert results["job_003"]["status"] == "completed"
    
    print("✓ Multiple jobs test passed")


async def main():
    """Run all tests."""
    try:
        await test_successful_job()
        await test_failed_job()
        await test_multiple_jobs()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
