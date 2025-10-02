# Extract All Pipeline Test Suite

Batch extraction pipeline that processes Instagram video codes from S3 through the API endpoints with full state management and resumable execution.

**Author**: Alex Colls

## Prerequisites

- **Python 3.7+**: The pipeline requires Python 3.7 or higher
- **Dependencies**: Install required packages using `pip install -r requirements.txt`
- **Environment**: Configure environment variables in `.env` file (see Environment Variables section below)

## Directory Structure

```
/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/tests/extract_all/
├── main.py          # Main entrypoint script
├── config.py        # Configuration and environment loading
├── s3_utils.py      # S3 utilities and file listing
├── qdrant_utils.py  # Qdrant connectivity and operations
├── api_client.py    # API client for /process and /status endpoints
├── job_monitor.py   # Async job monitoring and polling
├── state.py         # State management and persistence
├── run.sh           # Main execution script
├── resume.sh        # Resume from checkpoint script
├── README.md        # This documentation
├── requests/        # API request logs
├── responses/       # API response logs
└── logs/           # Application logs
```

## Environment Variables

The system reads configuration from a `.env` file located at `../../../.env` (relative to this directory) or from environment variables. All configuration can be overridden via command-line arguments.

### Required Environment Variables

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=your-bucket-name

# API Configuration
API_URL=http://localhost:8000
```

### Optional Environment Variables

```bash
# S3 Configuration
S3_PREFIX=documents/                    # S3 prefix for file filtering

# Qdrant Configuration
QDRANT_URL=http://localhost:6333       # Qdrant server URL
QDRANT_API_KEY=your_qdrant_api_key     # Optional API key
QDRANT_COLLECTION=documents            # Collection name

# API Configuration
API_KEY=your_api_key                   # Optional API authentication

# Processing Configuration
LIMIT=100                              # Max files to process (0=unlimited)
INTERVAL=10                            # Polling interval in seconds
TIMEOUT=300                            # Job timeout in seconds
LOG_LEVEL=INFO                         # Logging level (DEBUG, INFO, WARNING, ERROR)
```

## Usage

### Basic Usage

```bash
# Run the pipeline with default settings
./run.sh

# Resume from last checkpoint
./resume.sh

# Check current status
./resume.sh --status
```

### Advanced Usage

```bash
# Process only 50 files with debug logging
./run.sh --limit 50 --log-level DEBUG

# Resume with custom polling interval
./resume.sh --interval 5 --timeout 600

# Use custom environment file
./run.sh --env-file /path/to/custom.env

# Monitor logs in real-time
./run.sh --monitor-logs
```

### Command Line Options

#### run.sh Options

- `--limit LIMIT`: Limit number of files to process
- `--interval INTERVAL`: Polling interval in seconds (default: 10)
- `--timeout TIMEOUT`: Job timeout in seconds (default: 300)
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--env-file FILE`: Path to custom .env file
- `--resume`: Resume from last checkpoint
- `--monitor-logs`: Monitor log file in real-time
- `--help`: Show help message

#### resume.sh Options

- `--limit LIMIT`: Limit number of files to process
- `--interval INTERVAL`: Polling interval in seconds
- `--timeout TIMEOUT`: Job timeout in seconds
- `--log-level LEVEL`: Logging level
- `--env-file FILE`: Path to custom .env file
- `--status`: Show current status and statistics
- `--reset`: Reset state (clears all progress)
- `--help`: Show help message

## Python API Usage

### Direct Python Usage

```python
import asyncio
from config import Config
from s3_utils import S3Utils
from api_client import APIClient
from job_monitor import JobMonitor
from state import StateManager

async def main():
    # Initialize components
    config = Config()
    s3_utils = S3Utils(config)
    api_client = APIClient(config)
    state_manager = StateManager(config)
    job_monitor = JobMonitor(config, api_client, state_manager)

    # List files to process
    files = await s3_utils.list_files()

    # Process a single file
    job_id = await api_client.submit_job(files[0])
    result = await job_monitor.monitor_job(job_id)

    # Mark as processed
    await state_manager.mark_processed(files[0], job_id, result)

if __name__ == '__main__':
    asyncio.run(main())
```

### Running Python Script Directly

```bash
# Run with default settings
python3 main.py

# Run with custom options
python3 main.py --limit 50 --interval 5 --log-level DEBUG

# Resume from checkpoint
python3 main.py --resume
```

