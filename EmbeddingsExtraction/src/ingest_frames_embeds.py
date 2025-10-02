"""
ingest_frames_s3.py  –  6 GB-safe version
──────────────────────────────────────────
Streams PNG frames from s3://<BUCKET>/<platform>/<video>/<frame>_<sec>.png,
encodes them with jina-clip-v2 (512-D Matryoshka),
and upserts vectors + metadata to a local Qdrant instance.
"""

import gc, io, os, time, uuid
from functools import partial

from dotenv import load_dotenv
load_dotenv()

import boto3
from PIL import Image
from tqdm import tqdm
import torch

from qdrant_client import QdrantClient, models
from models.jina_clip_v2 import encode_images_pil

# ── Config ────────────────────────────────────────────────────────────────
BUCKET      = os.getenv("AWS_S3_BUCKET", "oriane-frames")
BATCH_SIZE  = 8            # ← fits a 6 GB RTX 2060
DIM         = 512
COLL        = "video_frames"

# ── Qdrant ────────────────────────────────────────────────────────────────
qd = QdrantClient(host="localhost", port=6333)
if not qd.collection_exists(COLL):
    qd.create_collection(
        COLL,
        vectors_config=models.VectorParams(size=DIM,
                                           distance=models.Distance.COSINE),
    )
    for field in ("platform", "video"):
        qd.create_payload_index(
            COLL, field_name=field,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

encode_imgs = partial(encode_images_pil, dim=DIM)   # keeps call-site tidy
s3          = boto3.client("s3")

# ── Helpers ───────────────────────────────────────────────────────────────
def iter_s3_keys(bucket):
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".png"):
                continue
            try:
                platform, video, filename = key.split("/", 2)
                frame_n, sec = filename[:-4].split("_")
            except ValueError:
                continue
            yield key, platform, video, int(frame_n), float(sec)

def load_image(key):
    body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    return Image.open(io.BytesIO(body)).convert("RGB")

def upsert_batch(batch):
    imgs = [load_image(b["s3_key"]) for b in batch]
    with torch.inference_mode(), torch.cuda.amp.autocast():
        vecs = encode_imgs(imgs)           # (B, 1024)
    vecs = vecs[:, :DIM]      # ▼ truncate to 512 so Qdrant accepts it
    torch.cuda.empty_cache()
    gc.collect()

    points = [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector=v.tolist(),
            payload={
                "platform": b["platform"],
                "video"   : b["video"],
                "frame"   : b["frame"],
                "second"  : b["second"],
                "created_at": int(time.time()),
            },
        )
        for b, v in zip(batch, vecs)
    ]
    qd.upsert(COLL, points)

# ── Main loop ─────────────────────────────────────────────────────────────
buf = []
for k, plat, vid, fn, sec in tqdm(iter_s3_keys(BUCKET), desc="Ingesting"):
    buf.append({"s3_key": k, "platform": plat, "video": vid,
                "frame": fn, "second": sec})
    if len(buf) == BATCH_SIZE:
        upsert_batch(buf)
        buf.clear()

if buf:
    upsert_batch(buf)

print("✅ Finished ingesting from S3")
