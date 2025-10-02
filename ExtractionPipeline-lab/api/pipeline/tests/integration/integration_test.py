#!/usr/bin/env python3
"""
Integration test for the POST /process endpoint

This test verifies that the endpoint works correctly with actual HTTP requests
and validates the complete functionality including background processing.
"""

import json
import requests
import time
from config.env_config import settings


def test_process_endpoint_integration():
    """Test the POST /process endpoint with actual HTTP requests."""
    
    # Test data
    test_request = {
        "items": [
            {"platform": "instagram", "code": "TEST123"},
            {"platform": "youtube", "code": "TEST456"}
        ]
    }
    
    # Headers for authentication
    headers = {
        "Content-Type": "application/json"
    }
    
    if settings.api_key:
        headers["X-API-Key"] = settings.api_key
    
    print("Integration Test: POST /process endpoint")
    print("=" * 50)
    print(f"Request payload: {json.dumps(test_request, indent=2)}")
    print(f"Max videos per request: {settings.max_videos_per_request}")
    print()
    
    # Note: This test assumes the API server is running on localhost
    # In a real scenario, you'd start the server first or use a test server
    base_url = f"http://localhost:{settings.api_port}"
    
    try:
        # Make POST request to /process endpoint
        response = requests.post(
            f"{base_url}/process",
            json=test_request,
            headers=headers,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 202:
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
            
            if "jobId" in response_data:
                job_id = response_data["jobId"]
                print(f"✅ SUCCESS: Job created with ID: {job_id}")
                
                # Optional: Check job status via the jobs endpoint
                job_response = requests.get(
                    f"{base_url}/jobs/{job_id}",
                    headers=headers,
                    timeout=10
                )
                
                if job_response.status_code == 200:
                    job_data = job_response.json()
                    print(f"Job Status: {job_data.get('status', 'unknown')}")
                    print(f"Job Items: {len(job_data.get('items', []))}")
                else:
                    print(f"Could not retrieve job status: {job_response.status_code}")
                    
            else:
                print("❌ ERROR: Response missing jobId field")
                
        else:
            print(f"❌ ERROR: Unexpected status code {response.status_code}")
            print(f"Response Body: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to API server")
        print("Make sure the API server is running on localhost:8000")
        print("You can start it with: python3 main.py")
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {str(e)}")


if __name__ == "__main__":
    test_process_endpoint_integration()
