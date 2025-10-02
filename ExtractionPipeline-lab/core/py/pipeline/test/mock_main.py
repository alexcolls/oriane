#!/usr/bin/env python3
"""
Mock version of main.py for testing retry queue functionality without dependencies
"""

import json
import os
import sys
import time
from typing import Any, Dict, List, Set

# Configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BATCH_SIZE = 10
DEFAULT_RETRY_BATCH_SIZE = 1


def log_info(msg: str):
    print(f"INFO: {msg}")


def log_warning(msg: str):
    print(f"WARNING: {msg}")


def log_error(msg: str):
    print(f"ERROR: {msg}")


def run_entrypoint_batch(items: List[Dict[str, Any]]) -> int:
    """
    Mock version that simulates entrypoint.py behavior.
    Returns non-zero for items with 'fail' in the code.
    """
    log_info(f"[batch] Running entrypoint.py with {len(items)} items")

    # Simulate processing time
    time.sleep(0.1)

    # Check if any item should fail (for testing)
    for item in items:
        code = item.get("code", "")
        if "fail" in code or "nonexistent" in code:
            log_error(f"[batch] Simulated failure for {code}")
            return 1

    log_info("[batch] All items processed successfully")
    return 0


def extract_item_codes(items: List[Dict[str, Any]]) -> List[str]:
    """Extract codes from list of items for logging/tracking."""
    return [item.get("code", "unknown") for item in items]


def split_into_batches(items: List[Dict[str, Any]], batch_size: int) -> List[List[Dict[str, Any]]]:
    """Split items into batches of specified size."""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i : i + batch_size])
    return batches


def main():
    """Main orchestrator with retry queue logic."""

    # Parse command line arguments
    max_retries = int(os.getenv("MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
    batch_size = int(os.getenv("BATCH_SIZE", str(DEFAULT_BATCH_SIZE)))
    retry_batch_size = int(os.getenv("RETRY_BATCH_SIZE", str(DEFAULT_RETRY_BATCH_SIZE)))

    log_info(f"[main] Starting pipeline orchestrator")
    log_info(
        f"[main] Config: max_retries={max_retries}, batch_size={batch_size}, retry_batch_size={retry_batch_size}"
    )

    # Get job input
    raw_job_input = os.getenv("JOB_INPUT")
    if not raw_job_input:
        log_error("[main] JOB_INPUT environment variable is required")
        sys.exit(1)

    try:
        items: List[Dict[str, Any]] = json.loads(raw_job_input)
    except json.JSONDecodeError as e:
        log_error(f"[main] Invalid JSON in JOB_INPUT: {e}")
        sys.exit(1)

    if not items:
        log_warning("[main] No items to process")
        return

    log_info(f"[main] Processing {len(items)} total items")

    # Split into initial batches
    batches = split_into_batches(items, batch_size)
    log_info(f"[main] Split into {len(batches)} initial batches")

    # Track failed items for retry
    retry_set: Set[str] = set()

    # ─── Phase 1: Process initial batches ───
    log_info("[main] ═══ Phase 1: Initial batch processing ═══")

    for batch_idx, batch in enumerate(batches):
        batch_codes = extract_item_codes(batch)
        log_info(
            f"[main] Processing batch {batch_idx + 1}/{len(batches)} (codes: {', '.join(batch_codes)})"
        )

        exit_status = run_entrypoint_batch(batch)

        if exit_status == 0:
            log_info(f"[main] ✅ Batch {batch_idx + 1} completed successfully")
        else:
            log_warning(f"[main] ❌ Batch {batch_idx + 1} failed with exit status {exit_status}")
            # Add all codes from failed batch to retry set
            for item in batch:
                code = item.get("code")
                if code:
                    retry_set.add(code)
            log_info(f"[main] Added {len(batch)} items to retry queue")

    # ─── Phase 2: Retry failed items individually ───
    if retry_set:
        log_info(f"[main] ═══ Phase 2: Retrying {len(retry_set)} failed items ═══")

        # Create mapping from code to original item
        code_to_item = {item.get("code"): item for item in items if item.get("code")}

        retry_attempt = 1

        while retry_set and retry_attempt <= max_retries:
            log_info(
                f"[main] --- Retry attempt {retry_attempt}/{max_retries} ({len(retry_set)} items) ---"
            )

            # Convert retry set to list of items for this attempt
            retry_items = []
            for code in list(retry_set):  # Copy set to list to avoid modification during iteration
                if code in code_to_item:
                    retry_items.append(code_to_item[code])

            # Split retry items into small batches (typically size=1)
            retry_batches = split_into_batches(retry_items, retry_batch_size)

            current_retry_set: Set[str] = set()

            for retry_batch_idx, retry_batch in enumerate(retry_batches):
                retry_codes = extract_item_codes(retry_batch)
                log_info(
                    f"[main] Retry batch {retry_batch_idx + 1}/{len(retry_batches)} (codes: {', '.join(retry_codes)})"
                )

                exit_status = run_entrypoint_batch(retry_batch)

                if exit_status == 0:
                    log_info(f"[main] ✅ Retry batch succeeded - removing from retry set")
                    # Remove successful items from retry set
                    for item in retry_batch:
                        code = item.get("code")
                        if code in retry_set:
                            retry_set.discard(code)
                else:
                    log_warning(f"[main] ❌ Retry batch failed with exit status {exit_status}")
                    # Keep failed items for next retry attempt
                    for item in retry_batch:
                        code = item.get("code")
                        if code:
                            current_retry_set.add(code)

            # Update retry set for next attempt
            retry_set = current_retry_set
            retry_attempt += 1

            if retry_set and retry_attempt <= max_retries:
                log_info(f"[main] {len(retry_set)} items still failing, will retry...")
                time.sleep(0.1)  # Brief pause between retry attempts

    # ─── Final summary ───
    if retry_set:
        log_error(f"[main] ❌ {len(retry_set)} items failed after {max_retries} retry attempts")
        log_error(f"[main] Permanently failed codes: {', '.join(sorted(retry_set))}")
        log_error(f"[main] Check extraction_errors table for detailed error information")
        sys.exit(1)
    else:
        log_info("[main] ✅ All items processed successfully!")
        log_info("[main] Pipeline orchestration completed")


if __name__ == "__main__":
    main()
