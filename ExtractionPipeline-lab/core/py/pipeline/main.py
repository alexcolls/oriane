#!/usr/bin/env python3
"""
Main orchestrator for video extraction pipeline with retry queue
──────────────────────────────────────────────────────────────────
This script handles batch processing with graceful error capture and retry logic:
• Runs entrypoint.py with batches of items
• Parses exit status; on non-zero, adds failed IDs to local retry_set
• After full pass, retries failed items individually (size=1) up to N times
• Failures inside entrypoint are already captured in extraction_errors via FK
• Resource throttling: Sequential batch processing with sleep between batches
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Set

from config.logging_config import configure_logging

# Configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BATCH_SIZE = 10
DEFAULT_RETRY_BATCH_SIZE = 1
DEFAULT_SLEEP_SECONDS = 2.0

log = configure_logging()


def run_entrypoint_batch(items: List[Dict[str, Any]]) -> int:
    """
    Run entrypoint.py with a batch of items.
    Returns the exit status code.
    """
    job_input = json.dumps(items)
    env = os.environ.copy()
    env["JOB_INPUT"] = job_input

    log.info(f"[batch] Running entrypoint.py with {len(items)} items")

    try:
        result = subprocess.run(
            [sys.executable, "entrypoint.py"],
            env=env,
            capture_output=False,  # Let output go to stdout/stderr
            timeout=3600,  # 1 hour timeout per batch
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        log.error("[batch] Entrypoint execution timed out after 1 hour")
        return 124  # Standard timeout exit code
    except Exception as e:
        log.error(f"[batch] Failed to execute entrypoint: {e}")
        return 1


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
    parser = argparse.ArgumentParser(description="Video extraction pipeline orchestrator")
    parser.add_argument(
        "--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Number of items per batch"
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help="Seconds to sleep between batches",
    )
    args = parser.parse_args()

    batch_size = args.batch_size
    sleep_between_batches = args.sleep
    max_retries = int(os.getenv("MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
    retry_batch_size = int(os.getenv("RETRY_BATCH_SIZE", str(DEFAULT_RETRY_BATCH_SIZE)))

    log.info(f"[main] Starting pipeline orchestrator")
    log.info(
        f"[main] Config: batch_size={batch_size}, sleep_between_batches={sleep_between_batches}, max_retries={max_retries}"
    )

    # Get job input
    raw_job_input = os.getenv("JOB_INPUT")
    if not raw_job_input:
        log.error("[main] JOB_INPUT environment variable is required")
        sys.exit(1)

    try:
        items: List[Dict[str, Any]] = json.loads(raw_job_input)
    except json.JSONDecodeError as e:
        log.error(f"[main] Invalid JSON in JOB_INPUT: {e}")
        sys.exit(1)

    if not items:
        log.warning("[main] No items to process")
        return

    log.info(f"[main] Processing {len(items)} total items")

    # Split into initial batches
    batches = split_into_batches(items, batch_size)
    log.info(f"[main] Split into {len(batches)} initial batches")

    # Track failed items for retry
    retry_set: Set[str] = set()

    # ─── Phase 1: Process initial batches ───
    log.info("[main] ═══ Phase 1: Initial batch processing ═══")

    for batch_idx, batch in enumerate(batches):
        batch_codes = extract_item_codes(batch)
        log.info(
            f"[main] Processing batch {batch_idx + 1}/{len(batches)} (codes: {', '.join(batch_codes)})"
        )

        exit_status = run_entrypoint_batch(batch)

        if exit_status == 0:
            log.info(f"[main] ✅ Batch {batch_idx + 1} completed successfully")
        else:
            log.warning(f"[main] ❌ Batch {batch_idx + 1} failed with exit status {exit_status}")
            # Add all codes from failed batch to retry set
            for item in batch:
                code = item.get("code")
                if code:
                    retry_set.add(code)
            log.info(f"[main] Added {len(batch)} items to retry queue")

        log.info(f"[main] Sleeping for {sleep_between_batches} seconds before next batch...")
        time.sleep(sleep_between_batches)

    # ─── Phase 2: Retry failed items individually ───
    if retry_set:
        log.info(f"[main] ═══ Phase 2: Retrying {len(retry_set)} failed items ═══")

        # Create mapping from code to original item
        code_to_item = {item.get("code"): item for item in items if item.get("code")}

        retry_attempt = 1

        while retry_set and retry_attempt <= max_retries:
            log.info(
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
                log.info(
                    f"[main] Retry batch {retry_batch_idx + 1}/{len(retry_batches)} (codes: {', '.join(retry_codes)})"
                )

                exit_status = run_entrypoint_batch(retry_batch)

                if exit_status == 0:
                    log.info(f"[main] ✅ Retry batch succeeded - removing from retry set")
                    # Remove successful items from retry set
                    for item in retry_batch:
                        code = item.get("code")
                        if code in retry_set:
                            retry_set.discard(code)
                else:
                    log.warning(f"[main] ❌ Retry batch failed with exit status {exit_status}")
                    # Keep failed items for next retry attempt
                    for item in retry_batch:
                        code = item.get("code")
                        if code:
                            current_retry_set.add(code)

            # Update retry set for next attempt
            retry_set = current_retry_set
            retry_attempt += 1

            if retry_set and retry_attempt <= max_retries:
                log.info(f"[main] {len(retry_set)} items still failing, will retry...")
                time.sleep(5)  # Brief pause between retry attempts

    # ─── Final summary ───
    if retry_set:
        log.error(f"[main] ❌ {len(retry_set)} items failed after {max_retries} retry attempts")
        log.error(f"[main] Permanently failed codes: {', '.join(sorted(retry_set))}")
        log.error(f"[main] Check extraction_errors table for detailed error information")
        sys.exit(1)
    else:
        log.info("[main] ✅ All items processed successfully!")
        log.info("[main] Pipeline orchestration completed")


if __name__ == "__main__":
    main()
