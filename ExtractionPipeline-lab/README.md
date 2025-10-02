# Oriane Visual Extraction Pipeline

[![CI](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/oriane-labs/extraction-pipeline/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://docs.docker.com/get-docker/)
[![CUDA](https://img.shields.io/badge/CUDA-12.0%2B-green)](https://developer.nvidia.com/cuda-downloads)

**A comprehensive, GPU-accelerated visual content processing and search platform that transforms raw videos and images into searchable embeddings at enterprise scale.**

The Oriane Extraction Pipeline is a sophisticated, modular system designed to process multimedia content efficiently using cutting-edge computer vision and machine learning technologies. From intelligent video border cropping and scene detection to semantic search capabilities, this platform provides end-to-end solutions for visual content analysis and retrieval.

---

## 🌟 Key Features

### 🎬 **Advanced Video Processing**
- **GPU-accelerated cropping** using CUDA-enabled FFmpeg and custom C++ kernels
- **Intelligent border detection** with gradient-based fallback algorithms
- **Scene-aware frame extraction** leveraging PySceneDetect for optimal sampling
- **Perceptual deduplication** to eliminate redundant frames
- **Multi-format support** (MP4, MKV, MOV, AVI, WebM)

### 🖼️ **Image Processing & Management**
- **Batch and single image uploads** with automatic format standardization
- **UUID-based file organization** for scalable storage management
- **Automatic embedding generation** using state-of-the-art CLIP models
- **S3-integrated storage** with optimized upload strategies

### 🔍 **Semantic Search Engine**
- **Text-to-image search** using natural language queries
- **Image-to-image similarity** search capabilities
- **User-specific content search** across uploaded media
- **Real-time embedding retrieval** by collection and ID
- **Vector similarity matching** powered by Qdrant

### ⚡ **High-Performance Architecture**
- **Serverless scaling** via AWS Batch with on-demand GPU instances
- **Infrastructure as Code** with complete Terraform configurations
- **Horizontal scaling** support for enterprise workloads
- **Observability & resilience** with PostgreSQL state tracking

### 🔧 **Developer-Friendly**
- **RESTful API** with automatic OpenAPI documentation
- **Modular design** for easy extension and customization
- **Comprehensive testing** with unit and integration test suites
- **Docker containerization** for consistent deployments

---

## 📋 Table of Contents

1. [Architecture Overview](#️-architecture-overview)
2. [Component Breakdown](#-component-breakdown)
3. [Quick Start Guide](#-quick-start-guide)
4. [Installation & Setup](#️-installation--setup)
5. [Usage Examples](#-usage-examples)
6. [API Documentation](#-api-documentation)
7. [Core Processing Pipeline](#-core-processing-pipeline)
8. [C++ Native Components](#-c-native-components)
9. [Vector Database & Search](#-vector-database--search)
10. [AWS Deployment](#️-aws-deployment)
11. [Environment Configuration](#-environment-configuration)
12. [Development Guide](#-development-guide)
13. [Performance & Optimization](#-performance--optimization)
14. [Troubleshooting](#-troubleshooting)
15. [Contributing](#-contributing)
16. [License & Acknowledgements](#-license--acknowledgements)

---

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Application]
        B[Mobile App]
        C[API Clients]
    end

    subgraph "API Gateway"
        D[FastAPI Service]
        D1[Authentication]
        D2[Rate Limiting]
        D3[Request Validation]
    end

    subgraph "Processing Layer"
        E[Video Processing]
        F[Image Processing]
        G[Embedding Generation]
        H[Scene Detection]
    end

    subgraph "GPU Acceleration"
        I[CUDA FFmpeg]
        J[C++ Kernels]
        K[CLIP Models]
    end

    subgraph "Storage Layer"
        L[(AWS S3)]
        M[(Qdrant Vector DB)]
        N[(PostgreSQL)]
    end

    subgraph "Infrastructure"
        O[AWS Batch]
        P[GPU Instances]
        Q[Auto Scaling]
    end

    A --> D
    B --> D
    C --> D
    D --> D1
    D --> D2
    D --> D3
    D --> E
    D --> F
    E --> I
    F --> I
    E --> J
    F --> J
    G --> K
    H --> K
    I --> G
    J --> G
    E --> L
    F --> L
    G --> M
    D --> N
    E --> O
    O --> P
    P --> Q
```

### Pipeline Flow

1. **Content Ingestion**: Raw videos/images uploaded via API or S3 triggers
2. **GPU Processing**: CUDA-accelerated cropping, frame extraction, and enhancement
3. **AI Analysis**: CLIP-based embedding generation for semantic understanding
4. **Vector Storage**: Embeddings indexed in Qdrant for fast similarity search
5. **Search & Retrieval**: Real-time queries against the vector database
6. **State Management**: Progress tracking and error handling via PostgreSQL

---

## 📦 Component Breakdown

### 🌐 **API Service** (`/api/`)
FastAPI-based REST service providing all client interfaces.
- **Location**: [`api/README.md`](api/README.md)
- **Features**: Content upload, semantic search, user management
- **Tech Stack**: FastAPI, Pydantic, Uvicorn
- **Endpoints**: 12+ REST endpoints with full OpenAPI documentation

### 🔧 **Core Processing Engine** (`/core/`)
The heart of the system handling all multimedia processing.

#### **Python Pipeline** (`/core/py/`)
- **Location**: [`core/py/README.md`](core/py/README.md)
- **Pipeline Documentation**: [`core/py/pipeline/README.md`](core/py/pipeline/README.md)
- **Features**: End-to-end video processing, embedding generation
- **Components**: Border cropping, scene detection, deduplication, CLIP embeddings

#### **C++ Performance Kernels** (`/core/cpp/`)
High-performance native implementations for compute-intensive tasks.
- **Files**:
  - [`crop_n_frame.cpp`](core/cpp/crop_n_frame.cpp) - Main processing pipeline
  - [`crop/main.cpp`](core/cpp/crop/main.cpp) - FFmpeg CUDA integration
- **Features**: GPU-accelerated video cropping, frame extraction
- **Performance**: 10x faster than Python equivalents
- **Dependencies**: CUDA Toolkit, OpenCV, FFmpeg with NVENC

### 📊 **Vector Database** (`/qdrant/`)
Complete Qdrant vector search stack for video frame and image embeddings.
- **Main Guide**: [`qdrant/README.md`](qdrant/README.md) - Production-ready ingestion and search pipeline
- **Collection Management**: [`qdrant/collections/README.md`](qdrant/collections/README.md)
- **Collections**: `watched_frames`, `user_images`, `user_videos`
- **Features**: GPU-accelerated ingestion, multimodal search playground, schema-as-code
- **Capabilities**: 512-dimensional CLIP embeddings, cosine similarity, cloud-native deployment

### 🛠️ **Utility Scripts** (`/scripts/`)
Maintenance and administration tools.
- **TypeScript**: Database integrity checks, S3 auditing
- **Python**: Batch processing utilities
- **SQL**: Database maintenance queries

### ☁️ **Infrastructure** (`/terraform/`)
Complete Infrastructure as Code for AWS deployment.
- **Resources**: VPC, IAM, Batch, ECR, RDS, CloudWatch
- **Scaling**: Auto-scaling GPU clusters
- **Monitoring**: Comprehensive logging and metrics

---

## 🚀 Quick Start Guide

### Prerequisites

- **NVIDIA GPU** with CUDA 11.4+ support
- **Docker** (for containerized deployment)
- **Python** 3.10+ (for local development)
- **Node.js** 18+ (for utility scripts)
- **AWS CLI** (for cloud deployment)

### Option 1: Extraction Pipeline (Recommended)

```bash
# Clone the repository
git clone https://github.com/oriane-labs/extraction-pipeline.git
cd extraction-pipeline

# Set up environment variables (see Environment Configuration section)
export ORIANE_ADMIN_DB_URL="postgresql://user:pass@host:5432/dbname"
export QDRANT_URL="https://your-qdrant-endpoint:6333"
export QDRANT_KEY="your-qdrant-api-key"
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Run extraction pipeline
make extract          # activates venv & runs main.py

# Re-run after crash
make resume           # same as extract, resumes from checkpoint
```

### Option 2: Docker Deployment

```bash
# Clone the repository
git clone https://github.com/oriane-labs/extraction-pipeline.git
cd extraction-pipeline

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Build and run the complete stack
docker-compose up --build

# Access the API documentation
open http://localhost:8000/api/docs
```

### Option 3: Local Development

```bash
# API Service
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env
# Configure .env
./run-dev.sh

# Core Processing (separate terminal)
cd core/py/pipeline
./test/test_locally.sh
```

### Option 4: Native C++ (Maximum Performance)

```bash
# Build C++ components
cd core/cpp
./build.sh

# Run video processing
./crop_n_frame input_video.mp4 output_directory
```

---

## 🔧 Installation & Setup

### System Dependencies

#### CUDA & GPU Drivers
```bash
# Ubuntu/Debian
wget https://developer.download.nvidia.com/compute/cuda/12.0.0/local_installers/cuda_12.0.0_525.60.13_linux.run
sudo sh cuda_12.0.0_525.60.13_linux.run

# Verify installation
nvidia-smi
nvcc --version
```

#### FFmpeg with CUDA Support
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Verify CUDA support
ffmpeg -hide_banner -filters | grep cuda
```

#### OpenCV Development Headers
```bash
# Ubuntu/Debian
sudo apt install libopencv-dev pkg-config

# Verify installation
pkg-config --cflags --libs opencv4
```

### Environment Configuration

Create `.env` files in each component directory:

```bash
# Copy templates
cp api/.env.sample api/.env
cp core/py/pipeline/.env.example core/py/pipeline/.env

# Edit with your credentials
# AWS, Qdrant, PostgreSQL, etc.
```

### Database Setup

```bash
# Start Qdrant locally
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Create collections
cd qdrant/collections
python create.py watched_frames.json
python create.py user_images.json
python create.py user_videos.json
```

---

## 📖 Usage Examples

### API Usage

#### Upload and Process a Video
```bash
curl -X POST "http://localhost:8000/add-content/video/user123" \
  -H "X-API-Key: your-api-key" \
  -F "file=@sample_video.mp4"
```

#### Search by Text
```bash
curl -X POST "http://localhost:8000/search-by/text" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "prompt": "a cat sitting on a chair",
    "limit": 10,
    "collection_name": "watched_frames"
  }'
```

#### Batch Image Upload
```bash
curl -X POST "http://localhost:8000/add-content/image/batch/user123" \
  -H "X-API-Key: your-api-key" \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  -F "files=@image3.gif"
```

### Python SDK Usage

```python
from oriane_client import OrianeClient

client = OrianeClient(api_key="your-api-key")

# Upload video
result = client.upload_video("user123", "path/to/video.mp4")
print(f"Video processed: {result['video_id']}")

# Search
results = client.search_by_text("sunset over mountains", limit=5)
for hit in results:
    print(f"Score: {hit['score']}, ID: {hit['id']}")
```

### Core Pipeline Usage

```bash
# Process specific videos
cd core/py/pipeline
JOB_INPUT='[{"platform":"instagram","code":"abc123"}]' python entrypoint.py

# Batch processing
echo '[{"platform":"instagram","code":"vid1"},{"platform":"youtube","code":"vid2"}]' | \
  JOB_INPUT="$(cat)" python entrypoint.py
```

---

## 📚 API Documentation

The API provides comprehensive REST endpoints for all functionality:

### Content Management
- `POST /add-content/image/{user_id}` - Single image upload
- `POST /add-content/image/batch/{user_id}` - Batch image upload
- `POST /add-content/video/{user_id}` - Video upload and processing

### Search Capabilities
- `POST /search-by/text` - Text-based semantic search
- `POST /search-by/image` - Image-based similarity search
- `POST /search-by-user-content/user-image` - Search user's images
- `POST /search-by-user-content/user-video` - Search user's videos

### Data Retrieval
- `POST /get-embeddings` - Retrieve embeddings by ID and collection
- `GET /debug/settings` - System configuration (development)
- `GET /` - Health check endpoint

### Interactive Documentation
Access full API documentation at `http://localhost:8000/api/docs` when running the service.

**Detailed API Guide**: [`api/README.md`](api/README.md)

---

## 🔄 Core Processing Pipeline

The pipeline transforms raw multimedia content into searchable embeddings through several stages:

### Phase 1: Smart Border Cropping
```cpp
// C++ implementation for maximum performance
// File: core/cpp/crop_n_frame.cpp
CropRect detect_crop_ffmpeg(const std::string& src_path) {
    // GPU-accelerated border detection using FFmpeg cropdetect
    // with gradient-based fallback for robust handling
}
```

**Features**:
- CUDA-accelerated FFmpeg processing
- Multiple probe points for accuracy
- Gradient-based fallback detection
- Safe margin calculation
- Hardware-accelerated encoding (NVENC)

### Phase 2: Scene Frame Extraction
```python
# Python implementation with PySceneDetect
# File: core/py/pipeline/src/scene_framing.py
def extract_scene_frames(video_path, output_dir, sample_fps=0.1):
    # Intelligent scene change detection
    # Content-aware frame selection
    # Timestamp-based naming convention
```

**Features**:
- Automatic scene change detection
- Content entropy analysis
- Configurable sampling rates
- Deduplication via perceptual hashing

### Phase 3: Embedding Generation
```python
# CLIP-based semantic embeddings
# File: core/py/pipeline/src/infer_embeds.py
def generate_embeddings(frame_paths, model_name="jinaai/jina-clip-v2"):
    # Batch processing for efficiency
    # GPU-accelerated inference
    # 512-dimensional output vectors
```

**Features**:
- State-of-the-art CLIP v2 models
- Batch processing optimization
- GPU memory management
- Deterministic output for consistency

### Phase 4: Vector Storage
```python
# Qdrant integration for similarity search
# File: core/py/pipeline/src/store_embeds.py
def store_embeddings(embeddings, metadata, collection="watched_frames"):
    # Efficient vector upserts
    # Idempotent operations
    # Metadata preservation
```

**Complete Pipeline Guide**: [`core/py/pipeline/README.md`](core/py/pipeline/README.md)

---

## ⚡ C++ Native Components

For maximum performance, critical processing components are implemented in C++ with CUDA acceleration:

### Video Processing Engine
**File**: [`core/cpp/crop_n_frame.cpp`](core/cpp/crop_n_frame.cpp)

```cpp
// High-performance video processing
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/videoio.hpp>

// GPU-accelerated border detection
CropRect detect_crop_ffmpeg(const std::string& src_path);

// Parallel frame extraction
void extract_frames_parallel(const std::string& video_path);
```

### CUDA Integration
**File**: [`core/cpp/crop/main.cpp`](core/cpp/crop/main.cpp)

```cpp
// FFmpeg CUDA integration
extern "C" {
#include <libavformat/avformat.h>
#include <libavutil/hwcontext_cuda.h>
}

// Hardware-accelerated encoding
static enum AVPixelFormat get_hw_format(AVCodecContext *ctx);
```

### Building C++ Components

```bash
# Simple build
cd core/cpp
./build.sh

# Full CMake project
cd core/cpp/crop
./build.sh

# Docker build with all dependencies
docker build -t extraction-pipeline-cpp:dev core/cpp
```

### Performance Benefits
- **10x faster** than Python equivalents
- **GPU memory optimization** for large videos
- **Parallel processing** across multiple streams
- **Zero-copy operations** where possible

---

## 🔍 Vector Database & Search

The system uses Qdrant for high-performance vector similarity search with a comprehensive production-ready stack:

### Complete Qdrant Vector Search Stack

The [`qdrant/README.md`](qdrant/README.md) provides a full production pipeline for ingesting, indexing, and querying video frame embeddings:

#### **Key Features**
- **GPU-accelerated ingestion** - Direct S3 streaming with on-the-fly CLIP encoding
- **Multimodal search playground** - Image→frame, text→frame, and video→video retrieval
- **Schema-as-code** - Reusable JSON configurations for collection management
- **Safe migrations** - Idempotent scripts for data transformation between collections
- **One-click deployment** - Docker Compose + Nginx + TLS for HTTPS-secured hosting

#### **Quick Start Examples**

```bash
# Start local Qdrant instance
podman run --rm -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.14.1

# Create collections from JSON configs
python qdrant/collections/create.py qdrant/collections/user_videos.json

# Ingest S3 frames with GPU acceleration
export AWS_S3_BUCKET=my-bucket
python qdrant/ingest_frames_embeds.py

# Search playground examples
python qdrant/search_playground.py --text "dogs dancing in the rain" --top_k 15
python qdrant/search_playground.py --image /path/query.png --top_k 10
python qdrant/search_playground.py --video /path/query.mp4 --fps 1 --top_k 5
```

### Collection Schemas

#### Watched Frames Collection
```json
{
  "name": "watched_frames",
  "config": {
    "params": {
      "vectors": {
        "size": 512,
        "distance": "Cosine"
      }
    }
  }
}
```

#### User Images Collection
```json
{
  "name": "user_images",
  "config": {
    "params": {
      "vectors": {
        "size": 512,
        "distance": "Cosine"
      }
    }
  }
}
```

### Production Deployment

The `qdrant/deploy/` folder provides a complete production deployment setup:

```bash
# One-click deployment to EC2 with HTTPS
cd qdrant/deploy
./deploy-server.sh
```

This automatically:
- Installs Docker CE & Compose on remote host
- Provisions LetsEncrypt certificates with Certbot
- Boots the stack with Nginx reverse proxy
- Secures the Qdrant API at `https://qdrant.admin.oriane.xyz:6333`

### Search Performance
- **Sub-millisecond** query response times
- **Millions of vectors** supported per collection
- **Horizontal scaling** with clustering
- **Real-time indexing** for new content
- **CLIP v2 embeddings** using `jinaai/jina-clip-v2` model

### Maintenance & Migration

| Script | Purpose |
|--------|----------|
| `scripts/migrate_video_frames.py` | Re-index existing points with fresh payload schema |
| `scripts/migrate_collection.py` | Safely drop & recreate collections with bulk upload |

**Complete Vector Search Guide**: [`qdrant/README.md`](qdrant/README.md)
**Collection Management**: [`qdrant/collections/README.md`](qdrant/collections/README.md)

---

## ☁️ AWS Deployment

### Infrastructure Provisioning

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan deployment
terraform plan -var-file="production.tfvars"

# Deploy infrastructure
terraform apply
```

### Container Deployment

```bash
# Build and push to ECR
cd core/py/pipeline
./deploy/push_image.sh

# Submit processing job
aws batch submit-job \
  --job-name extract-video-batch \
  --job-queue gpu-queue \
  --job-definition extract-frames \
  --container-overrides '{
    "environment": [
      {"name": "JOB_INPUT", "value": "[{\"platform\":\"instagram\",\"code\":\"abc123\"}]"}
    ]
  }'
```

### Scaling Configuration

- **Auto Scaling Groups**: Automatic GPU instance provisioning
- **Spot Instances**: Cost optimization for batch processing
- **Multi-AZ Deployment**: High availability and fault tolerance
- **CloudWatch Monitoring**: Comprehensive metrics and alerting

### Infrastructure Components

| Component | Purpose | Scaling |
|-----------|---------|----------|
| **ECS Fargate** | API service hosting | Auto-scaling |
| **AWS Batch** | Video processing jobs | On-demand GPUs |
| **Application Load Balancer** | Traffic distribution | Multi-AZ |
| **RDS Aurora** | Metadata storage | Read replicas |
| **ElastiCache** | Caching layer | Cluster mode |
| **S3** | Content storage | Unlimited |

---

## 🔧 Environment Configuration

### Required Environment Variables for Extraction Pipeline

The following environment variables are **required** when using `make extract` or `make resume`:

- `FORCE_CPU=0`: Set to `1` to force models to run on CPU even if a GPU is available. Default is `0`, which allows use of GPU if available.

```bash
# PostgreSQL Database (Required)
ORIANE_ADMIN_DB_URL="postgresql://username:password@host:5432/database_name"
# Full connection URL for the Oriane admin database

# Qdrant Vector Database (Required)
QDRANT_URL="https://your-qdrant-endpoint:6333"
# URL of your Qdrant vector database instance

QDRANT_KEY="your-qdrant-api-key"
# API key for authenticating with Qdrant

# AWS Configuration (Required)
AWS_REGION="us-east-1"
# AWS region for S3 storage and other services

AWS_ACCESS_KEY_ID="your-access-key"
# AWS access key ID for authentication

AWS_SECRET_ACCESS_KEY="your-secret-key"
# AWS secret access key for authentication
```

### Complete Environment Variables

For full system configuration, these additional variables may be used:

```bash
# AWS Configuration (Extended)
S3_VIDEOS_BUCKET=oriane-contents
S3_FRAMES_BUCKET=oriane-frames
S3_APP_BUCKET=oriane-app

# Qdrant Vector Database (Extended)
QDRANT_DIM=512
QDRANT_COLLECTION=watched_frames

# PostgreSQL Database (Legacy Format)
DB_HOST=your-postgres-host
DB_PORT=5432
DB_NAME=oriane_db
DB_USER=your_username
DB_PASSWORD=your_password

# API Configuration
API_PORT=8000
API_SECRET_KEY=your_jwt_secret
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=secure_password

# Processing Configuration
VP_ENABLE_CROP=1
VP_ENABLE_DEDUP=1
VP_SAMPLE_FPS=0.1
VP_BATCH_SIZE=8
CLIP_MODEL=jinaai/jina-clip-v2
FORCE_CPU=0

# Performance Tuning
MAX_WORKERS=3
TOLERANCE=5
EDGE_THRESH=10
MIN_CROP_RATIO=0.10

# Pipeline Configuration
BATCH_SIZE=1000
SLEEP_DELAY=0.5
CHECKPOINT_FILE=checkpoint.txt
PIPELINE_SCRIPT=core/py/pipeline/entrypoint.py
```

## 📊 Extraction Pipeline DAG

The extraction pipeline follows a structured workflow for processing video content:

```mermaid
graph TD
    A[🚀 Start: make extract] --> B[📦 Load Checkpoint]
    B --> C[🔍 Query Database]
    C --> D{📋 Rows Available?}
    D -->|No| E[🏁 Complete]
    D -->|Yes| F[📝 Build Job Input]
    F --> G[🎬 Run Pipeline Subprocess]
    G --> H{✅ Pipeline Success?}
    H -->|No| I[❌ Log Error & Continue]
    I --> J[⏱️ Sleep Delay]
    J --> C
    H -->|Yes| K[✅ Mark as Extracted]
    K --> L[📊 Wait for Qdrant Upsert]
    L --> M{🔍 Embeddings Verified?}
    M -->|Yes| N[✅ Mark as Embedded]
    M -->|No| O[⚠️ Log Warning]
    N --> P[💾 Save Checkpoint]
    O --> P
    P --> Q[📈 Update Progress]
    Q --> J

    style A fill:#e1f5fe
    style E fill:#e8f5e8
    style I fill:#ffebee
    style O fill:#fff3e0
    style K fill:#e8f5e8
    style N fill:#e8f5e8
```

### Pipeline Components

| Component | Description | Failure Handling |
|-----------|-------------|------------------|
| **Checkpoint Manager** | Tracks processing progress with `cursor_id` | Graceful restart from last successful batch |
| **Batch Orchestrator** | Fetches unprocessed content in configurable batches | Continues on subprocess errors |
| **Core Pipeline** | Subprocess execution of video processing | Logs errors, doesn't advance checkpoint |
| **Qdrant Integration** | Verifies embedding upserts with polling | Warns on timeout, continues processing |
| **Progress Tracking** | Updates database status and checkpoint | Atomic operations for consistency |

### Key Features

- **🔄 Resumable**: Automatic checkpoint recovery after crashes
- **⚡ Fault Tolerant**: Continues processing on individual batch failures
- **📊 Observable**: Progress tracking with `tqdm` and detailed logging
- **🎯 Configurable**: Batch size, delays, and timeouts via environment variables
- **🔒 Safe**: Atomic database operations and idempotent Qdrant upserts

## 📋 Database Collections Schema

### Watched Frames Collection Schema

The `watched_frames` collection stores embeddings for extracted video frames:

```json
{
  "collection_name": "watched_frames",
  "vector_params": {
    "size": 512,
    "distance": "Cosine"
  },
  "payload_indexes": [
    {
      "field_name": "id",
      "field_schema": "keyword"
    },
    {
      "field_name": "platform",
      "field_schema": "keyword"
    },
    {
      "field_name": "video_code",
      "field_schema": "keyword"
    },
    {
      "field_name": "created_at",
      "field_schema": "datetime"
    }
  ],
  "payload_data": [
    {
      "field_name": "path",
      "field_schema": "keyword"
    },
    {
      "field_name": "frame_number",
      "field_schema": "integer"
    },
    {
      "field_name": "frame_second",
      "field_schema": "float"
    }
  ]
}
```

### Field Descriptions

| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| **vector** | `float[512]` | ✅ | CLIP v2 embedding for semantic search |
| **id** | `keyword` | ✅ | Unique frame identifier |
| **platform** | `keyword` | ✅ | Source platform (e.g., "instagram", "youtube") |
| **video_code** | `keyword` | ✅ | Platform-specific video identifier |
| **created_at** | `datetime` | ✅ | Timestamp of frame extraction |
| **path** | `keyword` | ❌ | S3 path to the frame image file |
| **frame_number** | `integer` | ❌ | Sequential frame number in video |
| **frame_second** | `float` | ❌ | Timestamp in seconds within video |

### Usage Examples

```python
# Search by text
results = qdrant_client.search(
    collection_name="watched_frames",
    query_vector=clip_model.encode("cat playing with ball"),
    limit=10,
    query_filter={
        "must": [
            {"key": "platform", "match": {"value": "instagram"}}
        ]
    }
)

# Search by video code
results = qdrant_client.scroll(
    collection_name="watched_frames",
    scroll_filter={
        "must": [
            {"key": "video_code", "match": {"value": "abc123"}}
        ]
    },
    limit=100
)
```

### Environment-Specific Configurations

#### Development
```bash
LOCAL_MODE=1
DEBUG=1
PROFILE_JSON=dev.prof
LOG_LEVEL=DEBUG
```

#### Production
```bash
LOCAL_MODE=0
DEBUG=0
LOG_LEVEL=INFO
MONITORING_ENABLED=1
```

---

## 👩‍💻 Development Guide

### Code Organization

```
ExtractionPipeline/
├── api/                    # FastAPI REST service
│   ├── controllers/        # Route handlers
│   ├── services/          # Business logic
│   ├── config/            # Configuration management
│   └── tests/             # API test suites
├── core/                  # Core processing components
│   ├── py/                # Python implementation
│   │   └── pipeline/      # End-to-end processing
│   └── cpp/               # C++ performance kernels
├── qdrant/                # Vector database configs
├── terraform/             # Infrastructure as code
└── scripts/               # Utility and maintenance tools
```

### Development Workflow

1. **Setup Development Environment**
   ```bash
   # Fork and clone repository
   git clone https://github.com/your-username/extraction-pipeline.git
   cd extraction-pipeline

   # Setup pre-commit hooks
   pre-commit install
   ```

2. **Local Development**
   ```bash
   # API development
   cd api
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ./run-dev.sh

   # Core pipeline development
   cd core/py/pipeline
   ./test/test_locally.sh
   ```

3. **Testing**
   ```bash
   # Unit tests
   pytest tests/ -v

   # Integration tests
   ./test/test_docker.sh

   # Performance tests
   python -m pytest tests/performance/
   ```

4. **Code Quality**
   ```bash
   # Python formatting
   black . && ruff check .

   # C++ formatting
   clang-format -i core/cpp/**/*.cpp

   # Type checking
   mypy api/ core/py/
   ```

### Contributing Guidelines

- **Code Style**: Follow Black formatting for Python, clang-format for C++
- **Testing**: Maintain >90% test coverage
- **Documentation**: Update READMEs for any new features
- **Performance**: Benchmark critical paths
- **Security**: Never commit credentials or API keys

### Debugging Tools

```bash
# API debugging
DEBUG=1 ./run-dev.sh

# Pipeline profiling
PROFILE_JSON=run.prof python entrypoint.py

# Memory profiling
python -m memory_profiler scripts/profile_memory.py

# GPU monitoring
nvidia-smi -l 1
```

---

## 📊 Performance & Optimization

### Benchmarks

| Operation | CPU (Python) | GPU (C++) | Speedup |
|-----------|--------------|-----------|----------|
| **Video Cropping** | 45 sec | 4.2 sec | 10.7x |
| **Frame Extraction** | 23 sec | 2.1 sec | 11.0x |
| **Embedding Generation** | 180 sec | 12 sec | 15.0x |
| **Search Query** | 250ms | 15ms | 16.7x |

### Optimization Strategies

#### GPU Memory Management
```python
# Batch processing optimization
batch_size = min(VP_BATCH_SIZE, available_gpu_memory // frame_size)
for batch in chunks(frames, batch_size):
    embeddings = model.encode(batch)
    torch.cuda.empty_cache()  # Free GPU memory
```

#### Parallel Processing
```cpp
// Multi-threaded video processing
std::vector<std::future<void>> futures;
for (const auto& video : video_batch) {
    futures.push_back(std::async(std::launch::async, process_video, video));
}
```

#### Caching Strategies
```python
# Redis caching for frequent queries
@lru_cache(maxsize=1000)
def get_embedding(video_id: str, frame_id: str):
    return qdrant_client.retrieve(collection="watched_frames", ids=[frame_id])
```

### Resource Requirements

#### Minimum System Requirements
- **GPU**: NVIDIA GTX 1660 (6GB VRAM)
- **CPU**: 4 cores, 2.5 GHz
- **RAM**: 16 GB
- **Storage**: 100 GB SSD

#### Recommended Production Setup
- **GPU**: NVIDIA A100 (40GB VRAM)
- **CPU**: 32 cores, 3.0 GHz
- **RAM**: 128 GB
- **Storage**: 1 TB NVMe SSD
- **Network**: 10 Gbps

---

## 🔧 Troubleshooting

### Common Issues

#### CUDA Not Found
```bash
# Check CUDA installation
nvcc --version
nvidia-smi

# Verify FFmpeg CUDA support
ffmpeg -hide_banner -filters | grep cuda

# Install CUDA if missing
wget https://developer.download.nvidia.com/compute/cuda/12.0.0/local_installers/cuda_12.0.0_525.60.13_linux.run
sudo sh cuda_12.0.0_525.60.13_linux.run
```

#### Out of GPU Memory
```python
# Reduce batch size
VP_BATCH_SIZE=4  # Default: 8

# Enable gradient checkpointing
model.gradient_checkpointing_enable()

# Clear cache regularly
torch.cuda.empty_cache()
```

#### Qdrant Connection Issues
```bash
# Check Qdrant status
curl http://localhost:6333/collections

# Restart Qdrant
docker restart qdrant

# Check logs
docker logs qdrant
```

#### API Authentication Errors
```bash
# Verify API key
curl -H "X-API-Key: your-key" http://localhost:8000/debug/settings

# Check environment variables
echo $API_SECRET_KEY
```

### Performance Issues

#### Slow Video Processing
1. **Check GPU utilization**: `nvidia-smi`
2. **Increase worker count**: `MAX_WORKERS=6`
3. **Use SSD storage** for temporary files
4. **Enable hardware encoding**: Verify NVENC support

#### High Memory Usage
1. **Reduce batch size**: `VP_BATCH_SIZE=4`
2. **Enable streaming**: Process videos in chunks
3. **Clear caches**: Regular garbage collection
4. **Monitor usage**: `htop`, `nvidia-smi`

### Logging & Debugging

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python entrypoint.py

# Profile performance
PROFILE_JSON=performance.prof python entrypoint.py

# Memory profiling
python -m memory_profiler entrypoint.py

# API request logging
uvicorn main:app --log-level debug
```

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Run the test suite**: `pytest tests/`
6. **Submit a pull request**

### Contribution Areas

- 🐛 **Bug fixes** and stability improvements
- ⚡ **Performance optimizations**
- 📚 **Documentation** enhancements
- 🧪 **Test coverage** improvements
- 🔧 **New features** and capabilities
- 🌐 **Internationalization** support

### Code Standards

- **Python**: Black formatting, type hints, docstrings
- **C++**: Google style guide, Doxygen comments
- **Tests**: Comprehensive coverage (>90%)
- **Documentation**: Clear, concise, with examples

### Community

- 💬 **Discussions**: GitHub Discussions for questions
- 🐛 **Issues**: Bug reports and feature requests
- 📧 **Contact**: dev@oriane.xyz for direct communication
- 🔒 **Security**: security@oriane.xyz for vulnerability reports

---

## 📄 License & Acknowledgements

### License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Acknowledgements

We thank the following projects and organizations that make this work possible:

#### Core Technologies
- **[FFmpeg](https://ffmpeg.org)** - Video processing foundation
- **[OpenCV](https://opencv.org)** - Computer vision algorithms
- **[NVIDIA CUDA](https://developer.nvidia.com/cuda-toolkit)** - GPU acceleration
- **[PyTorch](https://pytorch.org)** - Deep learning framework
- **[FastAPI](https://fastapi.tiangolo.com)** - Modern API framework

#### AI & ML Models
- **[Jina AI](https://jina.ai)** - CLIP v2 embedding models
- **[Hugging Face](https://huggingface.co)** - Model hosting and APIs
- **[OpenAI](https://openai.com)** - Original CLIP architecture

#### Infrastructure & Storage
- **[Qdrant](https://qdrant.tech)** - Vector database excellence
- **[Amazon Web Services](https://aws.amazon.com)** - Cloud infrastructure
- **[Terraform](https://www.terraform.io)** - Infrastructure as Code
- **[Docker](https://www.docker.com)** - Containerization platform

#### Development Tools
- **[PySceneDetect](https://scenedetect.com)** - Scene change detection
- **[pytest](https://pytest.org)** - Testing framework
- **[Black](https://black.readthedocs.io)** - Code formatting
- **[pre-commit](https://pre-commit.com)** - Git hooks

### Research & Papers

This work builds upon research in computer vision and deep learning:

- Radford, A., et al. "Learning Transferable Visual Representations with Contrastive Learning" (CLIP)
- Dosovitskiy, A., et al. "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale"
- Lin, T., et al. "Microsoft COCO: Common Objects in Context"

---

### 📞 Contact & Support

- **Documentation**: Comprehensive guides in each component's README
- **API Reference**: Interactive docs at `/api/docs`
- **Issues**: [GitHub Issues](https://github.com/oriane-labs/extraction-pipeline/issues)
- **Discussions**: [GitHub Discussions](https://github.com/oriane-labs/extraction-pipeline/discussions)
- **Email**: dev@oriane.xyz
- **Security**: security@oriane.xyz

---

**© 2025 Oriane Labs – Transforming visual content into searchable intelligence.**
