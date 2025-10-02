#!/usr/bin/env python3
"""
Fix Qdrant Paths Migration Script
=================================
This script migrates Qdrant points with paths starting with "oriane-frames/"
to use "instagram/" prefix instead, and updates the payload structure accordingly.

Algorithm:
1. Connect via existing store_embeds._client()
2. Scroll all points where payload.path LIKE "oriane-frames/%"
3. For each point build a new payload:
   - path: replace the leading string with "instagram/"
   - uuid: generate new UUID
   - created_at: use current UTC time
   - Rename frame_idx → frame_number, timestamp_s → frame_second if present
4. Upsert the corrected points in chunks (same size as settings.batch_size)
5. Log summary of fixed items
"""

from __future__ import annotations

import datetime
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

# Add the core pipeline to Python path for imports
script_dir = Path(__file__).parent
core_path = script_dir.parent.parent.parent / "core" / "py" / "pipeline" / "src"
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

try:
    from config.env_config import settings
    from config.logging_config import configure_logging
    import store_embeds
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Make sure you're running this script from the correct directory")
    sys.exit(1)

# Configure logging
log = configure_logging()


def fix_qdrant_paths() -> Dict[str, Any]:
    """
    Main function to fix Qdrant paths from oriane-frames/% to instagram/%.

    Returns:
        Dict with summary statistics
    """
    log.info("🔧 Starting Qdrant paths migration: oriane-frames/* → instagram/*")

    # Connect to Qdrant via existing client
    client = store_embeds._client()

    # Stats tracking
    stats = {
        "total_points_found": 0,
        "points_processed": 0,
        "points_fixed": 0,
        "batch_count": 0,
        "errors": []
    }

    start_time = time.perf_counter()

    try:
        # Scroll through all points to find ones with oriane-frames/ paths
        log.info(f"🔍 Searching for points with 'oriane-frames/*' paths in collection '{settings.collection}'")

        points_to_fix = []
        offset = None
        batch_size = min(settings.batch_size * 10, 1000)  # Use larger batches for scrolling

        while True:
            # Scroll through points
            scroll_result = client.scroll(
                collection_name=settings.collection,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )

            points, next_offset = scroll_result

            if not points:
                break

            # Filter points that need fixing
            for point in points:
                if (point.payload and
                    "path" in point.payload and
                    isinstance(point.payload["path"], str) and
                    point.payload["path"].startswith("oriane-frames/")):

                    points_to_fix.append(point)
                    stats["total_points_found"] += 1

            log.info(f"📊 Scanned {len(points)} points, found {len([p for p in points if p.payload and 'path' in p.payload and isinstance(p.payload['path'], str) and p.payload['path'].startswith('oriane-frames/')])} with oriane-frames/* paths")

            offset = next_offset
            if offset is None:
                break

        log.info(f"🎯 Found {stats['total_points_found']} points that need path fixing")

        if stats["total_points_found"] == 0:
            log.info("✅ No points found with oriane-frames/* paths. Migration not needed.")
            return stats

        # Process points in chunks
        log.info(f"🔄 Processing {len(points_to_fix)} points in batches of {settings.batch_size}")

        for i in range(0, len(points_to_fix), settings.batch_size):
            chunk = points_to_fix[i:i + settings.batch_size]

            try:
                fixed_points = []

                for point in chunk:
                    fixed_point = _fix_point_payload(point)
                    if fixed_point:
                        fixed_points.append(fixed_point)
                        stats["points_fixed"] += 1

                    stats["points_processed"] += 1

                # Upsert the fixed points
                if fixed_points:
                    client.upsert(
                        collection_name=settings.collection,
                        points=fixed_points,
                        wait=True
                    )

                    stats["batch_count"] += 1
                    log.info(f"✅ Batch {stats['batch_count']}: Fixed {len(fixed_points)}/{len(chunk)} points")

            except Exception as e:
                error_msg = f"❌ Error processing batch {stats['batch_count'] + 1}: {e}"
                log.error(error_msg)
                stats["errors"].append(error_msg)
                continue

        # Final summary
        elapsed_time = time.perf_counter() - start_time
        log.info(f"🎉 Migration completed in {elapsed_time:.2f}s")
        log.info(f"📊 Summary:")
        log.info(f"   • Total points found: {stats['total_points_found']}")
        log.info(f"   • Points processed: {stats['points_processed']}")
        log.info(f"   • Points fixed: {stats['points_fixed']}")
        log.info(f"   • Batches processed: {stats['batch_count']}")
        log.info(f"   • Errors: {len(stats['errors'])}")

        if stats["errors"]:
            log.warning("⚠️  Errors encountered:")
            for error in stats["errors"]:
                log.warning(f"   {error}")

        return stats

    except Exception as e:
        error_msg = f"❌ Fatal error during migration: {e}"
        log.error(error_msg)
        stats["errors"].append(error_msg)
        raise


def _fix_point_payload(point) -> Any:
    """
    Fix a single point's payload according to the migration rules.

    Args:
        point: Qdrant point object

    Returns:
        Fixed PointStruct or None if fixing failed
    """
    try:
        from qdrant_client.models import PointStruct

        # Create new payload with fixes
        new_payload = point.payload.copy()

        # 1. Fix path: oriane-frames/* → instagram/*
        if "path" in new_payload and isinstance(new_payload["path"], str):
            old_path = new_payload["path"]
            if old_path.startswith("oriane-frames/"):
                new_payload["path"] = old_path.replace("oriane-frames/", "instagram/", 1)

        # 2. Generate new UUID
        new_payload["uuid"] = str(uuid.uuid4())

        # 3. Set current UTC time
        new_payload["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 4. Rename fields if present
        # frame_idx → frame_number
        if "frame_idx" in new_payload:
            new_payload["frame_number"] = new_payload.pop("frame_idx")

        # timestamp_s → frame_second
        if "timestamp_s" in new_payload:
            new_payload["frame_second"] = new_payload.pop("timestamp_s")

        # Create new point with same ID and vector, but updated payload
        return PointStruct(
            id=point.id,
            vector=point.vector,
            payload=new_payload
        )

    except Exception as e:
        log.error(f"❌ Failed to fix point {point.id}: {e}")
        return None


if __name__ == "__main__":
    """
    Run the migration script directly.
    """
    try:
        # Confirmation prompt
        print("\n⚠️  Qdrant Path Migration: oriane-frames/* → instagram/*")
        print("   This will update point payloads in the Qdrant collection.")
        print(f"   Collection: {settings.collection}")
        print(f"   Batch size: {settings.batch_size}")
        print()

        response = input("   Proceed with migration? [y/N] ").strip().lower()
        if response != "y":
            print("❌ Migration cancelled.")
            sys.exit(0)

        print()

        # Run the migration
        stats = fix_qdrant_paths()

        # Exit with appropriate code
        if stats["errors"]:
            print(f"\n⚠️  Migration completed with {len(stats['errors'])} errors.")
            sys.exit(1)
        else:
            print(f"\n✅ Migration completed successfully!")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
