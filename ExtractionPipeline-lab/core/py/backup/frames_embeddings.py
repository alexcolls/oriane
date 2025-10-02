#!/usr/bin/env python3
"""
frames_embeddings.py
────────────────────
Take a directory full of *.png frames that were *just* extracted in-container,
encode them with jina-clip-v2 (512-D Matryoshka) on GPU, and upsert to the
remote Qdrant cluster defined by QDRANT_URL / QDRANT_KEY.

Nothing is read back from S3 – we operate on the fresh local files.
"""

from __future__ import annotations

import gc
import os
import re
import time
import uuid
from pathlib import Path
from typing import Dict, List

import torch
from dotenv import load_dotenv
from PIL import Image
from qdrant_client import QdrantClient, models

# --------------------------------------------------------------------------- #
# env / constants                                                             #
# --------------------------------------------------------------------------- #
load_dotenv(".env")  # dezelfde conventie als elders

QDRANT_URL = os.environ["QDRANT_URL"]  # e.g. https://qdrant.admin.oriane.xyz
QDRANT_KEY = os.environ["QDRANT_KEY"]
COLL = "video_frames"
DIM = 512
BATCH_SIZE = 8  # ← fits into a 6 GB card

# --------------------------------------------------------------------------- #
# initialise Qdrant (lazy – collection created only once)                     #
# --------------------------------------------------------------------------- #
qd = QdrantClient(
    url=QDRANT_URL.rstrip("/"),
    api_key=QDRANT_KEY,
    prefer_grpc=False,  # HTTPS+REST keeps things simple
    timeout=120,
)

if not qd.collection_exists(COLL):
    qd.create_collection(
        COLL,
        vectors_config=models.VectorParams(size=DIM, distance=models.Distance.COSINE),
    )
    for fld in ("platform", "video"):
        qd.create_payload_index(
            COLL,
            field_name=fld,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

# --------------------------------------------------------------------------- #
# encoder (shared model already written)                                      #
# --------------------------------------------------------------------------- #
from models.jina_clip_v2 import encode_images_pil  # noqa: E402

# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #
_FRAME_RE = re.compile(r"^(?P<idx>\d+)_(?P<sec>\d+\.\d+)\.png$")


def _iter_frames(dir_: Path) -> List[Path]:
    """Return frames sorted by the integer prefix (1_, 2_, 3_ …)."""
    return sorted(
        [p for p in dir_.glob("*.png") if _FRAME_RE.match(p.name)],
        key=lambda p: int(_FRAME_RE.match(p.name)["idx"]),
    )


def _encode_and_upsert(batch_files, platform: str, video: str):
    imgs = [Image.open(f).convert("RGB") for f in batch_files]
    with torch.inference_mode(), torch.cuda.amp.autocast():
        vecs = encode_images_pil(imgs, dim=DIM)  # (B, 512)
    torch.cuda.empty_cache()
    gc.collect()

    now = int(time.time())
    points = []
    for file_, vec in zip(batch_files, vecs):
        m = _FRAME_RE.match(file_.name)
        payload = {
            "platform": platform,
            "video": video,
            "frame": int(m["idx"]),
            "second": float(m["sec"]),
            "created_at": now,
        }
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vec.tolist(),
                payload=payload,
            )
        )
    qd.upsert(collection_name=COLL, points=points)


# --------------------------------------------------------------------------- #
# public API                                                                  #
# --------------------------------------------------------------------------- #
def embed_directory(frames_dir: Path, platform: str, video: str) -> int:
    """
    Encode every *.png in `frames_dir` and upsert to Qdrant.
    Returns the number of vectors written.
    """
    frame_files = _iter_frames(frames_dir)
    if not frame_files:
        print(f"[warn] no frames found in {frames_dir}")
        return 0

    buf: List[Path] = []
    written = 0
    for f in frame_files:
        buf.append(f)
        if len(buf) == BATCH_SIZE:
            _encode_and_upsert(buf, platform, video)
            written += len(buf)
            buf.clear()
    if buf:  # leftovers
        _encode_and_upsert(buf, platform, video)
        written += len(buf)
    print(f"  ↪︎ upserted {written} embeddings to Qdrant for {video}")
    return written
