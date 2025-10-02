#!/usr/bin/env python3
import json
import os
import sys

import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

# ─── Load env ────────────────────────────────────────────────────────
HERE = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(HERE, "..", "pipeline/.env"))

LOCAL_URL = "http://localhost:6333"
REMOTE_URL = os.getenv("QDRANT_URL")  # e.g. http://qdrant.admin.oriane.xyz:6333
API_KEY = os.getenv("QDRANT_KEY")
COLLECTION = "video_frames"
VECTOR_DIM = 512
DISTANCE = rest.Distance.COSINE  # or rest.Distance.Euclid, etc.
BATCH_SIZE = 500
SCROLL_LIMIT = 1_000_000  # fetch all locally in one go

if not REMOTE_URL or not API_KEY:
    print("❌ QDRANT_URL and QDRANT_KEY must be set in env or .env", file=sys.stderr)
    sys.exit(1)

remote = QdrantClient(url=REMOTE_URL, api_key=API_KEY)

# ─── 0) Confirmation ────────────────────────────────────────────────
print(f"\n⚠️  You are about to DESTRUCTIVELY reset the remote collection “{COLLECTION}”.")
print("   This will DELETE all existing data in that collection,")
print("   then RECREATE it and UPLOAD your entire *local* data.\n")
resp = input("   Are you absolutely sure you want to proceed? [y/N] ").strip().lower()
if resp != "y":
    print("Aborted. No changes made.")
    sys.exit(0)

# ─── 1) Drop & recreate ─────────────────────────────────────────────
print(f"\n🛑 Deleting remote collection “{COLLECTION}” (if it exists)…")
remote.delete_collection(collection_name=COLLECTION)
print("  → deleted (or did not exist)")

print(f"🆕 Recreating remote collection “{COLLECTION}” …")
remote.create_collection(
    collection_name=COLLECTION,
    vectors_config=rest.VectorParams(size=VECTOR_DIM, distance=DISTANCE),
)
print("  → created")

# ─── 2) Scroll local in one shot ────────────────────────────────────
print(f"\n📥 Fetching all points from local Qdrant (limit={SCROLL_LIMIT})…")
r = requests.post(
    f"{LOCAL_URL}/collections/{COLLECTION}/points/scroll",
    headers={"Content-Type": "application/json"},
    json={
        "with_payload": True,
        "with_vectors": True,
        "limit": SCROLL_LIMIT,
    },
    timeout=120,
)
r.raise_for_status()
all_points = r.json()["result"]["points"]
print(f"  → fetched {len(all_points)} points locally")

# ─── 3) Chunk & upsert ──────────────────────────────────────────────
print(f"\n🚚 Uploading in batches of {BATCH_SIZE} …")
total = 0
for i in range(0, len(all_points), BATCH_SIZE):
    chunk = all_points[i : i + BATCH_SIZE]
    pts = [
        rest.PointStruct(
            id=p["id"],
            vector=p["vector"],
            payload=p.get("payload", {}),
        )
        for p in chunk
    ]
    remote.upsert(
        collection_name=COLLECTION,
        points=pts,
        wait=True,
    )
    total += len(pts)
    print(f"  • upserted {len(pts):4d}  (running total: {total})")

print(f"\n✅ All done! Remote “{COLLECTION}” now has {total} points.\n")
