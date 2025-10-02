#!/usr/bin/env python3
"""
Migrate points from the remote ‘video_frames’ collection to ‘watched_frames’.

Highlights
----------
• Deterministic SHA-1 IDs on
  “{platform}:{video_code}:{frame_number}:{frame_second}”.
• ID duplicated in payload for easy filtering.
• Path auto-prefixed with platform (“instagram” default).
• created_at timestamp added (UTC ISO-8601).
• Vector-length guard (default 512-dim).
• Pure remote streaming:  client.scroll(...) → transform → upsert,
  so it handles any existing ID type (int, UUID, hex, etc.).
• Points missing either frame index **or** timestamp are skipped
  (and the script tells you how many).
"""

from __future__ import annotations

import hashlib
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from tqdm import tqdm  # pip install tqdm

# ─── Config ──────────────────────────────────────────────────────────────
SRC = "video_frames"
DST = "watched_frames"
BATCH_SIZE = 256
VECTOR_DIM = 512
DEFAULT_PLATFORM = "instagram"

# ─── Connection ─────────────────────────────────────────────────────────
load_dotenv("../../core/py/pipeline/.env", override=True)
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_KEY = os.getenv("QDRANT_KEY")
if not QDRANT_URL or not QDRANT_KEY:
    sys.exit("❌  QDRANT_URL and QDRANT_KEY must be set")

print(f"Connecting to Qdrant at {QDRANT_URL} …")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
print("✅  Connection successful.\n")


# ─── Helpers ────────────────────────────────────────────────────────────
def deterministic_id(
    platform: str, video_code: str, frame_number: int | str, frame_second: float | str
) -> str:
    """
    Returns a UUID-v5 generated from the 4 identifying fields.
    The result is deterministic and Qdrant-compatible.
    """
    name = f"{platform}:{video_code}:{frame_number}:{frame_second}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))  # 36-char UUID


def transform_payload(raw: Dict[str, Any], now_iso: str) -> tuple[str, Dict[str, Any]] | None:
    """
    Map origin payload to the new schema.
    Returns  (new_id, new_payload)  or None if required fields are missing.
    """
    platform = raw.get("platform") or DEFAULT_PLATFORM
    raw_video = raw.get("video") or raw.get("video_code") or ""
    video_code = raw_video.rsplit(".", 1)[0]

    frame_number = raw.get("frame_idx") or raw.get("frame_number")
    frame_second = raw.get("timestamp_s") or raw.get("frame_second")
    if frame_number is None or frame_second is None:
        return None  # skip — malformed

    path = raw.get("path", "")
    if not path.startswith(f"{platform}/"):
        path = f"{platform}/{path.lstrip('/')}"

    _id = deterministic_id(platform, video_code, frame_number, frame_second)

    return _id, {
        "id": _id,
        "platform": platform,
        "video_code": video_code,
        "path": path,
        "frame_number": int(frame_number),
        "frame_second": float(frame_second),
        "created_at": now_iso,
    }


# ─── Migration ──────────────────────────────────────────────────────────
def run_migration() -> None:
    print(f"🚀  Migrating ‘{SRC}’ → ‘{DST}’ …")
    now_iso = datetime.now(timezone.utc).isoformat()

    total_upserted = 0
    total_skipped = 0
    offset: Optional[models.PointId] = None

    pbar = tqdm(unit="pts", ncols=90)
    while True:
        batch, offset = client.scroll(
            collection_name=SRC,
            limit=BATCH_SIZE,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        if not batch:
            break

        upserts: List[models.PointStruct] = []
        for pt in batch:
            if len(pt.vector) != VECTOR_DIM:
                raise ValueError(
                    f"Vector length {len(pt.vector)} ≠ expected {VECTOR_DIM} " f"(src id {pt.id})"
                )
            transformed = transform_payload(pt.payload, now_iso)
            if transformed is None:
                total_skipped += 1
                continue
            new_id, new_payload = transformed
            upserts.append(models.PointStruct(id=new_id, vector=pt.vector, payload=new_payload))

        if upserts:
            client.upsert(collection_name=DST, points=upserts, wait=True)
            total_upserted += len(upserts)

        pbar.update(len(batch))
    pbar.close()

    print(f"\n🎉  Done: {total_upserted} upserted, {total_skipped} skipped " f"(to ‘{DST}’).")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as exc:
        sys.exit(f"\n❌  Migration aborted: {exc}")
