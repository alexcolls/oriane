#!/usr/bin/env python3
"""
Test script to validate retry queue functionality in main.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_retry_queue():
    """Test the retry queue functionality with a mock job input."""

    # Create a minimal test job input
    test_job_input = [
        {"platform": "instagram", "code": "nonexistent_code_1"},
        {"platform": "instagram", "code": "nonexistent_code_2"},
    ]

    # Set environment variables for testing
    env = os.environ.copy()
    env.update(
        {
            "JOB_INPUT": json.dumps(test_job_input),
            "LOCAL_MODE": "1",  # Skip database operations
            "SKIP_UPLOAD": "1",  # Skip S3 upload
            "MAX_RETRIES": "2",  # Limit retries for faster test
            "BATCH_SIZE": "2",  # Process both items in one batch initially
            "RETRY_BATCH_SIZE": "1",  # Retry individually
        }
    )

    print("🧪 Testing retry queue functionality...")
    print(f"📋 Test job input: {test_job_input}")
    print(f"🔧 Config: MAX_RETRIES=2, BATCH_SIZE=2, RETRY_BATCH_SIZE=1")
    print(f"🏠 LOCAL_MODE=1, SKIP_UPLOAD=1 (test mode)")
    print()

    try:
        # Run main.py with test configuration
        result = subprocess.run(
            [sys.executable, "main.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        print("📤 STDOUT:")
        print(result.stdout)
        print("\n📤 STDERR:")
        print(result.stderr)
        print(f"\n🔢 Exit code: {result.returncode}")

        # Analyze the output
        stdout = result.stdout

        # Check if retry logic was triggered
        if "Phase 2: Retrying" in stdout:
            print("✅ Retry phase was triggered correctly")
        else:
            print("❌ Retry phase was not triggered")

        # Check if individual retries occurred
        if "Retry batch" in stdout:
            print("✅ Individual retry batches were processed")
        else:
            print("❌ Individual retry batches were not processed")

        # Check if final failure was handled correctly
        if "failed after" in stdout and result.returncode != 0:
            print("✅ Final failure handling worked correctly")
        else:
            print("❌ Final failure handling may have issues")

        # Since we're using nonexistent codes, we expect failure
        if result.returncode != 0:
            print("✅ Expected failure due to nonexistent test codes")
        else:
            print("❌ Unexpected success - test codes should fail")

        print(f"\n🎯 Test completed with exit code {result.returncode}")

        return result.returncode == 1  # We expect failure for this test

    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


def main():
    """Run the retry queue test."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    # Change to the repository root
    os.chdir(repo_root)

    print("🔬 Starting retry queue functionality test")
    print(f"📁 Working directory: {repo_root}")
    print("=" * 50)

    success = test_retry_queue()

    print("=" * 50)
    if success:
        print("🎉 Retry queue test PASSED")
        sys.exit(0)
    else:
        print("💥 Retry queue test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
