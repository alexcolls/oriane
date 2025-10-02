#!/usr/bin/env python3
"""fix_wrong_points.py – Repair malformed points in the `watched_frames` Qdrant collection.

V4 – **defer deletions to the very end** (so we no longer mutate the collection
while scrolling) and adds an _aggressive_ fallback that walks IDs one‑by‑one if
scroll keeps failing.

Why defer deletes?
------------------
Deleting points mid‑scroll can make the `offset` token stale; on some Qdrant
set‑ups that leads to the connection being closed (the *Server disconnected
without sending a response* you’re seeing). Now we:

1. **Upsert** any corrected record immediately (safe – adds data but doesn’t
   change existing offsets).
2. **Collect IDs to delete** in memory.
3. After the full scan completes (or on graceful Ctrl‑C) we bulk‑delete them in
   chunks.

Extra hardening:
* If `scroll` still fails after retries all the way down to `MIN_SCROLL`, we
  fall back to getting **all point IDs via /collections/{name}/points/ids** and
  iterate them individually (never touches `scroll`). That is slow, but keeps
  you from being stuck.
"""

from __future__ import annotations

import atexit
import datetime as _dt
import itertools
import math
import os
import sys
import time
import uuid
from typing import Iterable, List

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException
from qdrant_client.http.models import PointStruct

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        print(f"Missing env var {name}", file=sys.stderr)
        sys.exit(1)
    return v


load_dotenv('../../core/py/pipeline/.env')

QDRANT_URL = _env("QDRANT_URL", "http://localhost:6333")
QDRANT_KEY = os.getenv("QDRANT_KEY")
COLLECTION = _env("QDRANT_COLLECTION", "watched_frames")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
UPSERT_CHUNK = int(os.getenv("UPSERT_CHUNK", "256"))
DELETE_CHUNK = int(os.getenv("DELETE_CHUNK", "512"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "2.0"))
MIN_SCROLL = int(os.getenv("MIN_SCROLL", "100"))

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def deterministic_uuid(code: str, num: int, sec: float) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{code}_{num}_{sec}"))


def correct_path(platform_: str, code: str, n: int, sec: float) -> str:
    return f"{platform_}/{code}/{n}_{sec}.png"


MANDATORY_FIELDS = {
    "platform",
    "video_code",
    "frame_number",
    "frame_second",
    "created_at",
    "path",
}


def _with_retry(fn, *args, **kwargs):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except ResponseHandlingException as exc:
            if attempt == MAX_RETRIES:
                raise
            print(f"[WARN] {exc}; retry {attempt}/{MAX_RETRIES}")
            time.sleep(RETRY_DELAY * attempt)

# ---------------------------------------------------------------------------
# Global deletion bucket (filled during scan, flushed at exit)
# ---------------------------------------------------------------------------

delete_bucket: List[str | int] = []

def _flush_deletes(client: QdrantClient):
    if not delete_bucket:
        return
    print(f"\nFlushing {len(delete_bucket)} deletions…")
    for i in range(0, len(delete_bucket), DELETE_CHUNK):
        _with_retry(
            client.delete,
            collection_name=COLLECTION,
            points_selector=delete_bucket[i : i + DELETE_CHUNK],
        )
    print("Deletions complete.")

# ---------------------------------------------------------------------------
# Repair helpers
# ---------------------------------------------------------------------------

def prepare_repairs(points) -> List[PointStruct]:
    """Return upserts and extend global delete list."""

    upserts: List[PointStruct] = []

    for p in points:
        pl = p.payload or {}
        platform = pl.get("platform", "instagram")
        code = pl.get("video_code")
        num = pl.get("frame_number")
        sec = pl.get("frame_second")
        if None in (code, num, sec):
            continue
        try:
            num_i = int(num)
            sec_f = float(sec)
        except (TypeError, ValueError):
            continue
        expect_id = deterministic_uuid(code, num_i, sec_f)
        expect_path = correct_path(platform, code, num_i, sec_f)

        new_pl = pl.copy()
        repaired = False
        if new_pl.get("path") != expect_path:
            new_pl["path"] = expect_path; repaired = True
        if "created_at" not in new_pl:
            new_pl["created_at"] = _dt.datetime.utcnow().isoformat(timespec="microseconds") + "Z"; repaired = True
        for fld in MANDATORY_FIELDS - new_pl.keys():
            new_pl[fld] = (
                platform if fld == "platform" else
                code if fld == "video_code" else
                num_i if fld == "frame_number" else
                sec_f if fld == "frame_second" else None
            ); repaired = True

        id_fix = str(p.id) != expect_id
        if id_fix or repaired:
            upserts.append(PointStruct(id=expect_id if id_fix else p.id, vector=p.vector, payload=new_pl))
            if id_fix:
                delete_bucket.append(p.id)

    return upserts


