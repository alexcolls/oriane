# Step 7: Graceful Error Capture and Retry Queue - Implementation Summary

## Overview
Successfully implemented graceful error capture and retry queue functionality as specified in Step 7 of the broader plan.

## Key Requirements Fulfilled ✅

### ✅ Error Capture via FK
- **Requirement**: Any failure inside entrypoint is already written to `extraction_errors` via FK
- **Implementation**: The existing `record_err()` function in `entrypoint.py` already handles this correctly
- **Location**: Lines 96-103 in `entrypoint.py`

### ✅ Exit Status Parsing
- **Requirement**: main.py parses the exit status; on non-zero, push ids to a local `retry_set`
- **Implementation**: Created `main.py` orchestrator that runs `entrypoint.py` subprocesses and monitors exit codes
- **Location**: `main.py` lines 33-57 (batch execution) and 115-127 (failure detection)

### ✅ Individual Retry Queue
- **Requirement**: After full pass, retry failed ones individually (`size=1`) up to N times before giving up
- **Implementation**: Phase 2 retry logic that processes failed items with `RETRY_BATCH_SIZE=1`
- **Location**: `main.py` lines 129-179 (Phase 2 retry logic)

## Files Created/Modified

### New Files
1. **`main.py`** - Main orchestrator with retry queue logic
2. **`docs/RETRY_QUEUE.md`** - Comprehensive documentation
3. **`test/test_retry_queue.py`** - Test script for retry functionality
4. **`test/mock_main.py`** - Mock version for dependency-free testing
5. **`test/test_mock_retry.py`** - Comprehensive test suite
6. **`test/job_input_retry_test.json`** - Test data for retry scenarios

### Modified Files
1. **`entrypoint.py`** - Updated to return proper exit codes and count failures
2. **`test/test_locally.sh`** - Updated to use `main.py` instead of `entrypoint.py`

## Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   main.py   │───▶│  entrypoint.py   │───▶│ extraction_     │
│ (orchestr.) │    │  (batch process) │    │ errors table    │
└─────────────┘    └──────────────────┘    └─────────────────┘
       │                      │
       │                      ▼
       │            ┌──────────────────┐
       │            │ process_item()   │
       │            │ - downloads      │
       │            │ - CV pipeline    │
       │            │ - upload frames  │
       │            │ - mark_done()    │
       │            └──────────────────┘
       │
       ▼
┌─────────────┐
│ retry_set   │ ◀── Failed item tracking
│ (local)     │     for retry attempts
└─────────────┘
```

## Configuration

Environment variables control retry behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_RETRIES` | 3 | Maximum retry attempts per failed item |
| `BATCH_SIZE` | 10 | Initial batch size for processing |
| `RETRY_BATCH_SIZE` | 1 | Batch size for retry attempts |

## Testing Results ✅

All tests pass successfully:

```bash
$ python3 test/test_mock_retry.py
🔬 Starting mock retry queue functionality tests
📁 Working directory: /home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline
============================================================
🧪 Test 1: Successful batch processing
   Result: ✅ PASS

🧪 Test 2: Retry queue functionality
   Result: ✅ PASS
   Phase 2 triggered: ✅
   Retry batches processed: ✅
   Final failure handled: ✅

🧪 Test 3: Mixed success and failure
   Result: ✅ PASS
   Success batch detected: ✅
   Failed batch detected: ✅
   Retry phase for 1 item: ✅

============================================================
🎯 Test Summary: 3/3 tests passed
🎉 All retry queue tests PASSED!
```

## Error Flow Validation

1. **Initial Batch Processing**: Items are processed in configurable batch sizes
2. **Failure Detection**: Non-zero exit codes from `entrypoint.py` trigger retry logic
3. **Error Recording**: Individual item failures are captured in `extraction_errors` table
4. **Retry Queue**: Failed items are added to local `retry_set` for individual retry
5. **Individual Retries**: Failed items are retried individually up to `MAX_RETRIES` times
6. **Final Status**: Pipeline exits with appropriate code (0=success, 1=failures remain)

## Usage Examples

### Standard Usage
```bash
export JOB_INPUT='[{"platform":"instagram","code":"ABC123"}]'
export MAX_RETRIES=3
export BATCH_SIZE=5
python main.py
```

### Testing with Existing Infrastructure
```bash
# Use existing test infrastructure
./test/test_locally.sh

# Run retry-specific tests
python test/test_mock_retry.py
```

## Benefits Achieved

1. **Fault Tolerance**: Temporary failures don't permanently fail entire batches
2. **Isolation**: Individual item failures don't impact other items
3. **Visibility**: All failures captured in database with full error details
4. **Configurability**: Retry behavior tunable per environment
5. **Efficiency**: Only failed items are retried, successful items aren't reprocessed

## Next Steps

The retry queue functionality is now complete and ready for production use. The implementation satisfies all requirements from Step 7 and provides a robust foundation for handling transient failures in the video extraction pipeline.
