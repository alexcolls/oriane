from __future__ import annotations

"""Qdrant service

Centralised helper for connecting to Qdrant and performing common
operations (currently limited to *search* for the API needs).
"""

import os
from functools import lru_cache
from typing import Any, Dict, List

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

# Attempt to load a .env file at repo root so local development works out of
# the box. We silence failures because in production these vars are expected
# to be present in the environment already.
load_dotenv(dotenv_path=os.getenv("DOTENV_PATH", ".env"), override=False)


# ---------------------------------------------------------------------------
# Client initialisation (singleton)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _client() -> QdrantClient:
    """Return a cached *QdrantClient* instance based on env-vars."""
    url = os.getenv("QDRANT_URL")
    key = os.getenv("QDRANT_KEY")
    if not url or not key:
        raise RuntimeError("QDRANT_URL and QDRANT_KEY must be set in the environment or .env file.")

    return QdrantClient(url=url.rstrip("/"), api_key=key, prefer_grpc=True)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def search(
    *, vector: List[float], limit: int = 5, collection: str | None = None
) -> List[models.ScoredPoint]:
    """Search *collection* for *vector* and return the raw hits list."""
    collection_name = collection or os.getenv("QDRANT_COLLECTION", "watched_frames")
    client = _client()

    return client.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )


def fetch_embedding(
    *, collection: str, user_id: str, entry_id: str
) -> tuple[List[float], Dict[str, Any] | None]:
    """Fetch a specific embedding vector and payload from the specified collection."""
    client = _client()

    # Fetch the point by ID
    points = client.retrieve(
        collection_name=collection, ids=[entry_id], with_payload=True, with_vectors=True
    )

    if not points:
        raise ValueError(f"No entry found with ID {entry_id} in collection {collection}")

    point = points[0]

    # Verify the user_id matches if it exists in payload
    if point.payload and point.payload.get("user_id") != user_id:
        raise ValueError(f"Entry {entry_id} does not belong to user {user_id}")

    if not point.vector:
        raise ValueError(f"No vector found for entry {entry_id}")

    return point.vector, point.payload


def fetch_all_video_embeddings(
    *, collection: str, user_id: str, video_id: str
) -> List[tuple[List[float], Dict[str, Any] | None]]:
    """Fetch all embeddings for a specific video from the specified collection."""
    client = _client()

    # Search for all points with the given video_id and user_id
    filter_condition = models.Filter(
        must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
            models.FieldCondition(key="video_id", match=models.MatchValue(value=video_id)),
        ]
    )

    # Scroll through all points that match the filter
    points, _ = client.scroll(
        collection_name=collection,
        scroll_filter=filter_condition,
        with_payload=True,
        with_vectors=True,
        limit=10000,  # Large limit to get all frames
    )

    if not points:
        raise ValueError(
            f"No video frames found for video_id {video_id} and user_id {user_id} in collection {collection}"
        )

    # Sort by frame_number if available in payload
    points.sort(key=lambda p: p.payload.get("frame_number", 0) if p.payload else 0)

    return [(point.vector, point.payload) for point in points if point.vector]
