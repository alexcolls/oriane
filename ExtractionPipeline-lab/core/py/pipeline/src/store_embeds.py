"""
Phase 5 – Vector storage in Qdrant
──────────────────────────────────
Public helpers
──────────────
* `upsert_embeddings(items: list[dict])`

    Each *item* must have keys:
        • "id"        – int | str
        • "vector"    – list[float]  (len == settings.dim)
        • "payload"   – dict         (arbitrary meta)

Example item structure (same as original frames_embeddings.py):

```python
{
    "id": f"{video_stem}_{frame_idx}",
    "vector": [0.123, 0.456, …],          # 512 floats
    "payload": {
        "video": "some_clip.mp4",
        "timestamp_s": 42.3,
        "path": "frames/some_clip/15_42.30.png"
    }
}
"""

from __future__ import annotations

import itertools
import time
from typing import Any, Dict, Iterable, List

from config.env_config import settings
from config.logging_config import configure_logging
from config.profiler import profile
from qdrant_client import QdrantClient, models

log = configure_logging()

_QD: QdrantClient | None = None  # singleton


def _client() -> QdrantClient:
    """Lazy initialiser – prefer gRPC for speed, fall back to REST."""
    global _QD
    if _QD is None:
        _QD = QdrantClient(
            url=settings.qdrant_url.rstrip("/"),
            api_key=settings.qdrant_key or None,
            prefer_grpc=True,
        )
        log.info(f"🔗 [qdrant] connected → {settings.qdrant_url}/")
        _ensure_collection()
    return _QD


def _ensure_collection() -> None:
    """Create the collection iff it doesn't exist (idempotent)."""
    cl = _QD
    if cl is None:
        return
    existing = [c.name for c in cl.get_collections().collections]
    if settings.collection in existing:
        return

    log.info(f"[qdrant] creating collection '{settings.collection}'")
    cl.create_collection(
        collection_name=settings.collection,
        vectors_config=models.VectorParams(size=settings.dim, distance=models.Distance.COSINE),
    )


def _chunks(iterable: Iterable[Any], n: int) -> Iterable[List[Any]]:
    """Yield successive *n*-sized chunks."""
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


@profile
def upsert_embeddings(points: List[Dict[str, Any]], *, batch: int | None = None) -> None:
    """
    Upsert `points` into Qdrant.

    `points` must be a list of dicts with keys **id**, **vector**, **payload**.
    """
    if not points:
        log.warning("[qdrant] no points to upsert")
        return

    cl = _client()
    batch = batch or settings.batch_size
    total = len(points)
    pushed = 0
    t0 = time.perf_counter()

    for chunk in _chunks(points, batch):
        cl.upsert(
            collection_name=settings.collection,
            wait=True,
            points=models.Batch(
                ids=[p["id"] for p in chunk],
                vectors=[p["vector"] for p in chunk],
                payloads=[p["payload"] for p in chunk],
            ),
        )
        pushed += len(chunk)

    log.info(f"✅ [qdrant] upserted {pushed}/{total} pts in {time.perf_counter() - t0:.2f}s")
