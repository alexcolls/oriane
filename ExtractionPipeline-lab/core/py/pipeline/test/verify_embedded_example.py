#!/usr/bin/env python3
"""
Example usage of embedded status verification.

This script demonstrates how to use the verify_embedded module
to check and mark video codes as embedded after pipeline processing.
"""

import os
import sys
from pathlib import Path

# Add the pipeline source directory to Python path
pipeline_dir = Path(__file__).parent.parent
sys.path.insert(0, str(pipeline_dir))

from config.env_config import settings
from config.logging_config import configure_logging
from src.verify_embedded import mark_embedded_codes, verify_batch_embedded

log = configure_logging()


def example_batch_verification():
    """Example of verifying a batch of video codes."""

    # Example video codes that might be processed by the pipeline
    video_codes = [
        "C1234567890",  # Instagram shortcode format
        "C9876543210",
        "C1122334455",
    ]

    log.info(f"Example: Verifying {len(video_codes)} video codes...")

    # Step 1: Check which codes have vectors in Qdrant
    verification_results = verify_batch_embedded(video_codes)

    log.info("Verification results:")
    for code, has_vectors in verification_results.items():
        status = "✅ HAS VECTORS" if has_vectors else "❌ NO VECTORS"
        log.info(f"  {code}: {status}")

    return verification_results


def example_marking_embedded():
    """Example of marking codes as embedded in the database."""

    # Example video codes (typically from successful pipeline runs)
    processed_codes = [
        "C1234567890",
        "C9876543210",
        "C1122334455",
    ]

    log.info(f"Example: Marking embedded status for {len(processed_codes)} codes...")

    # This function will:
    # 1. Check which codes have vectors in Qdrant
    # 2. Look up database IDs for codes with vectors
    # 3. Mark those IDs as embedded in the database
    mark_embedded_codes(processed_codes)

    log.info("Marking process complete!")


def example_pipeline_integration():
    """Example of how this integrates with pipeline processing."""

    log.info("Example: Pipeline integration flow...")

    # Simulate a batch of items from pipeline input
    batch_items = [
        {"platform": "instagram", "code": "C1234567890"},
        {"platform": "instagram", "code": "C9876543210"},
        {"platform": "instagram", "code": "C1122334455"},
    ]

    # Step 1-5: Pipeline processing (simulated)
    successfully_processed_codes = []

    for item in batch_items:
        code = item["code"]

        # Simulate pipeline processing
        log.info(f"Processing {code}...")

        try:
            # In real pipeline, this would be:
            # - Download video
            # - Extract frames
            # - Generate embeddings
            # - Store in Qdrant
            # - Upload frames to S3

            log.info(f"✅ {code} processed successfully")
            successfully_processed_codes.append(code)

        except Exception as e:
            log.error(f"❌ {code} failed: {e}")

    # Step 6: Embedded status verification
    if successfully_processed_codes:
        log.info(f"🔍 Verifying embedded status for {len(successfully_processed_codes)} codes")
        mark_embedded_codes(successfully_processed_codes)
        log.info("✅ Embedded status verification complete")
    else:
        log.warning("No codes to verify")


def main():
    """Run examples."""

    log.info("🚀 Starting embedded verification examples...")
    log.info(f"Using Qdrant URL: {settings.qdrant_url}")
    log.info(f"Using collection: {settings.collection}")

    examples = [
        ("Batch Verification", example_batch_verification),
        ("Marking Embedded", example_marking_embedded),
        ("Pipeline Integration", example_pipeline_integration),
    ]

    for example_name, example_func in examples:
        log.info(f"\n{'='*60}")
        log.info(f"Running: {example_name}")
        log.info(f"{'='*60}")

        try:
            example_func()
            log.info(f"✅ {example_name} completed successfully")
        except Exception as e:
            log.error(f"❌ {example_name} failed: {e}")
            import traceback

            traceback.print_exc()

    log.info("\n🎉 All examples completed!")


if __name__ == "__main__":
    # Check environment setup
    if not settings.qdrant_url:
        print("❌ QDRANT_URL environment variable is required")
        print("Please set up your .env file with Qdrant configuration")
        sys.exit(1)

    main()
