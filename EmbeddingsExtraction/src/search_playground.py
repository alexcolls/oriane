"""
search_playground.py
────────────────────
Demonstrates 3 query modes on the local Qdrant instance filled by
ingest_frames_embeds.py.

Usage examples (from project root):
  # 1. image → frames
  python -m src.search_playground --image /path/query.png --top_k 10

  # 2. video → frames  (samples 1 fps, change --fps as you like)
  python -m src.search_playground --video /path/query.mp4 --fps 1 --top_k 5

  # 3. text  → frames
  python -m src.search_playground --text "dogs dancing under the rain" --top_k 15
"""

import argparse, os, io, sys, json, pathlib
from collections import defaultdict

import boto3
import cv2
import numpy as np
from PIL import Image
import torch

from qdrant_client import QdrantClient, models
from src.models.jina_clip_v2 import encode_images_pil, encode_texts

DIM   = 512
COLL  = "video_frames"
DEV   = "cuda" if torch.cuda.is_available() else "cpu"

cl = QdrantClient(host="localhost", port=6333)


# ── helpers ────────────────────────────────────────────────────────────────
def to_payload(hit):
    p = hit.payload
    return f"{p['platform']}/{p['video']} frame={p['frame']} sec={p['second']:.2f}  score={hit.score:.4f}"

def search_vec(vec, top_k=10, flt=None):
    return cl.search(
        collection_name=COLL,
        query_vector=vec.tolist(),
        limit=top_k,
        query_filter=flt,
    )

def search_image(path, top_k=10, flt=None):
    img = Image.open(path).convert("RGB")
    vec = encode_images_pil([img], dim=DIM)[0][:DIM]
    return search_vec(vec, top_k, flt)

def search_text(prompt, top_k=10, flt=None):
    vec = encode_texts([prompt], dim=DIM)[0][:DIM]
    return search_vec(vec, top_k, flt)

def video_to_frames(path, fps=1):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open {path}")
    rate = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(rate / fps) if rate > 0 else 1
    i = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if i % frame_interval == 0:
            yield Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        i += 1
    cap.release()

def aggregate_video_hits(hits_per_frame, top_k):
    """Collapse many frame-level hits into video-level ranking."""
    scores = defaultdict(float)
    for hits in hits_per_frame:
        for h in hits:
            vid = h.payload["video"]
            scores[vid] = max(scores[vid], h.score)   # keep best hit score
    return sorted(scores.items(), key=lambda x: -x[1])[:top_k]


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--image", help="Path to query image")
    g.add_argument("--video", help="Path to query video (samples --fps)")
    g.add_argument("--text",  help="Text prompt")
    ap.add_argument("--fps", type=float, default=1.0, help="Frames/sec for video sampling")
    ap.add_argument("--top_k", type=int, default=10)
    args = ap.parse_args()

    if args.image:
        hits = search_image(args.image, args.top_k)
        print("\nTop frames for image query:")
        for h in hits:
            print(to_payload(h))

    elif args.text:
        hits = search_text(args.text, args.top_k)
        print("\nTop frames for text prompt:")
        for h in hits:
            print(to_payload(h))

    else:  # video query
        hits_all = []
        for fr in video_to_frames(args.video, fps=args.fps):
            vec = encode_images_pil([fr], dim=DIM)[0][:DIM]
            hits = search_vec(vec, top_k=args.top_k)
            hits_all.append(hits)
        top_videos = aggregate_video_hits(hits_all, args.top_k)
        print("\nTop videos for video query:")
        for vid, sc in top_videos:
            print(f"{vid:40s}  score={sc:.4f}")
