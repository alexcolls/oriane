#!/usr/bin/env python3
"""
Fix Qdrant Collection Dimension
===============================
This script will:
1. Check the current watched_frames collection
2. Delete it if it has wrong dimensions (1024 instead of 512)
3. Recreate it with correct dimensions (512)
4. Optionally migrate data from video_frames collection if it exists
"""

import sys

from config.env_config import settings
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams


def main():
    print(f"🔍 Connecting to Qdrant at {settings.qdrant_url}")

    client = QdrantClient(
        url=settings.qdrant_url.rstrip("/"),
        api_key=settings.qdrant_key or None,
        prefer_grpc=True,
    )

    # Check current collections
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]

    print(f"📋 Available collections: {collection_names}")

    # Check if watched_frames exists and its configuration
    target_collection = settings.collection  # "watched_frames"

    if target_collection in collection_names:
        try:
            collection_info = client.get_collection(target_collection)
            current_dim = collection_info.config.params.vectors.size
            print(f"📏 Current {target_collection} dimension: {current_dim}")

            if current_dim == settings.dim:
                print(
                    f"✅ Collection already has correct dimension ({settings.dim}). Nothing to do!"
                )
                return

            if current_dim == 1024 and settings.dim == 512:
                print(f"❌ Collection has wrong dimension {current_dim}, expected {settings.dim}")

                # Count existing points
                collection_stats = client.get_collection(target_collection)
                point_count = collection_stats.points_count
                print(f"📊 Collection currently has {point_count} points")

                if point_count > 0:
                    response = input(
                        f"⚠️  This will DELETE {point_count} existing points in '{target_collection}'. Continue? (yes/no): "
                    )
                    if response.lower() != "yes":
                        print("❌ Operation cancelled")
                        return

                # Delete the collection
                print(f"🗑️  Deleting collection '{target_collection}'...")
                client.delete_collection(target_collection)
                print(f"✅ Collection '{target_collection}' deleted")

            else:
                print(f"❌ Unexpected dimension: {current_dim}. Expected either 512 or 1024.")
                return

        except Exception as e:
            print(f"❌ Error checking collection: {e}")
            return

    # Create the collection with correct dimensions
    print(f"🔨 Creating collection '{target_collection}' with dimension {settings.dim}...")

    client.create_collection(
        collection_name=target_collection,
        vectors_config=VectorParams(size=settings.dim, distance=Distance.COSINE),
    )

    print(f"✅ Collection '{target_collection}' created with dimension {settings.dim}")

    # Check if video_frames collection exists for migration
    if "video_frames" in collection_names:
        video_frames_info = client.get_collection("video_frames")
        video_frames_dim = video_frames_info.config.params.vectors.size
        video_frames_count = video_frames_info.points_count

        print(
            f"📋 Found 'video_frames' collection with {video_frames_count} points (dim: {video_frames_dim})"
        )

        if video_frames_dim == settings.dim and video_frames_count > 0:
            response = input(
                f"🔄 Migrate {video_frames_count} points from 'video_frames' to '{target_collection}'? (yes/no): "
            )
            if response.lower() == "yes":
                print("🔄 Starting migration...")

                # Scroll through all points in video_frames
                offset = None
                migrated_count = 0
                batch_size = 100

                while True:
                    points, offset = client.scroll(
                        collection_name="video_frames",
                        limit=batch_size,
                        offset=offset,
                        with_payload=True,
                        with_vectors=True,
                    )

                    if not points:
                        break

                    # Prepare points for upsert
                    upsert_points = []
                    for point in points:
                        upsert_points.append(
                            models.PointStruct(
                                id=point.id, vector=point.vector, payload=point.payload
                            )
                        )

                    # Upsert to target collection
                    client.upsert(
                        collection_name=target_collection, points=upsert_points, wait=True
                    )

                    migrated_count += len(upsert_points)
                    print(f"📦 Migrated {migrated_count}/{video_frames_count} points...")

                print(
                    f"✅ Migration complete! {migrated_count} points migrated from 'video_frames' to '{target_collection}'"
                )
            else:
                print("⏭️  Migration skipped")
        else:
            if video_frames_dim != settings.dim:
                print(
                    f"⚠️  video_frames has incompatible dimension ({video_frames_dim}), skipping migration"
                )
            else:
                print("⚠️  video_frames is empty, skipping migration")

    print("🎉 Operation completed successfully!")


if __name__ == "__main__":
    main()
