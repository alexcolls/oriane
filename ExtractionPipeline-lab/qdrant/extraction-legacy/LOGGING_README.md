# Logging Infrastructure

This document describes the logging infrastructure for the extraction pipeline.

## Overview

The `logger.py` module provides a comprehensive logging solution with:
- **Rotating file handler**: Logs are saved to `/home/quantium/labs/oriane/ExtractionPipeline/qdrant/scripts/extract/logs/extract.log` with automatic rotation (10MB max, 5 backups)
- **Rich console output**: Enhanced terminal display with colors, timestamps, and rich formatting
- **Structured logging**: Specialized logging for batch operations including batch number, DB ID range, success/fail counts, and elapsed time

## Features

### File Logging
- Automatic log rotation (10MB per file, keeps 5 backups)
- Persistent storage in `logs/extract.log`
- Full extraction-specific formatting including batch info, ID ranges, and timing

### Console Logging
- Rich terminal output with colors and formatting
- Real-time progress display
- Exception tracebacks with local variables

### Batch Operation Logging
- Batch start/progress/completion tracking
- Success/failure counts
- Elapsed time measurement
- Database ID range tracking

## Usage

### Basic Usage

```python
from logger import setup_logging

# Initialize logger
logger = setup_logging("INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Basic logging
logger.info("Processing started")
logger.warning("Low memory warning")
logger.error("Failed to connect to database")
```

### Batch Operation Logging

```python
from logger import setup_logging, BatchContext

logger = setup_logging("INFO")

# Method 1: Using BatchContext (recommended)
with BatchContext(batch_number=1, db_id_range="1-1000", total_records=1000) as batch:
    logger.info("Processing batch...")

    # Process records...
    for record in records:
        try:
            # Process record
            process_record(record)
            batch.record_success()
        except Exception as e:
            logger.error(f"Failed to process record: {e}")
            batch.record_failure()

        # Log progress every 100 records
        if processed % 100 == 0:
            batch.log_progress(processed)

# Method 2: Manual logging
logger.log_batch_start(batch_number=1, db_id_range="1-1000", total_records=1000)
# ... processing ...
logger.log_batch_complete(batch_number=1, db_id_range="1-1000",
                         success_count=950, fail_count=50, elapsed_time=120.5)
```

### Advanced Usage

```python
from logger import get_logger

# Get global logger instance
logger = get_logger("DEBUG")

# Log with custom fields
logger.info("Custom message", custom_field="value", another_field=123)

# Log extraction statistics
stats = {
    "total_processed": 10000,
    "success_rate": 95.2,
    "avg_processing_time": 0.5,
    "errors": ["connection_timeout", "invalid_data"]
}
logger.log_extraction_stats(stats)
```

## Log Format

### File Log Format
```
[IDs 1-1000] [Batch 1] 2025-07-06 21:27:37 - extraction_pipeline - INFO - Starting batch processing - Total records: 1000
[IDs 1-1000] [Batch 1] 2025-07-06 21:27:40 - extraction_pipeline - INFO - Batch progress: 500/1000 (50.0%) (Success: 475, Failed: 25)
[IDs 1-1000] [Batch 1] 2025-07-06 21:27:45 - extraction_pipeline - INFO - Batch completed - Total processed: 1000, Success rate: 95.0% (Success: 950, Failed: 50) [Elapsed: 8.23s]
```

### Console Format
The console output uses rich formatting with:
- Color-coded log levels
- Timestamps
- File names and line numbers
- Progress indicators
- Rich exception tracebacks

## Configuration

### Log Levels
- `DEBUG`: Detailed information for diagnosing problems
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical error messages for very serious errors

### File Rotation
- **Max file size**: 10MB
- **Backup count**: 5 files
- **Encoding**: UTF-8
- **Location**: `/home/quantium/labs/oriane/ExtractionPipeline/qdrant/scripts/extract/logs/extract.log`

## Integration Example

```python
#!/usr/bin/env python3
"""
Example extraction script using the logging infrastructure.
"""

from logger import setup_logging, BatchContext
import time

def main():
    # Initialize logging
    logger = setup_logging("INFO")
    logger.info("Starting extraction pipeline")

    try:
        # Example batch processing
        batch_size = 1000
        total_records = 10000

        for batch_num in range(1, (total_records // batch_size) + 1):
            start_id = (batch_num - 1) * batch_size + 1
            end_id = min(batch_num * batch_size, total_records)
            id_range = f"{start_id}-{end_id}"

            with BatchContext(batch_num, id_range, end_id - start_id + 1) as batch:
                logger.info(f"Processing batch {batch_num}")

                # Simulate processing
                for i in range(end_id - start_id + 1):
                    # Simulate some processing time
                    time.sleep(0.001)

                    # Simulate success/failure
                    if i % 10 == 0:
                        batch.record_failure()
                    else:
                        batch.record_success()

                    # Log progress every 100 records
                    if i % 100 == 0:
                        batch.log_progress(i + 1)

        logger.info("Extraction pipeline completed successfully")

    except Exception as e:
        logger.exception("Extraction pipeline failed")
        raise

if __name__ == "__main__":
    main()
```

## Files

- `logger.py`: Main logging module
- `logs/extract.log`: Main log file (auto-created)
- `logs/extract.log.1`, `logs/extract.log.2`, etc.: Rotated log files
