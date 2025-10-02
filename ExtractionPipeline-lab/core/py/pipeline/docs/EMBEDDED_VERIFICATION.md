# Embedded Status Verification (Step 6)

## Overview

After the pipeline finishes processing a batch of videos, the embedded status verification step checks that each video's frames have been successfully embedded as vectors in the Qdrant vector database. Only videos with confirmed vector embeddings are marked as `is_embedded = true` in the database.

## Purpose

This verification step ensures data consistency between:
- The PostgreSQL database (tracks processing status)
- The Qdrant vector database (stores actual embeddings)

Without this verification, database records might be marked as embedded even if the vector storage failed, leading to inconsistent state.

## How It Works

### 1. Batch Collection
During pipeline processing, successfully processed video codes are collected in a list.

### 2. Vector Verification
For each code, the system queries Qdrant to check if vectors exist:
```python
# Search for vectors with video_code in payload
search_result = client.scroll(
    collection_name=settings.collection,
    scroll_filter={
        "must": [{"key": "video_code", "match": {"value": code}}]
    },
    limit=1  # Only need to know if ≥1 exists
)
```

### 3. Database Marking
Only codes with confirmed vectors are marked as embedded:
```sql
UPDATE public.insta_content
SET is_embedded = true, embedded_at = :embedded_at
WHERE id = ANY(:id_list)
```

## Configuration

### Required Environment Variables

```bash
# Qdrant Configuration
QDRANT_URL=https://your-qdrant-endpoint:6333
QDRANT_KEY=your-api-key  # Optional
QDRANT_COLLECTION=watched_frames
QDRANT_DIM=512

# Database Configuration
ORIANE_ADMIN_DB_URL=postgresql://user:pass@host:port/db
```

### Optional Settings

- `VP_BATCH_SIZE`: Controls batch size for Qdrant operations (default: 8)
- Collection name can be changed via `QDRANT_COLLECTION`

## Integration

### In Main Pipeline
The verification step is automatically called after batch processing:

```python
# Step 6: Embedded status verification
if processed_codes:
    log.info(f"🔍 [verify] checking embedded status for {len(processed_codes)} processed codes")
    try:
        mark_embedded_codes(processed_codes)
        log.info("✅ [verify] embedded status verification complete")
    except Exception as e:
        log.error(f"❌ [verify] embedded status verification failed: {e}")
```

### Standalone Usage
The module can also be used independently:

```python
from src.verify_embedded import mark_embedded_codes, verify_batch_embedded

# Check which codes have vectors
results = verify_batch_embedded(["code1", "code2", "code3"])
# Returns: {"code1": True, "code2": False, "code3": True}

# Mark codes as embedded (only those with vectors)
mark_embedded_codes(["code1", "code2", "code3"])
# Only code1 and code3 will be marked in database
```

## Functions

### `verify_batch_embedded(codes: List[str]) -> Dict[str, bool]`
Checks which codes have vectors in Qdrant.

**Parameters:**
- `codes`: List of video codes to check

**Returns:**
- Dictionary mapping code → boolean (True if vectors exist)

### `mark_embedded_codes(codes: List[str]) -> None`
Marks codes as embedded in database if they have vectors in Qdrant.

**Parameters:**
- `codes`: List of video codes to check and potentially mark

### `verify_single_code(code: str) -> bool`
Convenience function to check a single code.

**Parameters:**
- `code`: Single video code to check

**Returns:**
- True if vectors exist, False otherwise

## Error Handling

### Connection Failures
- Qdrant connection failures are logged and treated as "no vectors found"
- Database connection failures are logged but don't stop the pipeline
- Missing environment variables cause graceful degradation

### Partial Failures
- If some codes can be verified but others fail, successful ones are still marked
- Each code is processed independently to maximize success rate

### Logging
All operations are logged with appropriate levels:
- `INFO`: Normal operations and results
- `WARNING`: Missing vectors or non-critical issues
- `ERROR`: Connection failures or critical errors

## Testing

Run the test script to verify setup:

```bash
cd /home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline
python test_verify_embedded.py
```

The test will verify:
1. Environment configuration
2. Qdrant connection and collection existence
3. Verification logic with sample codes
4. Database connection for marking operations

## Monitoring

### Key Metrics
- Codes processed vs codes with vectors
- Database marking success rate
- Qdrant query response times

### Log Messages
- `✅ [verify] {code}: vectors found` - Vector verification successful
- `⚠️ [verify] {code}: no vectors found` - No vectors for this code
- `❌ [verify] {code}: error checking vectors` - Verification failed
- `✅ [mark_embedded] marked N records as embedded` - Database update successful

## Troubleshooting

### Common Issues

1. **No vectors found for processed codes**
   - Check if Qdrant upsert step completed successfully
   - Verify collection name matches between pipeline and verification
   - Check Qdrant logs for storage errors

2. **Database marking failures**
   - Verify `ORIANE_ADMIN_DB_URL` is set correctly
   - Check database connectivity and permissions
   - Ensure target codes exist in `insta_content` table

3. **Connection timeouts**
   - Check network connectivity to Qdrant
   - Verify Qdrant endpoint URL and API key
   - Consider increasing timeout settings

### Debug Mode
Enable debug logging for detailed operation traces:

```bash
export LOG_LEVEL=DEBUG
python entrypoint.py
```
