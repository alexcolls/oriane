# Logging & DEBUG Support Implementation

## Overview

This implementation provides comprehensive logging and debug support for the extraction pipeline with the following key features:

1. **Consistent Logging Format**: Uses `configure_logging()` throughout the application
2. **Line-by-Line Streaming**: Subprocess output is streamed line-by-line into Job.log
3. **Real-time Debug View**: When `DEBUG_PIPELINE=1`, output is forwarded to UVicorn logger for real-time viewing

## Implementation Details

### 1. Consistent Logging Format

All modules now use `configure_logging()` to ensure consistent log formatting:

```python
from config.logging_config import configure_logging

# Configure logging using consistent format
logger = configure_logging()
uvicorn_logger = logging.getLogger("uvicorn")
```

### 2. Line-by-Line Subprocess Output Streaming

The `_execute_pipeline_async()` function now streams subprocess output line-by-line:

```python
# Read stdout line by line
while True:
    line = await process.stdout.readline()
    if not line:
        break
    line_str = line.decode().rstrip()
    if line_str:
        stdout_lines.append(line_str)
        
        # Stream to Job.log
        await update_job_status(job_id, log=line_str)
        
        # Forward to logger
        logger.info(line_str)
        
        # Forward to UVicorn logger when DEBUG_PIPELINE is true
        if debug_pipeline:
            uvicorn_logger.info(f"[Job {job_id}] {line_str}")
```

### 3. DEBUG_PIPELINE Support

When `DEBUG_PIPELINE=1` environment variable is set:
- Subprocess output is forwarded to UVicorn logger with job ID prefix
- Real-time viewing is enabled in the server logs
- Both stdout and stderr are captured and logged

### 4. Enhanced Job Model

The `update_job_status()` function has been enhanced to support log-only updates:

```python
async def update_job_status(job_id: UUID, status: Optional[JobStatus] = None, 
                           log: Optional[str] = None, 
                           progress: Optional[int] = None) -> Optional[Job]:
```

- `status` parameter is now optional (None to keep current status)
- Allows for efficient log streaming without changing job status
- Thread-safe with asyncio.Lock protection

## Usage Examples

### Basic Job Processing with Logging

```python
# Create a job
job = await create_job(items)

# Enable debug mode
os.environ["DEBUG_PIPELINE"] = "1"

# Process the job (logs will stream to Job.log and UVicorn logger)
await run_job(job.id)
```

### Log-Only Updates

```python
# Stream a log message without changing status
await update_job_status(job_id, log="Processing frame 1/100")

# Update status and log together
await update_job_status(job_id, status=JobStatus.RUNNING, log="Started processing")
```

### Real-time Debug Viewing

When `DEBUG_PIPELINE=1` is set, you can view real-time logs in the server output:

```
[2025-01-07 01:24:29] INFO     [Job b7d2e44d-fd97-4cd9-8419-76d3abae8700] Processing video 1/10
[2025-01-07 01:24:30] INFO     [Job b7d2e44d-fd97-4cd9-8419-76d3abae8700] Extracting frames...
[2025-01-07 01:24:31] INFO     [Job b7d2e44d-fd97-4cd9-8419-76d3abae8700] Frame extraction complete
```

## Key Benefits

1. **Real-time Monitoring**: Developers can monitor job progress in real-time when DEBUG_PIPELINE is enabled
2. **Persistent Logging**: All output is captured in Job.log for historical analysis
3. **Consistent Format**: All logs use the same format across the application
4. **Thread Safety**: Log updates are thread-safe with proper locking
5. **Performance**: Efficient streaming without buffering entire output

## Testing

The implementation includes a test script (`test_logging_debug.py`) that verifies:
- Logging configuration
- Job creation and status updates
- Log streaming functionality
- DEBUG_PIPELINE environment variable handling

Run the test with:
```bash
python3 test_logging_debug.py
```

## Environment Variables

- `DEBUG_PIPELINE`: Set to "1" to enable real-time UVicorn logging
- All other logging configuration is handled by `configure_logging()`

## File Changes

- `background/tasks.py`: Added line-by-line streaming and debug support
- `models/job.py`: Enhanced to support log-only updates
- `app.py`: Updated to use consistent logging format
- `config/logging_config.py`: Already existed, now used consistently
