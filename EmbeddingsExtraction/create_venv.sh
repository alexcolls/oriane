#!/usr/bin/env bash
set -e

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

# ---------- Core libs ----------
pip install "python-dotenv>=1.0"          # env loader
pip install "qdrant-client[grpc]>=1.14"   # vector DB sdk
pip install boto3                         # S3 client for ingestion
pip install opencv-python-headless

# ---------- PyTorch + CUDA ----------
# Pick ONE of the three lines below that matches your GPU driver
# CUDA 12.1  (NVIDIA driver ≥ 535)
#pip install torch==2.3.0+cu121 torchvision==0.18.0+cu121 --extra-index-url https://download.pytorch.org/whl/cu121
# CUDA 11.8  (driver ≥ 515, older GPUs)
#pip install torch==2.3.0+cu118 torchvision==0.18.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
# CPU-only fallback
# inside the activated .venv
pip install torch==2.3.0+cu121 torchvision==0.18.0+cu121 \
            --extra-index-url https://download.pytorch.org/whl/cu121

# ---------- Jina-CLIP v2 stack ----------
pip install "transformers==4.50.0" einops timm pillow safetensors

# ---------- Misc ----------
pip install tqdm   # stock tqdm is enough; add tqdm-multiprocess later if wanted
