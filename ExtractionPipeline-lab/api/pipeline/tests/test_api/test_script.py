#!/usr/bin/env python3
"""
End-to-end test script for the Oriane pipeline API.
This script submits a job, polls for completion, and reports progress.
"""

import json
import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_timestamp():
    """Get current timestamp for logging."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_json_payload(file_path):
    """Load JSON payload from file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[{get_timestamp()}] ERROR: JSON payload file not found at {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"[{get_timestamp()}] ERROR: Invalid JSON in payload file: {e}")
        return None

def submit_job(api_url, api_key, payload):
    """Submit job to the API and return job ID."""
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"[{get_timestamp()}] Submitting job to {api_url}/process")
        response = requests.post(f"{api_url}/process", json=payload, headers=headers)
        
        if response.status_code == 202:
            job_data = response.json()
            job_id = job_data.get('jobId')
            print(f"[{get_timestamp()}] Job submitted successfully. Job ID: {job_id}")
            return job_id
        else:
            print(f"[{get_timestamp()}] ERROR: Failed to submit job. Status: {response.status_code}")
            print(f"[{get_timestamp()}] Response: {response.text}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"[{get_timestamp()}] ERROR: Request failed: {e}")
        return None

def poll_job_status(api_url, api_key, job_id, timeout_minutes=30):
    """Poll job status until completion or timeout."""
    headers = {
        'X-API-Key': api_key
    }
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    poll_interval = 10  # seconds
    
    terminal_states = ['completed', 'failed', 'error', 'cancelled']
    
    print(f"[{get_timestamp()}] Starting to poll job status for job ID: {job_id}")
    
    while True:
        try:
            elapsed_time = time.time() - start_time
            
            # Check timeout
            if elapsed_time > timeout_seconds:
                print(f"[{get_timestamp()}] TIMEOUT: Job polling timed out after {timeout_minutes} minutes")
                return False
            
            # Poll status
            response = requests.get(f"{api_url}/status/{job_id}", headers=headers)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status', 'unknown')
                progress = status_data.get('progress', 0)
                log_tail = status_data.get('log_tail', '')
                
                # Print progress update
                print(f"[{get_timestamp()}] Job status: {status.upper()} | progress {progress}%")
                
                # Check if job is in terminal state
                if status.lower() in terminal_states:
                    if status.lower() == 'completed':
                        print(f"[{get_timestamp()}] SUCCESS: Job completed successfully!")
                        return True
                    else:
                        print(f"[{get_timestamp()}] Job finished with status: {status.upper()}")
                        # Print the job logs to see what went wrong
                        if log_tail:
                            print(f"[{get_timestamp()}] Job logs:")
                            print("─" * 50)
                            print(log_tail)
                            print("─" * 50)
                        return False
            
            else:
                print(f"[{get_timestamp()}] WARNING: Failed to get job status. Status: {response.status_code}")
                print(f"[{get_timestamp()}] Response: {response.text}")
            
        except requests.exceptions.RequestException as e:
            print(f"[{get_timestamp()}] ERROR: Request failed during polling: {e}")
        
        # Wait before next poll
        time.sleep(poll_interval)

def main():
    """Main function to orchestrate the end-to-end test."""
    print(f"[{get_timestamp()}] Starting end-to-end pipeline test")
    
    # Get configuration from environment variables
    api_url = os.getenv('API_URL')
    api_key = os.getenv('API_KEY')
    
    if not api_url or not api_key:
        print(f"[{get_timestamp()}] ERROR: Missing API_URL or API_KEY environment variables")
        return False
    
    print(f"[{get_timestamp()}] Using API URL: {api_url}")
    
    # Load JSON payload from absolute path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    payload_path = os.path.join(script_dir, "test-payload.json")
    payload = load_json_payload(payload_path)
    
    if not payload:
        return False
    
    print(f"[{get_timestamp()}] Loaded payload with {len(payload.get('items', []))} items")
    
    # Submit job
    job_id = submit_job(api_url, api_key, payload)
    
    if not job_id:
        print(f"[{get_timestamp()}] ERROR: Failed to submit job")
        return False
    
    # Poll for completion
    success = poll_job_status(api_url, api_key, job_id)
    
    if success:
        print(f"[{get_timestamp()}] Test completed successfully!")
        return True
    else:
        print(f"[{get_timestamp()}] Test failed or timed out")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
