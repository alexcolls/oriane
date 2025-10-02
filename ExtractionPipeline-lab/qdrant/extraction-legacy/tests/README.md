# Extraction Pipeline Smoke Tests

This directory contains unit smoke tests for the Qdrant extraction pipeline.

## Test Coverage

The test suite includes smoke tests for the following components:

### 1. `next_batch` Function Tests
- **Max 1000 Records**: Verifies that `next_batch` never returns more than 1000 records
- **Last ID Pagination**: Ensures `last_id` parameter is respected for proper pagination
- **Custom Batch Size**: Tests custom batch size functionality
- **Empty Results**: Handles cases when no records are found

### 2. Checkpoint Crash Survival Tests
- **JSON Checkpoint Persistence**: Simulates application crash and verifies checkpoint survival
- **File Corruption Handling**: Tests graceful handling of corrupted checkpoint files
- **Directory Creation**: Ensures checkpoint directories are created as needed
- **Concurrent Access**: Simulates multiple processes accessing the same checkpoint

### 3. Qdrant Client `mark_embedded` Tests
- **Valid IDs**: Tests marking records as embedded with valid ID lists
- **Empty List Handling**: Verifies graceful handling of empty ID lists
- **Single ID**: Tests functionality with single ID
- **Database Error Handling**: Ensures proper error handling for database failures
- **Parameter Validation**: Validates different input parameter types

## Running the Tests

### Method 1: Using the Test Runner Script
```bash
cd /home/quantium/labs/oriane/ExtractionPipeline/qdrant/scripts/extract/tests
./run_tests.py
```

### Method 2: Using pytest directly
```bash
# Install dependencies first
pip install pytest>=7.0.0 pytest-mock>=3.6.0

# Run tests
cd /home/quantium/labs/oriane/ExtractionPipeline/qdrant/scripts/extract
python -m pytest tests/test_smoke.py -v
```

### Method 3: Run individual test classes
```bash
# Test only next_batch functionality
python -m pytest tests/test_smoke.py::TestNextBatch -v

# Test only checkpoint functionality
python -m pytest tests/test_smoke.py::TestCheckpointManager -v

# Test only Qdrant client functionality
python -m pytest tests/test_smoke.py::TestQdrantClientStub -v
```

## Test Files

- `test_smoke.py` - Main test file containing all smoke tests
- `conftest.py` - Pytest configuration and shared fixtures
- `run_tests.py` - Test runner script with dependency installation
- `README.md` - This documentation file

## Dependencies

The tests require the following packages:
- `pytest>=7.0.0` - Testing framework
- `pytest-mock>=3.6.0` - Mocking utilities
- `sqlalchemy>=1.4.0` - Database ORM (already in main requirements)
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter (already in main requirements)

## Mocking Strategy

The tests use comprehensive mocking to avoid dependencies on:
- Actual database connections
- File system operations (except for temporary files)
- External services

This ensures tests run quickly and reliably in any environment.

## Test Philosophy

These are **smoke tests** designed to verify that:
1. Core functions behave correctly under normal conditions
2. Error conditions are handled gracefully
3. Key business logic constraints are enforced (e.g., max 1000 records)
4. State persistence mechanisms work correctly

The tests focus on critical functionality rather than exhaustive edge case coverage.
