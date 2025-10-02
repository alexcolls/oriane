#!/bin/bash

# Script to pre-download the jina-clip-v2 model
# This allows you to download the model before starting the API container

echo "🔄 Pre-downloading jina-clip-v2 model..."

# Create a temporary container to download the model
docker run --rm -it \
    -v $(pwd)/.model-cache:/root/.cache/huggingface \
    -e FORCE_CPU=1 \
    python:3.11-slim bash -c "
        pip install sentence-transformers torch einops --no-cache-dir
        python -c \"
from sentence_transformers import SentenceTransformer
import torch
print('🔄 Downloading jina-clip-v2 model...')
model = SentenceTransformer('jinaai/jina-clip-v2', device='cpu', trust_remote_code=True)
print('✅ Model downloaded successfully!')
print(f'Model device: {model.device}')
\"
"

if [ $? -eq 0 ]; then
    echo "✅ Model download completed!"
    echo "📁 Model cached in: $(pwd)/.model-cache"
    echo "🚀 You can now start the API container with the pre-downloaded model"
else
    echo "❌ Model download failed!"
    exit 1
fi
