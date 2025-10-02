#!/usr/bin/env python3
"""
Payload Structure Migration Script
=================================

This script migrates existing Qdrant points from the old payload structure
to the new structure:

OLD STRUCTURE:
- path: "oriane-frames/{code}/{frame_file}"
- other fields directly in payload

NEW STRUCTURE:
- uuid: str (UUID5 generated from code_framenumber_framesecond)
- created_at: str (ISO timestamp)
- video_code: str
- frame_number: int
- frame_second: float
- path: "instagram/{code}/{frame_file}" (platform prefix instead of oriane-frames)

The script:
1. Scans all points in the collection
2. Migrates payloads that start with "oriane-frames/"
3. Adds missing uuid and created_at fields
4. Updates path format to use platform prefix
"""

import argparse
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from uuid import uuid5, NAMESPACE_URL

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse


class PayloadMigrator:
    """Handles the migration of payload structures in Qdrant."""

    def __init__(self, qdrant_url: str, api_key: str, collection_name: str):
        self.client = QdrantClient(url=qdrant_url, api_key=api_key)
        self.collection_name = collection_name
        self.dry_run = False

    def set_dry_run(self, dry_run: bool):
        """Enable/disable dry run mode."""
        self.dry_run = dry_run

    def scan_for_bad_points(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Scan collection for points with old payload structure.

        Returns:
            List of points that need migration
        """
        print(f"🔍 Scanning for points with old payload structure...")

        bad_points = []
        offset = 0

        while True:
            try:
                # Scroll through points in batches
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=limit,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )

                points = response[0]  # First element is points list

                if not points:
                    break

                for point in points:
                    payload = point.payload or {}

                    # Check for old structure indicators
                    needs_migration = False

                    # Check 1: path starts with "oriane-frames/"
                    if payload.get("path", "").startswith("oriane-frames/"):
                        needs_migration = True

                    # Check 2: missing uuid field
                    if "uuid" not in payload:
                        needs_migration = True

                    # Check 3: missing created_at field
                    if "created_at" not in payload:
                        needs_migration = True

                    if needs_migration:
                        bad_points.append({
                            "id": point.id,
                            "payload": payload
                        })

                offset += len(points)

                if len(points) < limit:
                    break

            except Exception as e:
                print(f"❌ Error scanning points at offset {offset}: {e}")
                break

        print(f"📊 Found {len(bad_points)} points needing migration")
        return bad_points

    def migrate_point_payload(self, point_id: str, old_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate a single point's payload to new structure.

        Args:
            point_id: The point ID
            old_payload: Current payload

        Returns:
            New payload structure
        """
        new_payload = old_payload.copy()

        # Extract video code from various sources
        video_code = old_payload.get("video_code")
        if not video_code:
            # Try to extract from path
            path = old_payload.get("path", "")
            if "/" in path:
                parts = path.split("/")
                if len(parts) >= 2:
                    video_code = parts[1]  # oriane-frames/{code}/... or instagram/{code}/...

        if not video_code:
            # Try to extract from point ID
            if "_" in str(point_id):
                video_code = str(point_id).split("_")[0]

        # Extract frame info
        frame_number = old_payload.get("frame_number", 0)
        frame_second = old_payload.get("frame_second", 0.0)

        # Generate UUID if missing
        if "uuid" not in new_payload:
            if video_code:
                new_payload["uuid"] = str(uuid5(NAMESPACE_URL, f"{video_code}_{frame_number}_{frame_second}"))
            else:
                new_payload["uuid"] = str(uuid5(NAMESPACE_URL, f"unknown_{point_id}_{frame_number}_{frame_second}"))

        # Add created_at if missing
        if "created_at" not in new_payload:
            new_payload["created_at"] = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")

        # Set video_code if missing
        if "video_code" not in new_payload and video_code:
            new_payload["video_code"] = video_code

        # Fix path format if it starts with "oriane-frames/"
        if new_payload.get("path", "").startswith("oriane-frames/"):
            old_path = new_payload["path"]
            # Convert "oriane-frames/{code}/{file}" to "instagram/{code}/{file}"
            path_parts = old_path.split("/", 2)
            if len(path_parts) >= 3:
                new_payload["path"] = f"instagram/{path_parts[1]}/{path_parts[2]}"
            else:
                # Fallback for malformed paths
                new_payload["path"] = old_path.replace("oriane-frames/", "instagram/")

        return new_payload

    def migrate_batch(self, points: List[Dict[str, Any]]) -> int:
        """
        Migrate a batch of points.

        Args:
            points: List of points to migrate

        Returns:
            Number of successfully migrated points
        """
        if not points:
            return 0

        print(f"🔄 Migrating batch of {len(points)} points...")

        # Prepare update operations
        operations = []

        for point_data in points:
            point_id = point_data["id"]
            old_payload = point_data["payload"]

            new_payload = self.migrate_point_payload(point_id, old_payload)

            if self.dry_run:
                print(f"   [DRY RUN] Would update point {point_id}")
                print(f"     OLD: {json.dumps(old_payload, indent=2)}")
                print(f"     NEW: {json.dumps(new_payload, indent=2)}")
                print()
            else:
                # Create update operation
                operations.append(
                    models.UpdateOperation(
                        upsert=models.PointStruct(
                            id=point_id,
                            payload=new_payload,
                            vector={}  # Keep existing vector
                        )
                    )
                )

        if self.dry_run:
            return len(points)  # All would be "successful" in dry run

        # Execute batch update
        try:
            self.client.update_collection(
                collection_name=self.collection_name,
                update_operations=operations
            )
            return len(points)
        except Exception as e:
            print(f"❌ Error updating batch: {e}")
            return 0

    def run_migration(self, batch_size: int = 100):
        """
        Run the complete migration process.

        Args:
            batch_size: Number of points to process per batch
        """
        print(f"🚀 Starting payload migration for collection '{self.collection_name}'")
        print(f"🔧 Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        print(f"📦 Batch size: {batch_size}")

        # Get collection info
        try:
            info = self.client.get_collection(self.collection_name)
            print(f"📊 Collection has {info.points_count} total points")
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return

        # Find points needing migration
        bad_points = self.scan_for_bad_points()

        if not bad_points:
            print("✅ No points need migration!")
            return

        print(f"📋 Processing {len(bad_points)} points in batches of {batch_size}")

        total_migrated = 0

        # Process in batches
        for i in range(0, len(bad_points), batch_size):
            batch = bad_points[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(bad_points) + batch_size - 1) // batch_size

            print(f"📦 Processing batch {batch_num}/{total_batches}")

            migrated = self.migrate_batch(batch)
            total_migrated += migrated

            # Small delay between batches
            if not self.dry_run:
                time.sleep(0.5)

        print(f"\n✅ Migration complete!")
        print(f"   📊 Total points processed: {len(bad_points)}")
        print(f"   ✅ Successfully migrated: {total_migrated}")
        print(f"   ❌ Failed: {len(bad_points) - total_migrated}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate Qdrant payload structures")
    parser.add_argument("--qdrant-url", required=True, help="Qdrant server URL")
    parser.add_argument("--api-key", required=True, help="Qdrant API key")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")

    args = parser.parse_args()

    # Create migrator
    migrator = PayloadMigrator(
        qdrant_url=args.qdrant_url,
        api_key=args.api_key,
        collection_name=args.collection
    )

    migrator.set_dry_run(args.dry_run)

    # Run migration
    migrator.run_migration(batch_size=args.batch_size)


if __name__ == "__main__":
    main()
