# Concurrency & Throttling Features

This document describes the concurrency and throttling features implemented in the extraction pipeline API.

## Overview

The following features have been implemented to control concurrency and resource usage:

1. **New Environment Variables**
2. **Bounded ThreadPoolExecutor**
3. **GPU Memory Protection via Semaphore**
4. **Job Queue Management**
5. **Status Transitions (PENDING → RUNNING → COMPLETED/FAILED)**

## Environment Variables

### New Settings in `config/env_config.py`:

- `MAX_VIDEOS_PER_REQUEST` (int, default: 1000)
  - Controls the maximum number of videos allowed per `/process` request
  - Prevents resource exhaustion from oversized requests

- `PIPELINE_MAX_PARALLEL_JOBS` (int, default: 2)
  - Controls the maximum number of concurrent pipeline jobs
  - Limits GPU memory usage and system resource consumption

### Environment Variable Configuration

Add these to your `.env` file:

```bash
MAX_VIDEOS_PER_REQUEST=1000
PIPELINE_MAX_PARALLEL_JOBS=2
```

## Concurrency Manager

### Features

1. **Bounded ThreadPoolExecutor**
   - Limited to `PIPELINE_MAX_PARALLEL_JOBS` concurrent workers
   - Prevents resource exhaustion
   - Automatically queues overflow jobs

2. **GPU Memory Protection**
   - Semaphore with `PIPELINE_MAX_PARALLEL_JOBS` permits
   - Prevents GPU memory overallocation
   - Context manager: `async with manager.gpu_memory_protection():`

3. **Job Queue Management**
   - FIFO queue for pending jobs
   - Automatic worker assignment
   - Status tracking: PENDING → RUNNING → COMPLETED/FAILED

### Usage

```python
from config.concurrency_manager import get_concurrency_manager

manager = get_concurrency_manager()

# Submit a job
result = await manager.submit_job(function, *args, **kwargs)

# Use GPU memory protection
async with manager.gpu_memory_protection():
    # GPU-intensive operations
    pass

# Get statistics
stats = manager.get_stats()
```

## Job Status Flow

1. **PENDING**: Job is created and queued for processing
2. **RUNNING**: Job is being executed by a worker
3. **COMPLETED**: Job finished successfully (exit code 0)
4. **FAILED**: Job failed (non-zero exit code or exception)

## API Endpoints

### New Monitoring Endpoint

**GET `/concurrency/stats`**

Returns concurrency manager statistics:

```json
{
  "max_parallel_jobs": 2,
  "queue_size": 0,
  "active_workers": 2,
  "workers_running": true,
  "gpu_semaphore_available": 2
}
```

### Updated Configuration Endpoints

**GET `/config`** and **GET `/debug/settings`** now include:

```json
{
  "max_videos_per_request": 1000,
  "pipeline_max_parallel_jobs": 2,
  ...
}
```

## Implementation Details

### Files Modified

1. **`config/env_config.py`**
   - Added `MAX_VIDEOS_PER_REQUEST` and `PIPELINE_MAX_PARALLEL_JOBS` settings

2. **`config/concurrency_manager.py`** (new)
   - Implements `ConcurrencyManager` class
   - Bounded ThreadPoolExecutor with configurable parallelism
   - GPU memory semaphore protection
   - Job queue with worker management

3. **`background/tasks.py`**
   - Updated to use concurrency manager instead of direct ThreadPoolExecutor
   - Proper job status transitions
   - GPU memory protection integration

4. **`app.py`**
   - Added startup/shutdown event handlers
   - Initializes concurrency manager on startup
   - Added `/concurrency/stats` monitoring endpoint
   - Updated config endpoints

5. **`.env.sample`**
   - Added documentation for new environment variables

### Key Components

#### ConcurrencyManager Class

- **Worker Pool**: Bounded ThreadPoolExecutor with configurable size
- **GPU Semaphore**: Limits concurrent GPU operations
- **Job Queue**: FIFO queue for managing overflow
- **Statistics**: Real-time monitoring of concurrency state

#### Job Processing Flow

1. Job created with PENDING status
2. Job queued in concurrency manager
3. Worker picks up job and updates status to RUNNING
4. Worker executes pipeline with GPU memory protection
5. Job status updated to COMPLETED or FAILED based on result

## Testing

The implementation has been tested with:

1. **Unit Tests**: Individual component functionality
2. **Integration Tests**: End-to-end job processing
3. **Concurrency Tests**: Multiple jobs with queue management
4. **API Tests**: Endpoint functionality
5. **Environment Override Tests**: Configuration flexibility

### Test Results

- ✅ Concurrency manager initializes correctly
- ✅ Job queue processes multiple jobs with proper limits
- ✅ GPU semaphore prevents resource overallocation
- ✅ Status transitions work correctly
- ✅ API endpoints return proper data
- ✅ Environment variables override defaults
- ✅ Server startup/shutdown works properly

## Configuration Recommendations

### Development Environment
```bash
PIPELINE_MAX_PARALLEL_JOBS=2
MAX_VIDEOS_PER_REQUEST=100
```

### Production Environment
```bash
PIPELINE_MAX_PARALLEL_JOBS=4
MAX_VIDEOS_PER_REQUEST=1000
```

### High-Performance Setup
```bash
PIPELINE_MAX_PARALLEL_JOBS=8
MAX_VIDEOS_PER_REQUEST=2000
```

## Monitoring

Use the `/concurrency/stats` endpoint to monitor:

- Queue size (jobs waiting)
- Active workers (jobs running)
- GPU semaphore availability
- Worker status

## Benefits

1. **Resource Control**: Prevents GPU memory exhaustion
2. **Scalability**: Configurable parallelism based on hardware
3. **Reliability**: Proper error handling and status tracking
4. **Monitoring**: Real-time visibility into concurrency state
5. **Flexibility**: Environment-based configuration
6. **Queue Management**: Automatic handling of overflow jobs

The implementation provides a robust foundation for managing concurrent video processing jobs while protecting system resources and maintaining operational visibility.
