# Checkpoint/Resume Mechanism

This document describes the checkpoint/resume mechanism implemented for the extraction pipeline.

## Overview

The extraction pipeline now supports automatic checkpoint/resume functionality to handle interruptions gracefully. When the pipeline is stopped (either by Ctrl+C, system crash, or other interruption), it will automatically resume from the last successfully processed record when restarted.

## Features

- **Automatic Resume**: The pipeline automatically resumes from the last processed record
- **Dual Storage Options**: Supports both JSON file and database storage for checkpoints
- **Graceful Shutdown**: Handles Ctrl+C and other signals gracefully
- **Error Resilience**: Continues processing even if individual records fail
- **Batch Processing**: Processes records in configurable batches (default: 1000)

## Storage Options

### JSON File Storage (Default)
- **File Location**: `/home/quantium/labs/oriane/ExtractionPipeline/qdrant/scripts/extract/.checkpoint`
- **Format**: JSON with `last_processed_id` and `updated_at` fields
- **Benefits**: Simple, no database dependencies, easy to inspect
- **Use Case**: Recommended for most scenarios

### Database Storage
- **Table**: `public.extraction_checkpoint`
- **Schema**: `id BIGINT PRIMARY KEY, updated_at TIMESTAMP WITH TIME ZONE`
- **Benefits**: Centralized, transactional consistency
- **Use Case**: When multiple processes need coordination

## Usage

### Running the Pipeline

```bash
# Run with JSON checkpoint (default)
python main.py

# Run with database checkpoint
python -c "
from main import ExtractionPipeline
pipeline = ExtractionPipeline(use_json_checkpoint=False)
pipeline.run()
"
```

### Managing Checkpoints

Use the `checkpoint_utils.py` script to manage checkpoints:

```bash
# Show current checkpoint
python checkpoint_utils.py show

# Set checkpoint to specific ID
python checkpoint_utils.py set 12345

# Reset checkpoint (start from beginning)
python checkpoint_utils.py reset

# Use database storage instead of JSON
python checkpoint_utils.py --storage db show
```

### Setting Up Database Checkpoint

If using database storage, create the checkpoint table:

```sql
-- Run this SQL to create the checkpoint table
\i create_checkpoint_table.sql
```

## How It Works

1. **Startup**: The pipeline reads the last processed ID from the checkpoint
2. **Processing**: Records are processed in batches, starting from the checkpoint
3. **Checkpoint Updates**: After each successful batch, the checkpoint is updated
4. **Interruption**: If interrupted, the current batch position is saved
5. **Resume**: On restart, processing continues from the last checkpoint

## Configuration

### Batch Size
Default batch size is 1000 records. You can modify this:

```python
pipeline = ExtractionPipeline(batch_size=500)  # Process 500 records per batch
```

### Checkpoint Storage
Choose between JSON file and database:

```python
# JSON file (default)
pipeline = ExtractionPipeline(use_json_checkpoint=True)

# Database
pipeline = ExtractionPipeline(use_json_checkpoint=False)
```

## File Structure

```
qdrant/scripts/extract/
├── main.py                    # Main pipeline with checkpoint support
├── checkpoint_manager.py      # Checkpoint management logic
├── checkpoint_utils.py        # Command-line utilities
├── create_checkpoint_table.sql # Database table creation
├── models.py                  # Database models (includes ExtractionCheckpoint)
├── db.py                      # Database functions (includes checkpoint functions)
├── .checkpoint                # JSON checkpoint file (created automatically)
└── CHECKPOINT_README.md       # This documentation
```

## Error Handling

- **Individual Record Failures**: Pipeline continues processing other records
- **Batch Failures**: Checkpoint is not updated, allowing retry on restart
- **Signal Handling**: Graceful shutdown on Ctrl+C or system signals
- **File I/O Errors**: Proper error messages and fallback behavior

## Monitoring

The pipeline provides detailed logging:

```
Starting extraction pipeline...
Resuming from checkpoint: last processed ID = 12345
Processing batch of 1000 records (IDs: 12346 - 13346)
  Processing video extraction for record 12346
  Processing frame embedding for record 12346
Marked 1000 records as extracted
Updated checkpoint: last processed ID = 13346
Total records processed so far: 1000
```

## Best Practices

1. **Regular Monitoring**: Monitor the logs to ensure progress
2. **Checkpoint Verification**: Use `checkpoint_utils.py show` to verify progress
3. **Backup**: The JSON checkpoint file is small and can be backed up
4. **Resource Management**: Adjust batch size based on available memory/CPU
5. **Error Investigation**: Check logs for individual record failures

## Troubleshooting

### Pipeline Not Resuming
- Check if checkpoint file exists and is readable
- Verify database connectivity (if using database storage)
- Check file permissions

### Checkpoint Not Updating
- Ensure write permissions for the checkpoint file
- Check database connectivity and table existence
- Verify no errors in the batch processing

### Performance Issues
- Reduce batch size if memory usage is too high
- Increase batch size if processing is too slow
- Monitor database connection pool usage
