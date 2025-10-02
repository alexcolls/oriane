#!/usr/bin/env python3
"""
Enhanced test script for JobMonitor functionality with batch processing and retry logic.
"""
import asyncio
import json
from pathlib import Path
from job_monitor import JobMonitor, JobStatus
from config import Config


class MockAPIClient:
    """Mock API client for testing."""
    
    def __init__(self, responses):
        self.responses = responses
        self.call_counts = {}
    
    async def get_job_status(self, job_id):
        """Mock get_job_status method."""
        if job_id not in self.call_counts:
            self.call_counts[job_id] = 0
            
        if job_id in self.responses:
            response_list = self.responses[job_id]
            response_index = min(self.call_counts[job_id], len(response_list) - 1)
            response = response_list[response_index]
            self.call_counts[job_id] += 1
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
    
    def __init__(self):
        self.processed_files = {}
        self.failed_files = {}
    
    async def mark_processed(self, code, job_id=None, result=None):
        self.processed_files[code] = {"job_id": job_id, "result": result}
        print(f"Mock: Marked {code} as processed (job: {job_id})")
        return True
    
    async def mark_failed(self, code, job_id, error, retry_count=0):
        self.failed_files[code] = {"job_id": job_id, "error": error, "retry_count": retry_count}
        print(f"Mock: Marked {code} as failed (job: {job_id}, error: {error}, retry: {retry_count})")
        return True
    
    async def get_failed_files(self):
        return set(self.failed_files.keys())
    
    async def get_file_status(self, file_key):
        if file_key in self.failed_files:
            return self.failed_files[file_key]
        return None


async def test_basic_job_monitoring():
    """Test basic job monitoring functionality."""
    print("=" * 60)
    print("Testing basic job monitoring...")
    
    # Create mock responses
    mock_responses = {
        "job_success": [
            {"status": "pending"},
            {"status": "running"},
            {"status": "completed", "result": "success"}
        ],
        "job_failed": [
            {"status": "pending"},
            {"status": "running"},
            {"status": "failed", "error": "Processing failed"}
        ]
    }
    
    config = Config(interval=0.5, timeout=30)
    api_client = MockAPIClient(mock_responses)
    state_manager = MockStateManager()
    job_monitor = JobMonitor(config, api_client, state_manager)
    
    # Test successful job
    result = await job_monitor.monitor_job("job_success", timeout=5)
    print(f"Success result: {result}")
    assert result["status"] == "completed"
    
    # Test failed job
    result = await job_monitor.monitor_job("job_failed", timeout=5)
    print(f"Failed result: {result}")
    assert result["status"] == "failed"
    
    print("✓ Basic job monitoring tests passed")


async def test_batch_processing():
    """Test batch processing with concurrent jobs."""
    print("\n" + "=" * 60)
    print("Testing batch processing...")
    
    # Create mock responses for batch processing
    mock_responses = {
        "batch_job_1": [
            {"status": "pending"},
            {"status": "completed", "result": "success"}
        ],
        "batch_job_2": [
            {"status": "running"},
            {"status": "completed", "result": "success"}
        ],
        "batch_job_3": [
            {"status": "pending"},
            {"status": "failed", "error": "Network error"}
        ]
    }
    
    config = Config(interval=0.5, timeout=30)
    api_client = MockAPIClient(mock_responses)
    state_manager = MockStateManager()
    job_monitor = JobMonitor(config, api_client, state_manager)
    
    # Test batch processing
    job_ids = ["batch_job_1", "batch_job_2", "batch_job_3"]
    results = await job_monitor.monitor_multiple_jobs(job_ids, timeout=5)
    
    print(f"Batch results: {results}")
    assert len(results) == 3
    assert results["batch_job_1"]["status"] == "completed"
    assert results["batch_job_2"]["status"] == "completed"
    assert results["batch_job_3"]["status"] == "failed"
    
    print("✓ Batch processing tests passed")


