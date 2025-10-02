#!/usr/bin/env python3
"""
HTTP API Test Script
This script demonstrates how to use the Pipeline API via HTTP requests.
"""

import json
import time
import requests
import sys
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"  # Replace with actual API key

def test_http_api():
    """Test the API via HTTP requests."""
    print("🌐 Testing Pipeline API via HTTP")
    print("=" * 50)
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check successful")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Create a job
    print("\n2. Creating a job...")
    try:
        # Load test data
        with open("test_sample.json", "r") as f:
            test_data = json.load(f)
        
        job_request = {
            "items": test_data,
            "batch_size": 2,
            "local_mode": True,
            "skip_upload": True
        }
        
        response = requests.post(
            f"{API_BASE_URL}/jobs/",
            headers=headers,
            json=job_request
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✅ Job created successfully")
            print(f"   Job ID: {job_id}")
            print(f"   Status: {job_data['status']}")
        else:
            print(f"❌ Job creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Job creation failed: {e}")
        return False
    
    # Test 3: Get job status
    print("\n3. Getting job status...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/jobs/{job_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            job_data = response.json()
            print(f"✅ Job status retrieved")
            print(f"   Status: {job_data['status']}")
            print(f"   Items: {len(job_data['items'])}")
        else:
            print(f"❌ Job status retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Job status retrieval failed: {e}")
        return False
    
    # Test 4: List all jobs
    print("\n4. Listing all jobs...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/jobs/",
            headers=headers
        )
        
        if response.status_code == 200:
            jobs_data = response.json()
            print(f"✅ Jobs listed successfully")
            print(f"   Total jobs: {jobs_data['total']}")
            for job in jobs_data['jobs']:
                print(f"   - {job['job_id']}: {job['status']}")
        else:
            print(f"❌ Job listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Job listing failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 HTTP API tests completed successfully!")
    return True

def generate_curl_commands():
    """Generate curl commands for API testing."""
    print("\n🔧 Curl Commands for API Testing")
    print("=" * 50)
    
    print("# 1. Health check")
    print("curl -X GET http://localhost:8000/health")
    
    print("\n# 2. Create a job")
    print("curl -X POST http://localhost:8000/jobs/ \\")
    print("  -H 'X-API-Key: your-api-key-here' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{")
    print('    "items": [')
    print('      {"platform": "instagram", "code": "DHrbLqfv-ka"},')
    print('      {"platform": "instagram", "code": "DI3l1xMJOyR"}')
    print('    ],')
    print('    "batch_size": 2,')
    print('    "local_mode": true,')
    print('    "skip_upload": true')
    print("  }'")
    
    print("\n# 3. Get job status (replace JOB_ID with actual job ID)")
    print("curl -X GET http://localhost:8000/jobs/JOB_ID \\")
    print("  -H 'X-API-Key: your-api-key-here'")
    
    print("\n# 4. List all jobs")
    print("curl -X GET http://localhost:8000/jobs/ \\")
    print("  -H 'X-API-Key: your-api-key-here'")
    
    print("\n# 5. Start a job (replace JOB_ID with actual job ID)")
    print("curl -X POST http://localhost:8000/jobs/JOB_ID/start \\")
    print("  -H 'X-API-Key: your-api-key-here'")
    
    print("\n# 6. Stop a job (replace JOB_ID with actual job ID)")
    print("curl -X POST http://localhost:8000/jobs/JOB_ID/stop \\")
    print("  -H 'X-API-Key: your-api-key-here'")
    
    print("\n# 7. Get job logs (replace JOB_ID with actual job ID)")
    print("curl -X GET http://localhost:8000/jobs/JOB_ID/logs \\")
    print("  -H 'X-API-Key: your-api-key-here'")
    
    print("\n# 8. Get job progress (replace JOB_ID with actual job ID)")
    print("curl -X GET http://localhost:8000/jobs/JOB_ID/progress \\")
    print("  -H 'X-API-Key: your-api-key-here'")

def create_sample_request_100_videos():
    """Create a sample request for 100 videos."""
    print("\n📋 Sample Request for 100 Videos")
    print("=" * 50)
    
    try:
        # Load the full dataset
        with open("test/job_input.json", "r") as f:
            full_data = json.load(f)
        
        # Take first 100 items
        test_100 = full_data[:100]
        
        sample_request = {
            "items": test_100,
            "batch_size": 10,
            "local_mode": False,  # Enable DB writes for production
            "skip_upload": False  # Enable S3 upload for production
        }
        
        print("JSON payload for 100 videos:")
        print(json.dumps(sample_request, indent=2)[:500] + "...")
        
        print(f"\nRequest summary:")
        print(f"  - Videos: {len(test_100)}")
        print(f"  - Batch size: {sample_request['batch_size']}")
        print(f"  - Local mode: {sample_request['local_mode']}")
        print(f"  - Skip upload: {sample_request['skip_upload']}")
        
        # Save sample request to file
        with open("sample_100_videos_request.json", "w") as f:
            json.dump(sample_request, f, indent=2)
        
        print(f"\n✅ Sample request saved to 'sample_100_videos_request.json'")
        
        # Generate curl command for 100 videos
        print("\n🔧 Curl command for 100 videos:")
        print("curl -X POST http://localhost:8000/jobs/ \\")
        print("  -H 'X-API-Key: your-api-key-here' \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d @sample_100_videos_request.json")
        
    except Exception as e:
        print(f"❌ Failed to create sample request: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server-running":
        # Only run HTTP tests if server is running
        test_http_api()
    else:
        print("💡 To run HTTP tests, start the server first with:")
        print("   ./run-dev.sh")
        print("   python3 test_http_api.py --server-running")
        print("")
        
    generate_curl_commands()
    create_sample_request_100_videos()
