# Extraction Pipeline – Test Utilities

This folder contains small helper scripts and sample data that let you
exercise the **entire pipeline** without having to spin up any external
infrastructure. Everything can be executed on a developer laptop either
(a) directly in a local Python virtual-environment or (b) inside a Docker
container that mirrors the production image.

> All commands in the examples below are meant to be executed from the
> repository root (`$PROJECT_ROOT`). Adapt the paths if you are working
> from a different directory.

---

## 1. Local end-to-end run – `test_locally.sh`

Runs the pipeline on the host machine.
It will automatically create a **Python 3 virtual-environment**, install the
pinned requirements and then launch `python entrypoint.py` with a sample
`JOB_INPUT` payload.

```bash
# Basic run (creates .venv on first call)
./test/test_locally.sh

# Re-install all requirements even if requirements.txt did not change
./test/test_locally.sh --reinstall

# Additionally (re-)install GPU acceleration libraries defined in
# lib/extras_gpu.sh (e.g. CUDA, Torch w/ GPU, …)
./test/test_locally.sh --extras
```

The script writes a detailed log to `test/test_locally.log` and prints a
timing summary at the end.

Prerequisites:

- Python ≥ 3.9
- `virtualenv` (installed automatically via the standard library module)
- [optional] a CUDA-compatible GPU if you want to test GPU extras.

---

## 2. Docker end-to-end run – `test_docker.sh`

Builds the production Docker image and executes the pipeline **inside a
container**:

```bash
./test/test_docker.sh
```

What the script does:

1. `docker build -t extraction-pipeline:dev .` – build image from the local
   `Dockerfile` (always rebuilt so that changes in the working copy are
   picked up).
2. `docker run` with
   - `--env-file .env` – injects secrets & config expected by the pipeline.
   - `-e JOB_INPUT=<json>` – passes the same sample job input used by the
     local script.
   - `-v $HOME/.aws:/root/.aws:ro` – mounts the host AWS credentials so the
     pipeline can write to S3.
   - `--gpus all` – expose all GPUs (remove if you do not have CUDA).

The runtime log is stored in `test/test_docker.log`.

Prerequisites:

- Docker ≥ 20.10
- (optional) NVIDIA Container Toolkit if you want GPU access inside Docker.

---

## 3. Generating a fresh `job_input.json` – `gen_job_input.py`

`job_input.json` is a **list of media identifiers** that the pipeline will
process. The file committed to the repository contains ~10 k Instagram
codes, but you can easily generate a new one that is tailored to your test
case:

```bash
# Dump the 5 000 most recent rows ordered by scraped_at into test/job_input.json
python test/gen_job_input.py --limit 5000 \
                             --order-col scraped_at \
                             --outfile   test/job_input.json
```

The script connects to the `insta_content` Postgres table using the database
parameters found in `.env` (`DB_HOST`, `DB_NAME`, `DB_USER`, …).

Arguments:

- `--limit` Number of rows to export (default **10 000**)
- `--order-col` Timestamp column that defines _recency_ (default
  **created_at**)
- `--outfile` Write path – use `-` for _stdout_ so you can pipe the JSON
  directly into Docker: `python gen_job_input.py - | docker run … -e JOB_INPUT=$(cat)`

---

## 4. Vector search helpers – `test/search/`

After you have populated the Qdrant collection with embeddings you can run
quick similarity searches directly from the command line.
Both scripts rely on the **same encoder functions** that the main pipeline
uses (`src.infer_embeds`).

### 4.1 Image search – `search_image.py`

```bash
python test/search/search_image.py \
       --image test/samples/images/kids.png \
       --limit 5
```

Arguments:

- `--image` Path to a PNG/JPG; will be embedded and searched.
- `--limit` How many nearest neighbours to return (default **5**).
- `--collection` Qdrant collection (default **watched_frames**).

### 4.2 Text search – `search_text.py`

```bash
python test/search/search_text.py --text "a dog playing on the grass" --limit 10
```

Both search scripts expect **Qdrant credentials** (`QDRANT_URL`, `QDRANT_KEY`)
inside your `.env` at the project root.

---

## 5. Sample media

`test/samples/` contains a handful of small images and short Instagram
reels that you can use for ad-hoc tests without having to download new
content first.

```
└── test/samples
    ├── images
    │   ├── kids.png
    │   ├── singer.png
    │   └── building.png
    └── videos
        └── …
```

---

## 6. Cleaning up

```bash
# Remove the virtual-environment and logs
rm -rf .venv test/test_locally.log

# Remove Docker image & logs
docker image rm extraction-pipeline:dev
aws s3 rm …               # if you uploaded test data
```

---

Happy testing! 🎉
