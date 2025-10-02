# Performance Tuning Guide

This guide provides detailed recommendations for optimizing the performance of the Oriane Extraction Pipeline API, including tuning batch sizes, parallel job limits, and GPU memory management.

## Table of Contents

- [Performance Overview](#performance-overview)
- [Batch Size Optimization](#batch-size-optimization)
- [Parallel Job Management](#parallel-job-management)
- [GPU Memory Management](#gpu-memory-management)
- [FFMPEG Optimization](#ffmpeg-optimization)
- [Vector Database Performance](#vector-database-performance)
- [Monitoring and Metrics](#monitoring-and-metrics)
- [Troubleshooting](#troubleshooting)

## Performance Overview

The Oriane Extraction Pipeline processes videos through several stages:

1. **Video Download & Preprocessing**
2. **FFMPEG Cropping** (GPU-accelerated)
3. **Scene Detection & Frame Extraction**
4. **Frame Deduplication** (dHash)
5. **CLIP Embedding Generation** (GPU-intensive)
6. **S3 Upload** (I/O bound)
7. **Vector Database Storage** (Network bound)

Each stage has different performance characteristics and bottlenecks.

## Batch Size Optimization

### `VP_BATCH_SIZE` - CLIP Micro-batch Size

Controls the number of frames processed simultaneously during CLIP embedding generation.

**Environment Variable:**
```bash
VP_BATCH_SIZE=8
```

**Performance Impact:**
- **Small batches (1-4)**: Lower GPU memory usage, higher processing overhead
- **Medium batches (8-16)**: Balanced performance and memory usage
- **Large batches (32-64)**: Maximum GPU utilization, risk of OOM errors

**Tuning Recommendations:**

| GPU Memory | Recommended Batch Size | Max Batch Size |
|------------|----------------------|----------------|
| 4GB        | 4-8                  | 16             |
| 8GB        | 8-16                 | 32             |
| 12GB       | 16-32                | 64             |
| 16GB+      | 32-64                | 128            |

**Example Configuration:**
```bash
# For NVIDIA RTX 3080 (10GB)
VP_BATCH_SIZE=16

# For NVIDIA V100 (16GB)
VP_BATCH_SIZE=32

# For limited memory environments
VP_BATCH_SIZE=4
```

### Request Batch Size

Controls the number of videos processed in a single API request.

**Environment Variable:**
```bash
MAX_VIDEOS_PER_REQUEST=1000
```

**Performance Considerations:**
- Larger request batches reduce API overhead
- Memory usage scales with batch size
- Failed requests affect more videos
- Progress tracking becomes less granular

**Recommended Settings:**
```bash
# For high-throughput scenarios
MAX_VIDEOS_PER_REQUEST=1000

# For memory-constrained environments
MAX_VIDEOS_PER_REQUEST=100

# For development/testing
MAX_VIDEOS_PER_REQUEST=10
```

## Parallel Job Management

### `PIPELINE_MAX_PARALLEL_JOBS` - Maximum Concurrent Jobs

Controls the maximum number of processing jobs running simultaneously.

**Environment Variable:**
```bash
PIPELINE_MAX_PARALLEL_JOBS=2
```

**Performance Impact:**
- **Too low**: Underutilized resources, poor throughput
- **Too high**: GPU memory contention, system instability
- **Optimal**: Balanced resource usage and throughput

**Tuning Formula:**
```
Optimal Jobs = min(
    GPU_Memory_GB / (Estimated_Job_Memory_GB + 2),
    CPU_Cores / 2,
    Available_System_Memory_GB / 4
)
```

**Example Calculations:**

| System Configuration | Recommended Jobs | Reasoning |
|---------------------|------------------|-----------|
| 1x RTX 3080 (10GB), 16 cores, 32GB RAM | 2 | GPU memory limited |
| 2x V100 (32GB), 32 cores, 64GB RAM | 4 | Balanced across GPUs |
| 1x RTX 4090 (24GB), 24 cores, 128GB RAM | 4 | CPU and GPU balanced |

**Configuration Examples:**
```bash
# Single GPU workstation
PIPELINE_MAX_PARALLEL_JOBS=2

# Multi-GPU server
PIPELINE_MAX_PARALLEL_JOBS=4

# High-memory system
PIPELINE_MAX_PARALLEL_JOBS=6
```

### Worker Thread Configuration

Controls FFMPEG cropping thread pool size.

**Environment Variable:**
```bash
VP_MAX_WORKERS=4
```

**Performance Guidelines:**
- Should match CPU core count for CPU-bound tasks
- Reduce for memory-constrained environments
- Increase for I/O-bound operations

**Recommended Settings:**
```bash
# For 8-core systems
VP_MAX_WORKERS=8

# For 16-core systems
VP_MAX_WORKERS=16

# For memory-limited environments
VP_MAX_WORKERS=4
```

## GPU Memory Management

### Memory Allocation Strategy

The pipeline uses GPU memory for:
1. **CLIP Model Loading**: ~2-4GB (depends on model)
2. **Batch Processing**: ~100-500MB per batch
3. **FFMPEG CUDA Operations**: ~1-2GB
4. **System Overhead**: ~1GB

### Memory Optimization Techniques

#### 1. Model Optimization
```bash
# Use smaller CLIP models for reduced memory usage
CLIP_MODEL=openai/clip-vit-base-patch32  # ~600MB
# vs
CLIP_MODEL=jinaai/jina-clip-v2          # ~2GB
```

#### 2. Batch Size Scaling
```bash
# Dynamic batch sizing based on available memory
VP_BATCH_SIZE=8   # Start conservative
```

#### 3. CUDA Memory Management
```bash
# Enable memory fraction limiting
CUDA_MEMORY_FRACTION=0.8

# Enable memory growth
CUDA_MEMORY_GROWTH=1
```

### GPU Memory Monitoring

Monitor GPU memory usage:
```bash
# Check GPU memory
nvidia-smi -l 1

# Monitor specific metrics
nvidia-smi --query-gpu=memory.used,memory.total --format=csv -l 1
```

### Memory Troubleshooting

**Common Issues:**

1. **CUDA Out of Memory (OOM)**
   ```bash
   # Reduce batch size
   VP_BATCH_SIZE=4
   
   # Reduce parallel jobs
   PIPELINE_MAX_PARALLEL_JOBS=1
   ```

2. **Memory Fragmentation**
   ```bash
   # Restart service periodically
   # Implement memory cleanup in processing loops
   ```

3. **Model Loading Failures**
   ```bash
   # Clear GPU memory before model loading
   # Use model quantization
   ```

## FFMPEG Optimization

### Hardware Acceleration

Configure NVIDIA GPU acceleration:
```bash
# Enable CUDA acceleration
VP_CROP_HWACCEL=cuda

# Use NVENC encoder
VP_CROP_ENCODER=h264_nvenc

# Optimize encoder settings
VP_CROP_PRESET=p5     # Performance preset
VP_CROP_TUNE=hq       # High quality
VP_CROP_CQ=23         # Constant quality
```

### Encoder Performance Settings

**Preset Options** (VP_CROP_PRESET):
- `p1`: Fastest, lowest quality
- `p3`: Balanced speed/quality
- `p5`: Recommended for most cases
- `p7`: Slower, higher quality

**Tuning Options** (VP_CROP_TUNE):
- `hq`: High quality (recommended)
- `ll`: Low latency
- `ull`: Ultra low latency

### Memory Management for FFMPEG

```bash
# Limit concurrent FFMPEG processes
VP_MAX_WORKERS=4

# Optimize clip duration for crop detection
VP_CROP_CLIP_SECS=2

# Reduce probes for faster processing
VP_CROP_PROBES=3
```

## Vector Database Performance

### Qdrant Configuration

Optimize Qdrant connection settings:
```bash
# Connection pooling
QDRANT_CONNECTION_POOL_SIZE=10

# Batch insertion
QDRANT_BATCH_SIZE=100

# Compression
QDRANT_COMPRESSION=true
```

### Embedding Storage Optimization

```bash
# Optimize vector dimensions
QDRANT_DIM=512  # Balance between accuracy and performance

# Use appropriate distance metric
QDRANT_DISTANCE=cosine
```

## Monitoring and Metrics

### Key Performance Metrics

1. **Throughput Metrics**
   - Videos processed per hour
   - Frames extracted per minute
   - Embeddings generated per second

2. **Resource Utilization**
   - GPU memory usage
   - CPU utilization
   - Network I/O for S3 uploads

3. **Error Rates**
   - Failed video processing
   - S3 upload failures
   - Vector database insertion errors

### Performance Monitoring Endpoints

```bash
# Get concurrency statistics
curl -X GET "http://localhost:8000/concurrency/stats" \
  -H "X-API-Key: your-api-key-here"

# Check system configuration
curl -X GET "http://localhost:8000/config" \
  -H "X-API-Key: your-api-key-here"
```

### Logging Configuration

Enable detailed performance logging:
```bash
# Set log level
LOG_LEVEL=info

# Enable performance metrics
ENABLE_PERFORMANCE_METRICS=true
```

## Troubleshooting

### Common Performance Issues

#### 1. Slow Video Processing
**Symptoms:** High processing time per video
**Solutions:**
```bash
# Increase FFMPEG workers
VP_MAX_WORKERS=8

# Optimize hardware acceleration
VP_CROP_HWACCEL=cuda
VP_CROP_ENCODER=h264_nvenc
```

#### 2. GPU Memory Errors
**Symptoms:** CUDA OOM errors
**Solutions:**
```bash
# Reduce batch size
VP_BATCH_SIZE=4

# Limit parallel jobs
PIPELINE_MAX_PARALLEL_JOBS=1
```

#### 3. High CPU Usage
**Symptoms:** CPU bottlenecks
**Solutions:**
```bash
# Reduce worker threads
VP_MAX_WORKERS=4

# Optimize scene detection
VP_SCENE_THRESH=0.3
```

#### 4. S3 Upload Delays
**Symptoms:** Slow S3 uploads
**Solutions:**
```bash
# Increase connection pools
AWS_MAX_POOL_CONNECTIONS=20

# Use multipart uploads
AWS_MULTIPART_THRESHOLD=8388608
```

### Performance Benchmarking

Use these commands to benchmark performance:

```bash
# Process test batch
curl -X POST "http://localhost:8000/process" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d @sample_100_videos_request.json

# Monitor processing time
time curl -X GET "http://localhost:8000/status/{job_id}" \
  -H "X-API-Key: your-api-key-here"
```

### Optimal Configuration Examples

#### High-Performance Configuration
```bash
# For high-end GPU servers
VP_BATCH_SIZE=32
PIPELINE_MAX_PARALLEL_JOBS=4
VP_MAX_WORKERS=16
VP_CROP_HWACCEL=cuda
VP_CROP_ENCODER=h264_nvenc
VP_CROP_PRESET=p5
MAX_VIDEOS_PER_REQUEST=1000
```

#### Memory-Constrained Configuration
```bash
# For limited memory systems
VP_BATCH_SIZE=4
PIPELINE_MAX_PARALLEL_JOBS=1
VP_MAX_WORKERS=4
VP_CROP_HWACCEL=cuda
VP_CROP_ENCODER=h264_nvenc
VP_CROP_PRESET=p3
MAX_VIDEOS_PER_REQUEST=100
```

#### Development Configuration
```bash
# For development and testing
VP_BATCH_SIZE=2
PIPELINE_MAX_PARALLEL_JOBS=1
VP_MAX_WORKERS=2
VP_CROP_HWACCEL=auto
VP_CROP_ENCODER=libx264
VP_CROP_PRESET=fast
MAX_VIDEOS_PER_REQUEST=10
LOCAL_MODE=1
SKIP_UPLOAD=1
```

## Performance Monitoring Dashboard

Consider implementing monitoring with:
- **Prometheus**: For metrics collection
- **Grafana**: For visualization
- **Custom endpoints**: For application-specific metrics

Example metrics to track:
- Processing pipeline latency
- GPU memory utilization
- Video processing throughput
- Error rates by processing stage
- S3 upload success rates
- Vector database insertion rates

This comprehensive performance tuning should help optimize your Oriane Extraction Pipeline API for various deployment scenarios and resource constraints.
