#!/usr/bin/env python3
"""
Test script to validate retry queue functionality using mock_main.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_successful_batch():
    """Test with items that should succeed."""
    print("🧪 Test 1: Successful batch processing")

    test_job_input = [
        {"platform": "instagram", "code": "success_1"},
        {"platform": "instagram", "code": "success_2"},
    ]

    env = os.environ.copy()
    env.update(
        {
            "JOB_INPUT": json.dumps(test_job_input),
            "MAX_RETRIES": "2",
            "BATCH_SIZE": "2",
            "RETRY_BATCH_SIZE": "1",
        }
    )

    result = subprocess.run(
        [sys.executable, "test/mock_main.py"], env=env, capture_output=True, text=True, timeout=30
    )

    success = result.returncode == 0 and "All items processed successfully" in result.stdout
    print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
    if not success:
        print(f"   Exit code: {result.returncode}")
        print(f"   STDOUT: {result.stdout[:200]}...")
    return success


def test_retry_queue():
    """Test retry queue functionality with failing items."""
    print("🧪 Test 2: Retry queue functionality")

    test_job_input = [
        {"platform": "instagram", "code": "nonexistent_code_1"},
        {"platform": "instagram", "code": "nonexistent_code_2"},
    ]

    env = os.environ.copy()
    env.update(
        {
            "JOB_INPUT": json.dumps(test_job_input),
            "MAX_RETRIES": "2",
            "BATCH_SIZE": "2",
            "RETRY_BATCH_SIZE": "1",
        }
    )

    result = subprocess.run(
        [sys.executable, "test/mock_main.py"], env=env, capture_output=True, text=True, timeout=30
    )

    stdout = result.stdout

    # Check for expected behavior
    phase_2_triggered = "Phase 2: Retrying" in stdout
    retry_batches = "Retry batch" in stdout
    final_failure = "failed after" in stdout and result.returncode == 1

    success = phase_2_triggered and retry_batches and final_failure
    print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
    print(f"   Phase 2 triggered: {'✅' if phase_2_triggered else '❌'}")
    print(f"   Retry batches processed: {'✅' if retry_batches else '❌'}")
    print(f"   Final failure handled: {'✅' if final_failure else '❌'}")

    if not success:
        print(f"   Exit code: {result.returncode}")
        print(f"   STDOUT: {stdout[:500]}...")

    return success


def test_mixed_success_failure():
    """Test with mixed success and failure items."""
    print("🧪 Test 3: Mixed success and failure")

    test_job_input = [
        {"platform": "instagram", "code": "success_1"},
        {"platform": "instagram", "code": "nonexistent_fail"},
    ]

    env = os.environ.copy()
    env.update(
        {
            "JOB_INPUT": json.dumps(test_job_input),
            "MAX_RETRIES": "1",
            "BATCH_SIZE": "1",  # Process individually to test granular failure
            "RETRY_BATCH_SIZE": "1",
        }
    )

    result = subprocess.run(
        [sys.executable, "test/mock_main.py"], env=env, capture_output=True, text=True, timeout=30
    )

    stdout = result.stdout

    # Should have 1 successful batch and 1 failed batch that gets retried
    success_batch = "Batch 1 completed successfully" in stdout
    failed_batch = "Batch 2 failed" in stdout
    retry_phase = "Phase 2: Retrying 1 failed items" in stdout

    success = success_batch and failed_batch and retry_phase
    print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
    print(f"   Success batch detected: {'✅' if success_batch else '❌'}")
    print(f"   Failed batch detected: {'✅' if failed_batch else '❌'}")
    print(f"   Retry phase for 1 item: {'✅' if retry_phase else '❌'}")

    if not success:
        print(f"   Exit code: {result.returncode}")
        print(f"   STDOUT: {stdout[:500]}...")

    return success


def main():
    """Run all retry queue tests."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    # Change to the repository root
    os.chdir(repo_root)

    print("🔬 Starting mock retry queue functionality tests")
    print(f"📁 Working directory: {repo_root}")
    print("=" * 60)

    tests = [test_successful_batch, test_retry_queue, test_mixed_success_failure]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"   ❌ FAIL - Exception: {e}")
            print()

    print("=" * 60)
    print(f"🎯 Test Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All retry queue tests PASSED!")
        sys.exit(0)
    else:
        print("💥 Some retry queue tests FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
