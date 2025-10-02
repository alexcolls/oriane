# Resource Throttling & Parallelism Implementation

## Overview

This implementation adds resource throttling and parallelism control to avoid GPU/memory exhaustion while maintaining efficient processing. The pipeline now processes batches sequentially with configurable sleep intervals, while internal operations use controlled parallelism.

## Key Features

### ✅ Sequential Batch Processing
- Frames are processed in sequential batches to prevent GPU/memory exhaustion
- Configurable batch size (default: 8 frames per batch)
- Sleep interval between batches allows GPU/memory recovery
- Internal parallelism within each batch (max 4 workers)

### ✅ CLI Configuration
- `--batch-size N`: Control frames per batch (default: 8)
- `--sleep X.X`: Sleep duration between batches in seconds (default: 0.5)
- CLI arguments override environment variables

### ✅ Environment Variables
- `VP_BATCH_SIZE`: Batch size for frame processing
- `VP_SLEEP_BETWEEN_BATCHES`: Sleep duration between batches
- `VP_MAX_WORKERS`: Maximum worker threads (default: 4)

## Usage Examples

### Conservative Settings (Limited Resources)
```bash
# Small batches with longer recovery time
python main.py --batch-size 4 --sleep 2.0
python entrypoint.py --batch-size 4 --sleep 2.0
```

### Aggressive Settings (Powerful Hardware)
```bash
# Larger batches with minimal recovery time
python main.py --batch-size 16 --sleep 0.1
python entrypoint.py --batch-size 16 --sleep 0.1
```

### GPU Memory Constrained
```bash
# Very small batches with extended recovery
python entrypoint.py --batch-size 2 --sleep 1.0
```

## Implementation Details

### 1. Main Orchestrator (`main.py`)
- Added CLI argument parsing with `argparse`
- Sequential batch processing with sleep between batches
- Configuration logging for transparency

### 2. Pipeline Core (`src/pipeline.py`)
- New `_encode_frames_in_batches()` method for sequential processing
- Configurable batch size and sleep duration
- Progress tracking and logging
- GPU memory recovery between batches

### 3. Entry Point (`entrypoint.py`)
- CLI argument support for batch configuration
- Environment variable override capability
- Small delays between items for resource recovery

### 4. Environment Configuration (`config/env_config.py`)
- Added `sleep_between_batches` setting
- Configurable via `VP_SLEEP_BETWEEN_BATCHES` environment variable

### 5. Upload Throttling (`src/upload_frames.py`)
- Respects `max_workers` setting from configuration
- Controlled parallelism for S3 uploads

## Resource Management Strategy

1. **Sequential Batch Processing**: Process frames in small sequential batches rather than all at once
2. **Controlled Parallelism**: Limit worker threads to maximum of 4 concurrent operations
3. **Recovery Intervals**: Sleep between batches allows GPU memory cleanup and thermal recovery
4. **Adaptive Configuration**: CLI flags allow tuning based on available resources

## Configuration Hierarchy

1. CLI arguments (highest priority)
2. Environment variables
3. Default values (lowest priority)

## Performance Considerations

- **Batch Size**: Smaller batches = lower memory usage, but more overhead
- **Sleep Duration**: Longer sleep = better resource recovery, but slower throughput
- **Max Workers**: Limited to 4 to prevent resource contention

## Monitoring & Logging

The implementation includes comprehensive logging:
- Batch processing progress
- Resource configuration settings
- Sleep intervals and recovery periods
- Error handling and retry logic

## Examples in Practice

### Default Configuration
```bash
# Uses batch_size=8, sleep=0.5s, max_workers=4
python entrypoint.py
```

### Custom Resource Limits
```bash
# Conservative: small batches, longer recovery
python entrypoint.py --batch-size 4 --sleep 1.5

# Aggressive: larger batches, minimal recovery
python entrypoint.py --batch-size 12 --sleep 0.2
```

## Error Handling

- GPU OOM errors trigger automatic batch size reduction
- CPU fallback when GPU resources exhausted
- Graceful recovery with appropriate logging

This implementation successfully balances throughput with resource constraints, making the pipeline more robust and adaptable to different hardware configurations.