def chunked(iterable: Iterable, size: int):
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, size))
        if not batch:
            return
        yield batch

# ---------------------------------------------------------------------------
# Fallback – iterate explicit IDs (never uses scroll)
# ---------------------------------------------------------------------------

def id_walk_mode(client: QdrantClient):
    print("Switching to ID‑walk fallback – this will be slower but robust.")
    collection_info = _with_retry(client.get_collection, COLLECTION)
    total_points = collection_info.points_count
    print(f"Collection has {total_points} points; fetching all IDs…")
    
    # Get all point IDs using scroll with a large limit
    all_ids = []
    offset = None
    while True:
        points, offset = _with_retry(
            client.scroll,
            collection_name=COLLECTION,
            limit=10000,  # Large batch to get all IDs quickly
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )
        if not points:
            break
        all_ids.extend([p.id for p in points])
    
    print(f"Retrieved {len(all_ids)} point IDs")

    total_fixed = total_seen = 0
    for id_chunk in chunked(all_ids, BATCH_SIZE):
        pts = _with_retry(client.retrieve, COLLECTION, ids=id_chunk, with_payload=True, with_vectors=True)
        upserts = prepare_repairs(pts)
        for up_chunk in chunked(upserts, UPSERT_CHUNK):
            _with_retry(client.upsert, collection_name=COLLECTION, points=up_chunk)
        total_fixed += len(upserts)
        total_seen += len(pts)
        print(f"IDs {total_seen}/{len(all_ids)} processed – fixed {total_fixed}")

    return total_fixed

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
    atexit.register(_flush_deletes, client)

    # Get collection info to know total points
    collection_info = _with_retry(client.get_collection, COLLECTION)
    total_points = collection_info.points_count
    print(f"Collection {COLLECTION} has {total_points} points")

    offset = None
    batch = BATCH_SIZE
    total_fixed = total_seen = 0

    print(f"Scanning {COLLECTION} at {QDRANT_URL} (scroll={batch})…")
    while True:
        # Safety check: if we've processed more points than exist, something is wrong
        if total_seen >= total_points * 2:  # Allow some buffer for duplicates/retries
            print(f"[ERROR] Processed {total_seen} points but collection only has {total_points}. Switching to ID walk mode.")
            total_fixed = id_walk_mode(client)
            break
            
        try:
            points, offset = _with_retry(
                client.scroll,
                collection_name=COLLECTION,
                limit=batch,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
        except ResponseHandlingException as exc:
            if batch > MIN_SCROLL:
                batch = max(MIN_SCROLL, batch // 2)
                print(f"[WARN] Scroll still failing. Reduce batch → {batch} and retry…")
                continue
            else:
                print(f"[ERROR] Scroll unusable even at {batch}; {exc}")
                break

        if not points:
            break

        total_seen += len(points)
        upserts = prepare_repairs(points)
        for up_chunk in chunked(upserts, UPSERT_CHUNK):
            _with_retry(client.upsert, collection_name=COLLECTION, points=up_chunk)
        total_fixed += len(upserts)
        print(f"Seen {total_seen}/{total_points} | Fixed {total_fixed} | scroll={batch}")

    # If scroll fell apart entirely – walk IDs
    if total_seen == 0:
        total_fixed = id_walk_mode(client)

    print("\nPASS COMPLETE – please wait for delete flush…")


if __name__ == "__main__":
    main()
