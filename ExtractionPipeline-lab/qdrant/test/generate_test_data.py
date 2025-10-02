#!/usr/bin/env python3
"""
Test Data Generator for Qdrant Migration Testing
================================================

This script creates sample "bad" points in a Qdrant collection for testing
the migration script. It generates points with the old payload structure
that need to be migrated to the new format.
"""

import argparse
import json
import random
from typing import List, Dict, Any

import numpy as np
from qdrant_client import QdrantClient, models


class TestDataGenerator:
    """Generates test data for migration testing."""

    def __init__(self, qdrant_url: str, api_key: str, collection_name: str):
        self.client = QdrantClient(url=qdrant_url, api_key=api_key)
        self.collection_name = collection_name

    def generate_old_payload(self, video_code: str, frame_number: int, frame_second: float) -> Dict[str, Any]:
        """
        Generate an old-style payload structure for testing.

        Args:
            video_code: Video identifier
            frame_number: Frame number
            frame_second: Frame timestamp

        Returns:
            Old payload structure
        """
        # Mix of different old formats to test migration robustness
        payload_variants = [
            # Variant 1: Old oriane-frames path, missing uuid/created_at
            {
                "path": f"oriane-frames/{video_code}/frame_{frame_number:06d}.jpg",
                "video_code": video_code,
                "frame_number": frame_number,
                "frame_second": frame_second,
                "width": 1920,
                "height": 1080,
                "file_size": random.randint(50000, 200000)
            },
            # Variant 2: Old path format, missing uuid only
            {
                "path": f"oriane-frames/{video_code}/frame_{frame_number:06d}.jpg",
                "video_code": video_code,
                "frame_number": frame_number,
                "frame_second": frame_second,
                "created_at": "2023-01-01T00:00:00Z",  # Old timestamp format
                "width": 1920,
                "height": 1080
            },
            # Variant 3: Old path format, missing created_at only
            {
                "path": f"oriane-frames/{video_code}/frame_{frame_number:06d}.jpg",
                "video_code": video_code,
                "frame_number": frame_number,
                "frame_second": frame_second,
                "uuid": "old-uuid-format-12345",  # Old UUID format
                "width": 1920,
                "height": 1080
            },
            # Variant 4: Missing video_code (should be extracted from path)
            {
                "path": f"oriane-frames/{video_code}/frame_{frame_number:06d}.jpg",
                "frame_number": frame_number,
                "frame_second": frame_second,
                "width": 1920,
                "height": 1080
            },
            # Variant 5: Malformed path
            {
                "path": f"oriane-frames/{video_code}",  # Missing filename
                "video_code": video_code,
                "frame_number": frame_number,
                "frame_second": frame_second
            }
        ]

        return random.choice(payload_variants)

    def generate_good_payload(self, video_code: str, frame_number: int, frame_second: float) -> Dict[str, Any]:
        """
        Generate a good payload structure (already migrated) for testing.

        Args:
            video_code: Video identifier
            frame_number: Frame number
            frame_second: Frame timestamp

        Returns:
            Good payload structure
        """
        from uuid import uuid5, NAMESPACE_URL
        from datetime import datetime, timezone

        return {
            "uuid": str(uuid5(NAMESPACE_URL, f"{video_code}_{frame_number}_{frame_second}")),
            "created_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            "video_code": video_code,
            "frame_number": frame_number,
            "frame_second": frame_second,
            "path": f"instagram/{video_code}/frame_{frame_number:06d}.jpg",
            "width": 1920,
            "height": 1080,
            "file_size": random.randint(50000, 200000)
        }

    def generate_random_vector(self, dimension: int = 1024) -> List[float]:
        """Generate a random vector for testing."""
        # Generate random normalized vector
        vector = np.random.normal(0, 1, dimension)
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()

    def create_test_points(self, num_bad_points: int = 50, num_good_points: int = 10) -> List[models.PointStruct]:
        """
        Create test points with mix of good and bad payloads.

        Args:
            num_bad_points: Number of points with old structure
            num_good_points: Number of points with new structure

        Returns:
            List of test points
        """
        points = []

        # Sample video codes
        video_codes = [
            "ABC123DEF456",
            "XYZ789GHI012",
            "JKL345MNO678",
            "PQR901STU234",
            "VWX567YZA890"
        ]

        # Generate bad points
        for i in range(num_bad_points):
            video_code = random.choice(video_codes)
            frame_number = random.randint(1, 1000)
            frame_second = round(random.uniform(0.0, 60.0), 2)

            payload = self.generate_old_payload(video_code, frame_number, frame_second)
            vector = self.generate_random_vector()

            point_id = f"bad_{i}_{video_code}_{frame_number}"

            points.append(models.PointStruct(
                id=point_id,
                payload=payload,
                vector=vector
            ))

        # Generate good points
        for i in range(num_good_points):
            video_code = random.choice(video_codes)
            frame_number = random.randint(1, 1000)
            frame_second = round(random.uniform(0.0, 60.0), 2)

            payload = self.generate_good_payload(video_code, frame_number, frame_second)
            vector = self.generate_random_vector()

            point_id = f"good_{i}_{video_code}_{frame_number}"

            points.append(models.PointStruct(
                id=point_id,
                payload=payload,
                vector=vector
            ))

        return points

    def upload_test_data(self, points: List[models.PointStruct]):
        """
        Upload test points to Qdrant collection.

        Args:
            points: List of points to upload
        """
        print(f"📤 Uploading {len(points)} test points to collection '{self.collection_name}'...")

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"✅ Successfully uploaded {len(points)} test points")
        except Exception as e:
            print(f"❌ Error uploading test data: {e}")

    def clear_collection(self):
        """Clear all points from the collection."""
        print(f"🗑️  Clearing collection '{self.collection_name}'...")

        try:
            # Delete all points by using a filter that matches everything
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="frame_number",
                                match=models.MatchExcept(except_any=[])  # Matches all points
                            )
                        ]
                    )
                )
            )
            print("✅ Collection cleared")
        except Exception as e:
            print(f"❌ Error clearing collection: {e}")

    def show_collection_stats(self):
        """Show collection statistics."""
        try:
            info = self.client.get_collection(self.collection_name)
            print(f"📊 Collection '{self.collection_name}' statistics:")
            print(f"   Total points: {info.points_count}")
            print(f"   Vector size: {info.config.params.vectors.size}")
            print(f"   Distance metric: {info.config.params.vectors.distance}")
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate test data for Qdrant migration testing")
    parser.add_argument("--qdrant-url", required=True, help="Qdrant server URL")
    parser.add_argument("--api-key", required=True, help="Qdrant API key")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--bad-points", type=int, default=50, help="Number of bad points to generate")
    parser.add_argument("--good-points", type=int, default=10, help="Number of good points to generate")
    parser.add_argument("--clear", action="store_true", help="Clear collection before generating new data")
    parser.add_argument("--stats-only", action="store_true", help="Only show collection statistics")

    args = parser.parse_args()

    # Create generator
    generator = TestDataGenerator(
        qdrant_url=args.qdrant_url,
        api_key=args.api_key,
        collection_name=args.collection
    )

    if args.stats_only:
        generator.show_collection_stats()
        return

    # Clear collection if requested
    if args.clear:
        generator.clear_collection()

    # Generate and upload test data
    points = generator.create_test_points(
        num_bad_points=args.bad_points,
        num_good_points=args.good_points
    )

    generator.upload_test_data(points)
    generator.show_collection_stats()

    print(f"\n🎯 Test data generated successfully!")
    print(f"   📊 Bad points (need migration): {args.bad_points}")
    print(f"   ✅ Good points (already migrated): {args.good_points}")
    print(f"   📝 Total points: {len(points)}")


if __name__ == "__main__":
    main()
