#!/usr/bin/env python3
"""
Test runner script for background tasks tests.
"""

import sys
import subprocess
import os

def run_tests():
    """Run the background tasks tests."""
    # Change to the source directory
    os.chdir('/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/src')
    
    # Run the tests
    cmd = [sys.executable, '-m', 'pytest', 'tests/test_background_tasks.py', '-v', '--tb=short']
    
    print("Running tests...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
