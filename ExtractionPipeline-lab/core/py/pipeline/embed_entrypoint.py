#!/usr/bin/env python3
"""
Embedding entrypoint for frame processing
─────────────────────────────────────────

This script handles the embedding processing phase for videos that have already
been through the extraction phase. It:

1. Takes a video code as input
2. Finds the extracted frames for that video
3. Processes them through the embedding pipeline (CLIP)
4. Stores the embeddings in Qdrant

This is designed to be called from the main extraction pipeline when
is_extracted=True but is_embedded=False.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from uuid import uuid5, NAMESPACE_URL

from config.env_config import settings
from config.logging_config import configure_logging
from src import infer_embeds, store_embeds

log = configure_logging()


def process_embedding_for_code(code: str) -> bool:
    """
    Process frame embeddings for a single video code.

    Args:
        code: The video code (e.g., Instagram shortcode)

    Returns:
        True if successful, False otherwise
    """
    try:
        log.info(f"[embed] Processing embeddings for code: {code}")

        # Find the frames directory for this code
        frames_dir = settings.frames_dir / code
        if not frames_dir.exists():
            log.error(f"[embed] Frames directory not found: {frames_dir}")
            return False

        # Find all frame files in the directory
        frame_files = list(frames_dir.glob("*.png"))
        if not frame_files:
            log.warning(f"[embed] No PNG frames found in {frames_dir}")
            return False

        # Sort frames by filename (they should be numbered)
        frame_files.sort()
        log.info(f"[embed] Found {len(frame_files)} frames to process")

        # Generate embeddings
        t0 = time.perf_counter()
        vectors = infer_embeds.encode_image_batch(frame_files)
        embed_time = time.perf_counter() - t0

        if not vectors:
            log.error(f"[embed] Failed to generate embeddings for {code}")
            return False

        log.info(f"[embed] Generated {len(vectors)} embeddings in {embed_time:.1f}s")

        # Prepare Qdrant points
        points = []
        platform = "instagram"  # Constant for now

        for i, (frame_path, vector) in enumerate(zip(frame_files, vectors)):
            # Extract frame info from filename (format: {idx}_{timestamp}.png)
            frame_name = frame_path.name
            parts = frame_name.replace(".png", "").split("_")
            if len(parts) >= 2:
                frame_idx = parts[0]
                timestamp_s = float(parts[1])
            else:
                # Fallback if naming convention is different
                frame_idx = str(i)
                timestamp_s = float(i)

            # Convert to new payload structure
            frame_number = int(frame_idx)
            frame_second = timestamp_s
            s3_path = f"{platform}/{code}/{frame_path.name}"

            payload = {
                "uuid": str(uuid5(NAMESPACE_URL, f"{code}_{frame_number}_{frame_second}")),
                "created_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
                "video_code": code,
                "frame_number": frame_number,
                "frame_second": frame_second,
                "path": s3_path,
            }

            point_id = f"{code}_{frame_idx}"

            points.append(
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": payload,
                }
            )

        # Store in Qdrant
        t0 = time.perf_counter()
        store_embeds.upsert_embeddings(points)
        store_time = time.perf_counter() - t0

        log.info(f"[embed] Stored {len(points)} vectors in Qdrant in {store_time:.1f}s")
        log.info(f"[embed] ✅ Successfully processed embeddings for {code}")
        return True

    except Exception as e:
        log.error(f"[embed] ❌ Failed to process embeddings for {code}: {e}")
        return False


def main():
    """Main entrypoint for embedding processing."""
    parser = argparse.ArgumentParser(description="Process frame embeddings for video codes")
    parser.add_argument("codes", nargs="+", help="Video codes to process for embeddings")
    parser.add_argument(
        "--batch-size", type=int, default=None, help="Override batch size for embedding processing"
    )

    args = parser.parse_args()

    log.info(f"[embed] Starting embedding processing for {len(args.codes)} codes")

    # Override batch size if provided
    if args.batch_size:
        import os

        os.environ["VP_BATCH_SIZE"] = str(args.batch_size)
        log.info(f"[embed] Using batch size: {args.batch_size}")

    successful = 0
    failed = 0

    for code in args.codes:
        if process_embedding_for_code(code):
            successful += 1
        else:
            failed += 1

    log.info(f"[embed] Processing complete: {successful} successful, {failed} failed")

    # Exit with error code if any failed
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
