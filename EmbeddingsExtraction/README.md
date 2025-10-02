# EmbeddingsExtraction

EmbeddingsExtraction is a small yet production-ready reference stack that showcases how to:

1. **Extract multi-modal embeddings** (images & text) from video frames using the multilingual [Jina-CLIP v2](https://github.com/jina-ai/jina-clip) model.
2. **Stream the embeddings into [Qdrant](https://qdrant.tech)** — an open-source, high-performance vector database – together with rich payload metadata.
3. **Search the collection** with image, video or text queries.
4. **Package the whole system** so it can be spun-up locally with Docker _or_ provisioned on a remote Ubuntu server in minutes.

> The repository is intentionally concise (~200 LoC) so you can grasp the end-to-end flow at a glance and adapt it to your own projects.

---

## ✨ Key Features

• **Jina-CLIP v2 encoder** (1024-D) automatically truncated to 512 dimensions for Qdrant.<br/>
• **S3 streaming ingest** that keeps GPU memory in check (configurable batch size).<br/>
• **Cosine-distance search** with optional payload filters.<br/>
• **Image → frames**, **Text → frames** and **Video → video** query modes demonstrated.<br/>
• Single-command **local stack (`docker-compose`)** & **remote install script** (Docker + Nginx + Certbot).

---

## 📂 Repository Layout

```text
EmbeddingsExtraction/
 ├── src/                 # All Python sources
 │   ├── ingest_frames_embeds.py   # S3 → Jina-CLIP → Qdrant pipeline
 │   ├── search_playground.py      # Examples for the 3 query modes
 │   ├── init/
 │   │   └── create_collection.py  # One-off helper to create the Qdrant collection
 │   ├── models/                   # Thin wrappers around embedding models
 │   └── helpers/                  # Misc. utilities
 │
 ├── qdrant/             # Production-grade docker-compose stack (Qdrant + Nginx)
 │   ├── docker-compose.yml
 │   ├── nginx.conf
 │   └── remote-setup.sh         # Turns a fresh Ubuntu box into a ready-to-use stack
 │
 ├── docker-compose.yml  # Lightweight local stack (Qdrant only)
 ├── create_venv.sh      # Reproducible Python virtual-env installer
 ├── test_image.png      # Toy asset used in the README & examples
 └── start_qdrant.sh     # Convenience shortcut (`docker compose up -d` + health-check)
```

---

## 🚀 Quick Start (Local Machine)

### 1. Clone & install Python dependencies

```bash
# Clone
$ git clone <your-fork-url> embeddings-extraction && cd embeddings-extraction

# Create a reproducible venv (Python ≥ 3.10 recommended)
$ ./create_venv.sh
$ source .venv/bin/activate
```

### 2. Launch Qdrant locally

```bash
# Pull the image and start the container
$ ./start_qdrant.sh
```

A health-check on `localhost:6333/metrics` should return instantly.

### 3. Ingest your video frames

Set the following environment variables (see `.env.example` for the full list):

```bash
export AWS_ACCESS_KEY_ID=…
export AWS_SECRET_ACCESS_KEY=…
export AWS_REGION=us-east-1        # or your own
export AWS_S3_BUCKET=oriane-frames # default bucket used in the code
```

Then run the ingestion script:

```bash
$ python -m src.ingest_frames_embeds
```

Frames are streamed from S3, encoded on-the-fly and upserted in batches of 8 (6 GB GPU friendly). You should see something like:

```
Ingesting: 100%|████████████████████| 42.3k/42.3k [02:10<00:00, 325.60it/s]
✅ Finished ingesting from S3
```

### 4. Play with the search playground

```bash
# 1⃣ Image → frames
$ python -m src.search_playground --image ./test_image.png --top_k 5

# 2⃣ Text → frames
$ python -m src.search_playground --text "Dogs dancing under the rain" --top_k 10

# 3⃣ Video → video (sample 1 FPS by default)
$ python -m src.search_playground --video /path/my_query.mp4 --fps 0.5 --top_k 3
```

The script prints nicely formatted payloads such as:

```
tiktok/ABC123   frame=42  sec=17.00  score=0.8134
```

---

## ⚙️ Configuration

| Variable        | Default         | Description                                                  |
| --------------- | --------------- | ------------------------------------------------------------ |
| `AWS_S3_BUCKET` | `oriane-frames` | S3 bucket containing the frame PNGs                          |
| `BATCH_SIZE`    | `8`             | Frames processed per GPU batch                               |
| `DIM`           | `512`           | Number of vector dims stored in Qdrant (truncated from 1024) |
| `COLL`          | `video_frames`  | Name of the Qdrant collection                                |

All config values are surfaced at the top of `src/ingest_frames_embeds.py` for quick tweaking.

---

## ☁️ Deploying on a Remote Server

1. **Spin-up a fresh Ubuntu 22.04 LTS VPS** (tested on x86/64 + ARM64).
2. `scp -r qdrant/ user@server:/opt/qdrant-stack` (or clone the whole repo).
3. `ssh user@server "bash /opt/qdrant-stack/remote-setup.sh"`.

The script:

- Installs Docker CE + docker-compose‐plugin.
- Installs Nginx & obtains a Let's Encrypt cert (domain configured in the script).
- Creates `/qdrant_data` with correct permissions.
- Starts the stack with TLS termination on port 443.

You can then point your ingestion/search scripts to `https://<your-domain>` by setting `QDRANT_HOST`, `QDRANT_PORT`, and `https` scheme accordingly.

---

## 📝 Extending the Project

- **Switch encoder** – drop a new file in `src/models/` and plug it in `ingest_frames_embeds.py`.
- **Add more payload indexes** – see `src/init/create_collection.py` for examples.
- **Use a different storage backend** – Adapt the `iter_s3_keys` generator to read from GCS, local FS, etc.
- **Integrate with your app** – `src.helpers.searchers` contains tiny functions you can import in Jupyter notebooks or FastAPI apps.

---

## 🤝 Contributing

Issues and PRs are welcome! Please open an issue first to discuss your proposed change so we can align on scope and approach.

---

## 📜 Acknowledgements

- [Jina AI](https://jina.ai) for the open-source CLIP v2 model.
- [Qdrant](https://qdrant.tech) for the blazing-fast vector DB and superb SDK.

---

_© 2025 Oriane Labs – All rights reserved._
