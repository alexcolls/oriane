# Oriane Video-to-Embedding Pipeline

![CI](https://img.shields.io/badge/status-alpha-orange)
End-to-end extractor that turns raw Instagram videos into searchable CLIP
embeddings stored in Qdrant.

```
┌──────────┐ 0  download    ┌───────────────┐ 1  crop (opt.) ┌───────────────┐ 2 scene detect ┌──────────────┐
│ S3 video │──────────────►│ border_crop.py│───────────────►│ scene_framing │───────────────►│ deduplicate │
└──────────┘                └───────────────┘                └───────────────┘                └──────────────┘
                                                                                                   │
                                                                                                   ▼
                          5  embed & upsert ┌───────────────┐ 4 CLIP embeds  ┌──────────────┐   ┌───────────┐
                                            │ infer_embeds  │───────────────►│ store_embeds │──►│  Qdrant   │
                                            └───────────────┘                └──────────────┘   └───────────┘
                                                                                                   ▲
                                                                                                   │
                                                                         3 async upload frames     │
                                                                         ───────────────────────────┘
```

The central orchestrator is `entrypoint.py` which glues together lightweight
modules in `src/` and runtime configuration from `config/`.

---

## 1. Repository layout

```
core/py/pipeline/
├── entrypoint.py            # main entrypoint triggered by Docker / scripts
├── src/                     # stateless, testable processing stages
│   ├── download_videos.py   # S3 → local tmp/
│   ├── border_cropping.py   # Phase 1: smart letter-box removal (GPU ffmpeg)
│   ├── scene_framing.py     # Phase 2: scene-change sampling (PySceneDetect)
│   ├── deduplicate_frames.py# Phase 3: perceptual-hash filtering
│   ├── upload_frames.py     # Phase 3b: async S3 multipart uploads
│   ├── infer_embeds.py      # Phase 4: batch CLIP embeddings (Jina-CLIP-v2)
│   ├── store_embeds.py      # Phase 5: Qdrant upsert
│   └── pipeline.py          # Thin wrapper that strings phases 1-5 together
├── config/                  # Single source of truth for env + logging
│   ├── env_config.py        # immutable `settings` dataclass
│   ├── logging_config.py    # Rich console + JSONL file logs
│   └── profiler.py          # tiny decorator for phase timings
├── test/                    # helper scripts, sample media & docs
├── models/                  # pre-downloaded model weights (if any)
├── Dockerfile               # production image with CUDA-accelerated FFmpeg
└── requirements.txt         # pinned dependencies
```

---

## 2. Quick start

```bash
# 1. Clone & enter repo
$ git clone git@github.com:oriane-labs/extraction-pipeline.git && cd extraction-pipeline/core/py/pipeline

# 2. Copy env template and fill in secrets (AWS, Postgres, Qdrant …)
$ cp .env.example .env && $EDITOR .env

# 3. Run end-to-end on sample JOB_INPUT
$ ./test/test_locally.sh              # CPU or GPU
# or
$ ./test/test_docker.sh               # reproducible container build
```

The _test_ scripts take care of virtual-environment management, dependency
installation, Docker build caching and log aggregation. See
`test/README.md` for details.

---

## 3. Runtime configuration

All knobs are exposed as environment variables (see comments in
`config/env_config.py`). Sensible defaults make every feature opt-in:

| Variable             | Default             | Purpose                                            |
| -------------------- | ------------------- | -------------------------------------------------- |
| `AWS_REGION`         | us-east-1           | S3 region for video / frame buckets                |
| `S3_VIDEOS_BUCKET`   | oriane-contents     | Source bucket containing `platform/code/video.mp4` |
| `S3_FRAMES_BUCKET`   | oriane-frames       | Destination bucket for extracted PNGs              |
| `VP_ENABLE_CROP`     | 1                   | Toggle border_cropping phase                       |
| `VP_ENABLE_DEDUP`    | 1                   | Toggle perceptual-hash deduplication               |
| `VP_SAMPLE_FPS`      | 0.1                 | Target sampling rate for scene detect              |
| `VP_BATCH_SIZE`      | 8                   | CLIP batch size                                    |
| `CLIP_MODEL`         | jinaai/jina-clip-v2 | HuggingFace model name                             |
| `QDRANT_URL` / `KEY` | –                   | Vector DB endpoint & API key                       |
| `DB_*`               | –                   | Aurora Postgres creds (only needed in prod)        |

Adjust them in `.env` or via `docker run -e` flags.

---

## 4. Data flow in depth

1. **Download** – `src/download_videos.py` streams the MP4 from
   `s3://$S3_VIDEOS_BUCKET/<platform>/<code>/video.mp4` into a tmp dir.
2. **Crop (opt.)** – Black bars are removed by sampling `VP_CROP_PROBES`
   random positions, running `ffmpeg cropdetect`, and re-encoding on the GPU.
3. **Scene framing** – `PySceneDetect` extracts representative frames at
   `VP_SAMPLE_FPS`. Results are stored as `{idx}_{sec}.png`.
4. **Dedup (opt.)** – Adjacent frames with a dHash distance `≤VP_TOLERANCE`
   are removed.
5. **Async upload** – Extracted PNGs are uploaded concurrently to
   `s3://$S3_FRAMES_BUCKET/<platform>/<code>/` while the pipeline continues.
6. **CLIP embeddings** – Frames are batched (`VP_BATCH_SIZE`) through a
   _Jina-CLIP v2_ encoder on GPU.
7. **Qdrant upsert** – Each vector is inserted with a deterministic SHA-1
   primary key that encodes `(video_code, frame_number)` so reruns are idempotent.
8. **Book-keeping** – Success / failure events are recorded in Aurora PG
   unless `LOCAL_MODE=1`.

---

## 5. Extending / debugging

• **Swap models**: point `CLIP_MODEL` to any 512-dim CLIP variant.
• **Experiment with thresholds**: nearly every magic number lives in env vars.
• **Profiling**: each phase is wrapped by `@profile` – set
`PROFILE_JSON=run.prof` to dump Chrome-compatible traces.

> Tip: enable Rich tracebacks & JSONL logs for blazing-fast root-cause search.

---

## 6. Production deployment

The `Dockerfile` produces a self-contained CUDA 12 image (≈3 GB) that ships a
custom-built FFmpeg with NVENC/NPP for zero-copy GPU cropping. Pair it with
an Amazon ECS task or Kubernetes Job and feed it via SQS/Lambda triggering
mechanisms.

A minimal `docker run` looks like:

```bash
docker run --rm \
  --gpus all \
  --env-file .env \
  -e "JOB_INPUT=$(cat test/job_input.json | tr -d '\n')" \
  -v $HOME/.aws:/root/.aws:ro \
  extraction-pipeline:dev
```

---

## 7. License

© 2024 Oriane Labs. Released under the Apache-2.0 license.

---

_Questions or feedback? Open an issue or reach us at **dev@oriane.xyz**._
