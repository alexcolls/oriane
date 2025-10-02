# Oriane Search API

## Overview

The Oriane Search API is a modular and scalable microservice built with FastAPI. It serves as a gateway in Oriane's video extraction pipeline, enabling high-performance search functionalities through cutting-edge embedding technologies and an intuitive interface for interacting with visual content.

## Key Features

- **FastAPI**: Leverages FastAPI for asynchronous execution and automatic OpenAPI documentation.
- **Embeddings Search**: Utilize the power of CLIP embeddings for semantic search against a Qdrant vector store.
- **Dockerized Deployment**: Seamlessly deployable via Docker for efficient resource utilization, supporting both GPU and CPU.
- **Flexible Endpoints**: Offers a variety of endpoints to handle content addition and search queries effectively.
- **GPU Acceleration**: Uses CUDA-enabled functions for model acceleration and efficient video processing.

## Quick Start Guide

### Local Development

1. **Clone the Repository**:
   ```bash
   git clone <repo> && cd ExtractionPipeline/api
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   Copy `.env.sample` to `.env` and update configuration as needed.

5. **Start Development Server**:
   ```bash
   ./run-dev.sh
   ```

6. **Explore via Swagger UI**:
   Open `http://localhost:8000/api/docs` to access the API documentation.

### Docker Deployment

```bash
# Build the Docker image
docker build -t search-api .

# Run the Docker container
docker run --env-file .env -p 8000:8000 search-api
```

## API Endpoints

### Add Content

- **POST /add-content/image/{user_id}**: Upload a single image and add it to the content library.
- **POST /add-content/image/batch/{user_id}**: Upload and process multiple images in a batch.
- **POST /add-content/video/{user_id}**: Upload videos for frame extraction and embedding generation.

### Search

- **POST /search-by/text**: Perform text-based search against stored embeddings.
- **POST /search-by/image**: Execute image-based search queries.

### User Content Search

- **POST /search-by-user-content/user-image**: Search for similar content using a user's uploaded image.
- **POST /search-by-user-content/user-video**: Use frames from a user's uploaded video to search.

### Embeddings

- **POST /get-embeddings**: Retrieve an embedding by its ID and collection.

### Root and Debug

- **GET /**: Check API health status.
- **GET /debug/settings**: Retrieve current settings being used by the API.

## Video Processing Pipeline

The video processing pipeline is a core component of this service, leveraging GPU acceleration to rapidly process and index video content. It involves several stages:

1. **Upload and Extraction**:
   - Users upload videos to a designated S3 bucket.
   - Frames are extracted locally using OpenCV and FFmpeg.

2. **Frame Upload**:
   - Extracted frames are uploaded back to S3.
   - Retry logic ensures reliability in network transmissions.

3. **Embedding Generation**:
   - GPU-accelerated processing generates embeddings for extracted frames.
   - Utilizes the CLIP model to encode high-dimensional feature vectors.

4. **Storage in Qdrant**:
   - Frame embeddings are stored in Qdrant, organized and searchable by vector similarity.

## Environment Configuration

Central configuration is handled through `config/env_config.py` and environment variables defined in `.env`. This includes specifying API authentication details, S3, and Qdrant configurations.

### Example Configuration in `.env`:

```env
API_PORT=8000
QDRANT_URL=http://localhost:6333
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

Ensure that all necessary environment variables are set for deployment.

## Testing and Development

- Use `pytest` for running tests and verifying API functionality.
- Continuous testing augmentation with pre-commit hooks is supported.
- Scripts like `run.sh` simplify the testing and deployment processes.

## Conclusion

Oriane Search API is positioned as a robust solution for connecting rich media content with semantic search functionalities, driven by advanced machine learning models. The API provides a clear, extensible platform for development and deployment in production environments.

---

© 2025 Oriane – All rights reserved.
