# Retry Queue Functionality

## Overview

The video extraction pipeline now includes graceful error capture and retry queue functionality. This ensures that temporary failures don't cause entire batches to fail permanently, and individual items can be retried up to a configurable number of times.

## Architecture

### main.py - Orchestrator
- **Purpose**: Main entry point that handles batch processing with retry logic
- **Responsibilities**:
  - Splits input into initial batches
  - Runs `entrypoint.py` subprocess for each batch
  - Parses exit status to detect failures
  - Maintains local retry queue for failed items
  - Retries failed items individually with configurable attempts

### entrypoint.py - Batch Processor
- **Purpose**: Processes individual items within a batch
- **Responsibilities**:
  - Processes each item through the full pipeline
  - Records errors to `extraction_errors` table via FK
  - Returns appropriate exit status (0=success, 1=failure)
  - Ensures any batch with failures exits with non-zero status

## Error Handling Flow

```
1. main.py splits items into batches
2. For each batch:
   └── main.py calls entrypoint.py subprocess
   └── entrypoint.py processes items individually
   └── If item fails: record_err() writes to extraction_errors
   └── entrypoint.py exits with status 1 if any item failed
   └── main.py detects non-zero exit, adds all batch items to retry_set

3. After all initial batches:
   └── main.py retries failed items individually (size=1)
   └── Up to MAX_RETRIES attempts per item
   └── Final failures are logged and cause main.py to exit(1)
```

## Configuration

Environment variables control retry behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_RETRIES` | 3 | Maximum retry attempts per failed item |
| `BATCH_SIZE` | 10 | Initial batch size for processing |
| `RETRY_BATCH_SIZE` | 1 | Batch size for retry attempts (typically 1) |

## Usage

### Direct Usage
```bash
export JOB_INPUT='[{"platform":"instagram","code":"ABC123"}]'
export MAX_RETRIES=3
export BATCH_SIZE=5
python main.py
```

### With Test Script
```bash
# Run test with existing job_input.json
./test/test_locally.sh

# Run retry queue specific test
python test/test_retry_queue.py
```

## Benefits

1. **Fault Tolerance**: Temporary failures (network issues, resource constraints) don't permanently fail items
2. **Isolation**: Individual item failures don't impact other items in the batch
3. **Visibility**: All failures are captured in `extraction_errors` table with full error details
4. **Configurability**: Retry behavior can be tuned per deployment environment
5. **Efficiency**: Failed items are retried individually to avoid re-processing successful items

## Error Capture Details

- **Database Errors**: Written to `extraction_errors` table via FK relationship
- **Exit Status**: Non-zero exit from entrypoint.py triggers retry queue logic
- **Retry Tracking**: Local retry_set maintains failed item codes between attempts
- **Final Failures**: Items that fail after MAX_RETRIES are logged with detailed error information

## Monitoring

Monitor retry queue effectiveness by:

1. **Exit Codes**: main.py exits 0 only if all items eventually succeed
2. **Log Analysis**: Search logs for retry phase indicators
3. **Database Queries**: Query `extraction_errors` table for failure patterns
4. **Timing**: Monitor retry overhead in pipeline execution time

## Testing

Use the included test script to validate retry functionality:

```bash
cd /home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline
python test/test_retry_queue.py
```

This test uses nonexistent video codes to simulate failures and verify that:
- Initial batch fails correctly
- Retry phase is triggered
- Individual retries are attempted
- Final failure is handled appropriately
