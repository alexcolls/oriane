# ✨ Oriane

> AI-powered visual search and content monitoring platform for Instagram and social media

## 🌟 Overview

Oriane is a comprehensive platform for AI-driven visual search, content monitoring, and social media analytics. It combines computer vision, deep learning, and distributed systems to enable semantic search across video content, frame-by-frame analysis, and real-time content acquisition from Instagram.

## 📋 Table of Contents

- [Core Applications](#-core-applications)
- [AI & Processing Services](#-ai--processing-services)
- [Lambda Functions](#-lambda-functions)
- [AI Models](#-ai-models)
- [Infrastructure & DevOps](#-infrastructure--devops)
- [Legacy & Experimental](#-legacy--experimental)

---

## 🚀 Core Applications

### Web Applications

#### **OrianeApp-nuxt** 🎨
Main user-facing web application built with Nuxt.js (Vue 3). Provides the primary interface for visual search, content browsing, and user interactions.
- **Tech**: Nuxt 3, Vue 3, TypeScript
- **Features**: Visual search UI, content gallery, user authentication

#### **OrianeAdmin-nestjs** ⚙️
Comprehensive admin backend API built with NestJS. Manages all platform operations, user management, content acquisition, and AI job orchestration.
- **Tech**: NestJS, TypeScript, TypeORM, PostgreSQL
- **Features**: User management, content pipeline control, AI job scheduling, handle monitoring

#### **OrianeAdmin-react** 📊
React-based admin dashboard for platform management and monitoring.
- **Tech**: React, TypeScript
- **Features**: Admin controls, analytics, system monitoring

### Search & Core APIs

#### **OrianeSearch-fastapi** 🔍
High-performance vector search API for semantic visual search across video frames.
- **Tech**: FastAPI, Python, Qdrant
- **Features**: Multi-modal search (image + text), vector similarity, frame retrieval

#### **OrianePipeline-fastapi** 🔄
Content processing pipeline orchestrator managing the end-to-end flow from video ingestion to indexed frames.
- **Tech**: FastAPI, Python, AWS services
- **Features**: Pipeline management, status tracking, error handling

#### **OrianeVectorDB-qdrant** 💾
Qdrant vector database configuration and setup for storing and querying frame embeddings.
- **Tech**: Qdrant, Docker
- **Features**: Vector storage, similarity search, collection management

### SDK & Libraries

#### **OrianeExtractionSDK-python** 📦
Python SDK for frame extraction and processing operations. Provides reusable components for video analysis.
- **Tech**: Python, OpenCV, FFmpeg
- **Features**: Frame extraction, video processing utilities, common operations

---

## 🤖 AI & Processing Services

### Core AI

#### **OrianeCoreAI-python** 🧠
Core AI services for embeddings extraction, model inference, and visual analysis.
- **Tech**: Python, PyTorch, Transformers
- **Features**: Multi-modal embeddings (CLIP), frame analysis, model serving

#### **OrianeCoreAI-mojo** ⚡
High-performance AI inference implementation in Mojo for optimized model serving.
- **Tech**: Mojo
- **Status**: Experimental

### Processing ETLs

#### **orn-processor-etls** 🔧
End-to-end ETL pipeline for video processing:
1. **01_video-cropper**: Crops videos to square format
2. **02_video-to-frames**: Extracts frames from videos
3. **03_frames-to-embeddings**: Generates embeddings from frames
- **Tech**: Python, Poetry, AWS Batch
- **Features**: Distributed processing, error recovery, monitoring

#### **EmbeddingsExtraction** 🎯
Production-ready reference implementation for multi-modal embeddings extraction using Jina-CLIP v2.
- **Tech**: Python, Jina-CLIP, Docker
- **Features**: Image & text embeddings, batch processing

#### **ExtractionPipeline-lab** 🧪
Experimental visual extraction pipeline for testing new approaches and models.
- **Tech**: Python 3.10+
- **Status**: Laboratory/Testing

---

## ⚡ Lambda Functions

### Content Acquisition

#### **InstagramContentCollector-lambda** 📸
Automates Instagram content collection for monitored accounts.
- **Tech**: Python, AWS Lambda, Instagram API
- **Features**: Content scraping, handle monitoring, scheduling

#### **InstagramVideoDownloader-lambda** 📥
Downloads Instagram videos for processing.
- **Tech**: Python, AWS Lambda, S3

#### **InstagramVideoDownloaderBulk-lambda** 📦
Bulk video downloader for batch processing of Instagram content.
- **Tech**: Python, AWS Lambda, SQS

### Video Processing

#### **VideoCropper-lambda** ✂️
Crops videos to square format (1:1 aspect ratio) for consistent processing.
- **Tech**: Python, AWS Lambda, FFmpeg

#### **VideoFramesExtractor-lambda** 🎞️
Extracts frames from videos at specified intervals (default: 1 frame/second).
- **Tech**: Node.js, AWS Lambda, FFmpeg
- **Storage**: S3 (oriane-videos → oriane-frames)

#### **VideoFramesExtractorBulk-lambda** 🎬
Bulk frame extraction service for processing multiple videos.
- **Tech**: Node.js, AWS Lambda

#### **VideoFramesSceneExtractor-lambda** 🎭
Intelligent scene-based frame extraction using scene detection algorithms.
- **Tech**: Python, AWS Lambda, PySceneDetect
- **Features**: Scene change detection, key frame extraction

### AI Analysis

#### **FramesEmbeddingsExtractor-lambda** 🔢
Generates vector embeddings for extracted frames using AI models.
- **Tech**: Python, AWS Lambda, PyTorch
- **Models**: CLIP, ViT

#### **FrameComparisonModel-lambda** 🔬
Compares frames for similarity and duplicate detection.
- **Tech**: Python, AWS Lambda

#### **FramesComparer-lambda** 📊
Advanced frame comparison service with multiple similarity metrics.
- **Tech**: Python, AWS Lambda

---

## 🎨 AI Models

### Vision Models

#### **ViT-model** 👁️
Vision Transformer (ViT) model for image understanding and feature extraction.
- **Tech**: PyTorch, Transformers
- **Use**: Frame analysis, visual features

#### **ViT_SAM-model** 🎯
Segment Anything Model (SAM) with ViT backbone for object segmentation.
- **Tech**: PyTorch, SAM
- **Model Size**: ~2.6GB
- **Use**: Object detection, segmentation

#### **SAM-model** 🖼️
Standalone Segment Anything Model implementation.
- **Tech**: PyTorch

#### **SSCD-model** 🔐
Self-Supervised Copy Detection model for identifying duplicate/similar content.
- **Tech**: PyTorch
- **Use**: Content deduplication, copyright detection

---

## 🛠️ Infrastructure & DevOps

### Infrastructure as Code

#### **OrianeInfra-bash** 🏗️
Infrastructure management scripts and configurations.
- **Tech**: Bash, Docker, Kubernetes
- **Components**:
  - Qdrant setup (dev/prod environments)
  - EKS configurations
  - K8s deployments

#### **OrianeDevOpsCLI-bash** 🔧
DevOps CLI tools for deployment, monitoring, and maintenance.
- **Tech**: Bash
- **Features**: Deployment automation, log management

#### **ec2** ☁️
EC2 instance configurations and management scripts.
- **Tech**: AWS EC2, Bash

### Build & Compilation

#### **opencv-cuda** 🎥
Custom OpenCV build with CUDA support for GPU-accelerated video processing.
- **Tech**: C++, CUDA, CMake
- **Features**: GPU acceleration, NVIDIA Video Codec SDK

---

## 🧪 Legacy & Experimental

### Next-Generation Applications (orn-*)

#### **orn-admin-api** 🔄
Next-generation admin API (evolution of OrianeAdmin-nestjs).
- **Status**: In development

#### **orn-admin-web** 🌐
Next-generation admin web interface.
- **Status**: In development

#### **orn-experience-app** 📱
User experience application.
- **Status**: In development

#### **orn-search-api** 🔍
Next-generation search API.
- **Status**: In development

#### **orn-acquisition-lambdas** 📡
Consolidated acquisition lambda functions.
- **Status**: In development

### Kubernetes Applications

#### **orn-experience-applications** 📦
Kubernetes manifests for experience tier applications.

#### **orn-platform-applications** 🏢
Kubernetes manifests for platform services.

#### **orn-processor-applications** ⚙️
Kubernetes manifests for processing services.

#### **orn-platform-clusters** 🎯
Cluster-level configurations and management.

### Testing & Migration

#### **InstagramTests** 🧪
Test suite for Instagram integration and scraping.
- **Tech**: Python

#### **migration-supabase-to-aws** 🚚
Migration scripts from Supabase to AWS infrastructure.
- **Tech**: SQL, Bash

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Applications                        │
│  OrianeApp-nuxt  │  OrianeAdmin-react  │  orn-experience-app│
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────┴────────────────────────────────────────────────┐
│                       API Layer                              │
│  OrianeAdmin-nestjs  │  OrianeSearch-fastapi  │  orn-*-api  │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────┴────────────────────────────────────────────────┐
│                   Processing Layer                           │
│  OrianePipeline-fastapi  │  orn-processor-etls              │
│  Lambda Functions (acquisition, processing, analysis)        │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────┴────────────────────────────────────────────────┐
│                      AI Layer                                │
│  OrianeCoreAI-python  │  FramesEmbeddingsExtractor          │
│  AI Models (ViT, SAM, CLIP, SSCD)                           │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────┴────────────────────────────────────────────────┐
│                    Data Layer                                │
│  OrianeVectorDB-qdrant  │  PostgreSQL  │  S3                │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

1. **Content Acquisition**: Instagram lambdas collect content → S3
2. **Video Processing**: VideoCropper → VideoFramesExtractor → S3 frames
3. **AI Analysis**: FramesEmbeddingsExtractor generates vectors
4. **Storage**: Vectors stored in Qdrant, metadata in PostgreSQL
5. **Search**: OrianeSearch-fastapi queries Qdrant for visual search
6. **User Access**: Web apps consume APIs for search and management

## 🚀 Tech Stack

### Frontend
- **Nuxt 3** / **Vue 3** - Modern web framework
- **React** - Admin interfaces
- **TypeScript** - Type safety

### Backend
- **NestJS** - Enterprise Node.js framework
- **FastAPI** - High-performance Python API
- **PostgreSQL** - Relational database
- **Qdrant** - Vector database

### AI/ML
- **PyTorch** - Deep learning framework
- **Transformers** - Pre-trained models
- **CLIP** / **ViT** - Multi-modal embeddings
- **SAM** - Segmentation
- **OpenCV** - Computer vision

### Infrastructure
- **AWS Lambda** - Serverless compute
- **AWS S3** - Object storage
- **AWS Batch** - Batch processing
- **AWS SQS** - Message queuing
- **Kubernetes** - Container orchestration
- **Docker** - Containerization

### DevOps
- **Bash** - Automation scripts
- **Poetry** - Python dependency management
- **npm** / **pnpm** - Node.js packages

## 📦 Getting Started

Each repository contains its own README with specific setup instructions. General prerequisites:

```bash
# Core dependencies
- Node.js 18+
- Python 3.10+
- Docker & Docker Compose
- AWS CLI configured
- kubectl (for K8s deployments)

# Python projects
cd <project-directory>
poetry install
poetry run python main.py

# Node.js projects
cd <project-directory>
npm install
npm run dev
```

## 📚 Documentation

For in-depth technical documentation, research materials, and additional resources, see the **`_docs/`** directory:

### 📂 Documentation Structure

- **`_docs/TECH/`** - Technical documentation
  - **Architecture/** - System architecture diagrams (DrawIO files)
    - `ArchDiagrams.drawio` - Comprehensive architecture diagrams
    - `ArchInfra.drawio` - Infrastructure architecture
    - `SQLschemas.drawio` - Database schemas
    - `ETLs.drawio` - ETL pipeline diagrams
    - `Qdrant/` - Qdrant vector DB schema examples
  - **Research/** - AI/ML research and documentation
    - `Embeddings/` - Embeddings research (CLIP models, Qdrant on AWS)
    - `Models/` - AI model research (SSCD, ViT, filtering strategies)
    - `Scalability.docx` - Scalability analysis and planning
    - `APIs Frameworks table.xlsx` - API framework comparisons
  - **Samples/** - Sample data and debugging resources
    - `Debugging Samples/` - Test videos and debugging materials
    - `Hiker Responses/` - API response examples
    - `Video Samples.xlsx` - Test video catalog
  - `DNS.xlsx` - DNS configuration
  - `ETLs pricing.xlsx` - Cost analysis for ETL pipelines

- **`_docs/arch/`** - Architecture visualizations
  - System architecture diagrams (PNG/WebP)
  - Database schemas
  - Pipeline flow diagrams

- **`_docs/ai-images/`** - AI/ML concept visualizations
  - RAG architectures (naive, agentic, graph, multimodal)
  - Embedding strategies and types
  - Vector indexes and databases for AI apps
  - Context engineering and compression techniques

- **`_docs/pics/`** - Screenshots and UI mockups
  - Application screenshots
  - Development progress captures

- **`_docs/acquisition/`** - Content acquisition data
  - Instagram handles and keywords for monitoring

- **`_docs/alex linkedin pack/`** - Brand assets
  - LinkedIn banners and profile images

> 💡 **Tip**: Use Draw.io to open and edit `.drawio` files for architecture diagrams.

## 🔒 Security

- All `.env` files are excluded from version control
- AWS credentials managed via IAM roles
- Secrets stored in AWS Secrets Manager
- API authentication via JWT tokens
- Network security via VPC and security groups

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

This is a monorepo containing multiple interconnected projects. Each component follows its own development workflow.

---

**Built with ❤️ by the Oriane team**
