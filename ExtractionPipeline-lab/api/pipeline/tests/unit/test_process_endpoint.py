#!/usr/bin/env python3
"""
Test script for the POST /process endpoint

This script tests the new /process endpoint to ensure it works correctly
with proper request validation and job creation.
"""

import asyncio
import json
from fastapi.testclient import TestClient
from src.api.app import app
from config.env_config import settings


def test_process_endpoint():
    """Test the POST /process endpoint functionality."""
    client = TestClient(app)
    
    # Test data
    test_request = {
        "items": [
            {"platform": "instagram", "code": "ABC123"},
            {"platform": "youtube", "code": "XYZ789"}
        ]
    }
    
    # Test headers (assuming API key authentication)
    headers = {"X-API-Key": settings.api_key} if settings.api_key else {}
    
    print("Testing POST /process endpoint...")
    print(f"Request: {json.dumps(test_request, indent=2)}")
    
    # Make the request
    response = client.post("/process", json=test_request, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Check if response is as expected
    if response.status_code == 202:
        response_data = response.json()
        if "jobId" in response_data:
            print("✅ SUCCESS: Endpoint working correctly!")
            print(f"Job ID: {response_data['jobId']}")
        else:
            print("❌ ERROR: Response missing jobId field")
    else:
        print(f"❌ ERROR: Unexpected status code {response.status_code}")
        print(f"Error details: {response.text}")


def test_validation_limits():
    """Test request validation limits."""
    client = TestClient(app)
    
    print(f"\nTesting validation limits (max: {settings.max_videos_per_request})...")
    
    # Test headers
    headers = {"X-API-Key": settings.api_key} if settings.api_key else {}
    
    # Test empty request
    empty_request = {"items": []}
    response = client.post("/process", json=empty_request, headers=headers)
    print(f"Empty request - Status: {response.status_code}")
    
    # Test request exceeding limits
    large_request = {
        "items": [
            {"platform": "instagram", "code": f"test{i}"} 
            for i in range(settings.max_videos_per_request + 1)
        ]
    }
    response = client.post("/process", json=large_request, headers=headers)
    print(f"Oversized request - Status: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ SUCCESS: Validation limits working correctly!")
    else:
        print(f"❌ ERROR: Expected 400 status code, got {response.status_code}")


if __name__ == "__main__":
    test_process_endpoint()
    test_validation_limits()