async def test_batch_with_retry():
    """Test batch processing with retry logic."""
    print("\n" + "=" * 60)
    print("Testing batch processing with retry logic...")
    
    # Create mock responses for retry testing
    mock_responses = {
        "retry_job_1": [
            {"status": "pending"},
            {"status": "completed", "result": "success"}
        ],
        "retry_job_2": [
            {"status": "running"},
            {"status": "failed", "error": "Temporary error"},
            {"status": "completed", "result": "success"}  # Succeeds on retry
        ],
        "retry_job_3": [
            {"status": "pending"},
            {"status": "failed", "error": "Permanent error"},
            {"status": "failed", "error": "Still failing"}  # Fails on retry
        ]
    }
    
    config = Config(interval=0.5, timeout=30)
    api_client = MockAPIClient(mock_responses)
    state_manager = MockStateManager()
    job_monitor = JobMonitor(config, api_client, state_manager)
    
    # Test batch processing with retry
    job_ids = ["retry_job_1", "retry_job_2", "retry_job_3"]
    batch_result = await job_monitor.process_batch_with_retry(job_ids, max_retries=2, timeout=5)
    
    print(f"Batch with retry result: {batch_result}")
    assert batch_result["total_jobs"] == 3
    assert batch_result["successful"] >= 2  # At least 2 should succeed
    assert batch_result["retry_attempts"] > 0
    
    print(f"Success rate: {batch_result['success_rate']:.1f}%")
    print("✓ Batch processing with retry tests passed")


async def test_file_output():
    """Test file output functionality."""
    print("\n" + "=" * 60)
    print("Testing file output...")
    
    # Clean up any existing files
    for file_path in Path("responses").glob("*.json"):
        file_path.unlink()
    for file_path in Path("logs").glob("*.log"):
        file_path.unlink()
    
    # Create mock responses
    mock_responses = {
        "file_job_1": [
            {"status": "pending"},
            {"status": "completed", "result": "success"}
        ],
        "file_job_2": [
            {"status": "running"},
            {"status": "failed", "error": "Processing error"}
        ]
    }
    
    config = Config(interval=0.5, timeout=30)
    api_client = MockAPIClient(mock_responses)
    state_manager = MockStateManager()
    job_monitor = JobMonitor(config, api_client, state_manager)
    
    # Process jobs
    await job_monitor.monitor_job("file_job_1", timeout=5)
    await job_monitor.monitor_job("file_job_2", timeout=5)
    
    # Check output files
    response_files = list(Path("responses").glob("batch-*.json"))
    log_files = list(Path("logs").glob("batch-*.log"))
    
    print(f"Created {len(response_files)} response files")
    print(f"Created {len(log_files)} log files")
    
    assert len(response_files) >= 2
    assert len(log_files) >= 2
    
    # Check content of first response file
    if response_files:
        with open(response_files[0], 'r') as f:
            response_data = json.load(f)
            print(f"Sample response data: {response_data}")
            assert "job_id" in response_data or "result" in response_data
    
    # Check content of first log file
    if log_files:
        with open(log_files[0], 'r') as f:
            log_content = f.read()
            print(f"Sample log content: {log_content[:100]}...")
            assert "completed" in log_content or "failed" in log_content
    
    print("✓ File output tests passed")


async def test_statistics():
    """Test statistics functionality."""
    print("\n" + "=" * 60)
    print("Testing statistics...")
    
    config = Config(interval=0.5, timeout=30)
    api_client = MockAPIClient({})
    state_manager = MockStateManager()
    job_monitor = JobMonitor(config, api_client, state_manager)
    
    # Get initial statistics
    stats = await job_monitor.get_job_statistics()
    print(f"Initial statistics: {stats}")
    
    assert stats["active_jobs_count"] == 0
    assert "monitoring_config" in stats
    assert stats["monitoring_config"]["polling_interval"] == 0.5
    
    print("✓ Statistics tests passed")


async def main():
    """Run all tests."""
    try:
        await test_basic_job_monitoring()
        await test_batch_processing()
        await test_batch_with_retry()
        await test_file_output()
        await test_statistics()
        
        print("\n" + "=" * 60)
        print("🎉 All enhanced tests passed!")
        print("Job monitoring system is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