## State Management

The system maintains persistent state in `state.json` to enable resumable execution:

- **Processed Files**: Track successfully processed files with results
- **Failed Files**: Track failed files with error details and retry counts
- **Job History**: Complete history of all jobs with status and results
- **Automatic Backup**: State is backed up before major operations
- **Cleanup**: Old entries are automatically cleaned up to prevent unbounded growth

### State File Structure

```json
{
  "processed_files": {
    "s3_key": {
      "job_id": "job_123",
      "timestamp": "2024-01-01T12:00:00",
      "status": "completed",
      "result": {...}
    }
  },
  "failed_files": {
    "s3_key": {
      "job_id": "job_456",
      "timestamp": "2024-01-01T12:00:00",
      "error": "Processing failed",
      "retry_count": 1
    }
  },
  "job_history": {
    "job_123": {
      "s3_key": "document.pdf",
      "timestamp": "2024-01-01T12:00:00",
      "status": "completed",
      "result": {...}
    }
  }
}
```

## Logging

Comprehensive logging is provided with multiple levels:

- **DEBUG**: Detailed execution information
- **INFO**: General progress and status updates
- **WARNING**: Non-critical issues and recoverable errors
- **ERROR**: Critical errors and failures

### Log Files

- `logs/extract_all.log`: Main application log
- `requests/`: API request logs (timestamped JSON files)
- `responses/`: API response logs (timestamped JSON files)

## Error Handling

The system provides robust error handling:

- **Connection Errors**: Automatic retry for transient network issues
- **Timeout Handling**: Jobs that exceed timeout are cancelled
- **State Recovery**: Automatic state recovery from backup files
- **Graceful Shutdown**: Clean shutdown on interrupt signals
- **Partial Failures**: Individual file failures don't stop the entire process

## Performance Considerations

- **Async Processing**: Non-blocking I/O for efficient resource utilization
- **Concurrent Jobs**: Multiple jobs can be monitored simultaneously
- **Memory Management**: Efficient memory usage with streaming operations
- **State Persistence**: Atomic state updates to prevent corruption
- **Connection Pooling**: Reused HTTP connections for better performance

## Monitoring and Statistics

### Real-time Monitoring

```bash
# Show current status
./resume.sh --status

# Monitor logs in real-time
tail -f logs/extract_all.log

# Watch for new request/response files
watch -n 1 "ls -la requests/ responses/"
```

### Statistics Available

- Total files processed
- Total files failed
- Success rate percentage
- Recent activity (last 24 hours)
- Average processing time
- Current active jobs

## Troubleshooting

### Common Issues

1. **Missing Dependencies**

   ```bash
   pip3 install asyncio aiohttp aiofiles boto3 python-dotenv
   ```

2. **Environment Variables**

   ```bash
   # Check if .env file exists
   ls -la ../../../.env

   # Verify environment variables
   ./run.sh --help
   ```

3. **Permission Issues**

   ```bash
   # Make scripts executable
   chmod +x run.sh resume.sh
   ```

4. **State Corruption**
   ```bash
   # Reset state if corrupted
   ./resume.sh --reset
   ```

### Debug Mode

```bash
# Run with debug logging
./run.sh --log-level DEBUG

# Check individual component health
python3 -c "from config import Config; from s3_utils import S3Utils; import asyncio; asyncio.run(S3Utils(Config()).check_connection())"
```

## API Endpoints

The system interacts with the following API endpoints:

- `POST /process`: Submit processing jobs
- `GET /status/{job_id}`: Check job status
- `GET /result/{job_id}`: Get job results
- `POST /cancel/{job_id}`: Cancel jobs (optional)
- `GET /health`: Health check
- `GET /info`: API information

## Security Considerations

- Environment variables are used for sensitive configuration
- API keys are not logged in plain text
- State files may contain sensitive information - secure appropriately
- Network traffic uses HTTPS where configured
- File paths are validated to prevent directory traversal

## Contributing

To extend or modify the system:

1. Follow the existing code structure and patterns
2. Add comprehensive error handling
3. Update tests and documentation
4. Ensure backward compatibility with existing state files
5. Add appropriate logging for debugging

## License

This software is part of the ExtractionPipeline project. See the main project for license information.
