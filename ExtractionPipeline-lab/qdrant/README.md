# Qdrant Vector Search Stack for Video Frames

A production-ready pipeline for ingesting, indexing, and querying **video frame embeddings** with [Qdrant](https://qdrant.tech/).
Frames are encoded with _Jina CLIP v2_, stored as 512-D vectors, and made searchable through both a local development setup and a cloud-native deployment.

---

## Features

• **GPU-accelerated ingestion** – `ingest_frames_embeds.py` streams PNG frames directly from Amazon S3, encodes them on-the-fly, and upserts them in batches.
• **Multimodal search playground** – `search_playground.py` supports image → frame, text → frame, and video → video retrieval.
• **Schema-as-code** – reusable `collections/create.py` builds collections from JSON configs.
• **Safe migrations** – idempotent scripts under `scripts/` to move or transform data between collections.
• **One-click deploy** – `deploy/` contains Docker Compose, Nginx, TLS, and helper SSH scripts for an HTTPS-secured EC2 host.

---

## Directory Overview

| Path                      | Purpose                                               |
| ------------------------- | ----------------------------------------------------- |
| `ingest_frames_embeds.py` | Ingest S3 frames → Qdrant (`video_frames` collection) |
| `search_playground.py`    | CLI demo for image / video / text similarity search   |
| `models/`                 | Thin wrappers around CLIP encoders (Jina-CLIP)        |
| `collections/`            | JSON configs + creator script for collections         |
| `scripts/`                | One-off migration and maintenance utilities           |
| `deploy/`                 | Docker, Nginx, Certbot, and remote setup helpers      |

---

## Quick Start (Local)

1. **Spin up Qdrant**

```bash
#  Terminal ① – start a disposable local instance
podman run --rm \
  -p 6333:6333 -p 6334:6334 \
  qdrant/qdrant:v1.14.1
```

2. **Create the collection (only once)**

```bash
python qdrant/collections/create.py qdrant/collections/user_videos.json
```

3. **Ingest frames**

```bash
export AWS_S3_BUCKET=my-bucket           # set in .env for persistence
python qdrant/ingest_frames_embeds.py
```

4. **Query the data**

```bash
# Text → frames
python qdrant/search_playground.py --text "dogs dancing in the rain" --top_k 15

# Image → frames
python qdrant/search_playground.py --image /path/query.png --top_k 10

# Video → video (sample 1 fps)
python qdrant/search_playground.py --video /path/query.mp4 --fps 1 --top_k 5
```

---

## Production Deployment

The `deploy/` folder shows one opinionated way to host Qdrant behind Nginx + TLS on an Ubuntu EC2 instance.

1. Copy your PEM key to `deploy/keys/` and adjust `HOST` inside `deploy-server.sh`.
2. From your laptop run:

```bash
cd qdrant/deploy
./deploy-server.sh
```

The script:

• Installs Docker CE & Compose on the remote host.
• Provision LetsEncrypt certificates with Certbot.
• Boots the stack defined in `docker-compose.yml`.

Once complete, the Qdrant REST API will be available at `https://qdrant.admin.oriane.xyz:6333` (change the domain in `remote-setup.sh`).

---

## Maintenance & Migration Scripts

| Script                            | Description                                                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `scripts/migrate_video_frames.py` | Re-index existing `video_frames` points into a new `watched_frames` collection with a fresh payload schema.       |
| `scripts/migrate_collection.py`   | Safely drop & recreate a remote collection, then bulk-upload all local points (over REST) in configurable chunks. |

All scripts are **idempotent**; they will prompt for confirmation before destructive actions and respect `.env` credentials.

---

## Configuration

Place a `.env` file at project root (or export in your shell) with at least:

```env
# Qdrant
QDRANT_URL=http://localhost:6333         # or your remote endpoint
QDRANT_KEY=XXXXXXXXXXXX                  # leave blank for local dev

# AWS S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=oriane-frames
```

---

## Requirements

• Python 3.10+
• CUDA-enabled GPU (optional but recommended for fast CLIP encoding)
• Docker / Podman if you wish to run Qdrant locally

Install Python deps (preferably in a virtual env):

```bash
pip install -r requirements.txt  # see pyproject.toml if using Poetry
```

Key packages: `qdrant-client`, `torch`, `transformers`, `boto3`, `opencv-python`, `tqdm`, `python-dotenv`, `Pillow`.

---

## FAQ

**Which CLIP model is used?**
`jinaai/jina-clip-v2`, a multilingual ViT-B/16 model exposed via HuggingFace.

**How many vectors can this handle?**
The default Qdrant config easily serves tens of millions of 512-D vectors on a modest EC2 m6a.large (8 GiB RAM). Scale by adding shards / replicas.

**Can I change the embedding dimension?**
Yes – adjust `DIM` in `ingest_frames_embeds.py` _and_ the `vector_params.size` field in your collection JSON.

---

Happy searching! 🚀
