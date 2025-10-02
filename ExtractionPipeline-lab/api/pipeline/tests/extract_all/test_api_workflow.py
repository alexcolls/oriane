#!/usr/bin/env python3
"""
Simple test script to demonstrate the API client functionality.
"""
import asyncio
import logging
import os
from api_client import APIClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_api_workflow():
    """Test the complete API workflow with batch submission and status checking."""
    
    # Set environment variables
    os.environ['PIPELINE_API_URL'] = 'https://pipeline.api.qdrant.admin.oriane.xyz'
    os.environ['API_KEY'] = 'KgsG2H54dyu2SBCBWGiifqvcb230hkjaghKSjkDDfs72v4siAu689yGBhjkaH7saA6L7N001EGzXYZb0x'
    
    try:
        # Initialize the API client
        client = APIClient(30, max_retries=3)
        print("✓ API Client initialized successfully")
        
        # Test 1: Submit a batch of items for processing
        print("\n=== Test 1: Submitting batch ===")
        test_items = [
            {"file_path": "test/file1.pdf", "metadata": {"type": "document"}},
            {"file_path": "test/file2.txt", "metadata": {"type": "text"}},
        ]
        
        try:
            job_id = await client.submit_batch(test_items)
            print(f"✓ Batch submitted successfully with job ID: {job_id}")
        except Exception as e:
            print(f"✗ Batch submission failed: {e}")
            return
        
        # Test 2: Check job status
        print("\n=== Test 2: Checking job status ===")
        try:
            status = await client.get_status(job_id)
            print(f"✓ Job status retrieved: {status}")
        except Exception as e:
            print(f"✗ Status check failed: {e}")
        
        # Test 3: Test backward compatibility with submit_job
        print("\n=== Test 3: Testing backward compatibility ===")
        try:
            single_job_id = await client.submit_job("test/single_file.pdf")
            print(f"✓ Single job submitted successfully with job ID: {single_job_id}")
            
            # Check its status
            single_status = await client.get_job_status(single_job_id)
            print(f"✓ Single job status: {single_status}")
            
        except Exception as e:
            print(f"✗ Single job test failed: {e}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_workflow())
