#!/usr/bin/env python3
"""
Test script for the API client implementation.
"""
import asyncio
import logging
import os
from api_client import APIClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_api_client():
    """Test the API client basic functionality."""
    
    # Set minimal environment for testing
    os.environ['PIPELINE_API_URL'] = 'https://api.example.com'
    os.environ['API_KEY'] = 'test-key'
    
    try:
        # Initialize client
        client = APIClient(timeout=10, max_retries=2)
        print("✓ API Client initialized successfully")
        
        # Test that headers are set correctly
        expected_headers = {
            'Content-Type': 'application/json',
            'x-api-key': 'test-key'
        }
        assert client.headers == expected_headers
        print("✓ Headers configured correctly")
        
        # Test that base URL is set
        assert client.base_url == 'https://api.example.com'
        print("✓ Base URL configured correctly")
        
        # Test validation
        os.environ.pop('PIPELINE_API_URL', None)
        try:
            APIClient()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print("✓ Validation works - raises error when PIPELINE_API_URL is missing")
        
        print("\n✅ All basic tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_api_client())
