# Qdrant Payload Schema Documentation

## Baseline Analysis & Target Schema Definition

This document outlines the current Qdrant payload schema used in the frame embeddings pipeline and defines the new canonical payload structure for future consistency and deterministic operations.

## Current Payload Schema (Baseline)

### Current Implementation Location

- **Primary file**: `/core/py/pipeline/embed_entrypoint.py` (lines 88-99)
- **Storage function**: `/core/py/pipeline/src/store_embeds.py`

### Current Payload Structure

```python
{
    "id": f"{code}_{frame_idx}",
    "vector": [float, ...],  # 512-dimensional CLIP embeddings
    "payload": {
        "video_code": str,        # Video identifier (e.g., Instagram shortcode)
        "frame_idx": int,         # Frame index number (0-based)
        "timestamp_s": float,     # Timestamp in seconds
        "frame_path": str,        # Full path to frame file
    }
}
```

### Current Field Analysis

#### Missing/Incorrect Fields:

- ❌ **No deterministic UUID**: Current `id` field uses simple concatenation `{code}_{frame_idx}` which lacks namespace isolation
- ❌ **No creation timestamp**: Missing `created_at` field for tracking when the record was created
- ❌ **Inconsistent naming**: Field names don't follow consistent conventions
- ❌ **No standardized path format**: `frame_path` contains full filesystem paths instead of relative paths

#### Current Field Mapping:

- `video_code` → ✅ **Correct** (keeping as-is)
- `frame_idx` → 🔄 **Rename** to `frame_number` for clarity
- `timestamp_s` → 🔄 **Rename** to `frame_second` for consistency
- `frame_path` → 🔄 **Standardize** to relative path format

## New Canonical Payload Schema

### Target Payload Structure

```python
{
    "id": str,           # Deterministic UUID5
    "vector": [float],   # 512-dimensional CLIP embeddings
    "payload": {
        "uuid": str,              # Deterministic UUID5 (same as id)
        "created_at": str,        # ISO-8601 UTC timestamp
        "video_code": str,        # Video identifier (unchanged)
        "frame_number": int,      # Frame index [was frame_idx]
        "frame_second": float,    # Frame timestamp [was timestamp_s]
        "path": str,             # Relative path (e.g., "instagram/DKOicvaMxAb/50_6.63.png")
    }
}
```

### Canonical Field Definitions

#### `uuid` (deterministic, str)

- **Type**: String (UUID5 format)
- **Purpose**: Deterministic, globally unique identifier
- **Generation**: See "Deterministic UUID Recipe" below
- **Example**: `"a1b2c3d4-e5f6-5789-a1b2-c3d4e5f67890"`

#### `created_at` (ISO-8601, UTC)

- **Type**: String (ISO-8601 format)
- **Purpose**: Track when the embedding record was created
- **Format**: `YYYY-MM-DDTHH:MM:SS.sssZ`
- **Example**: `"2024-07-07T15:30:45.123Z"`

#### `video_code` (str)

- **Type**: String
- **Purpose**: Platform-specific video identifier
- **Format**: Unchanged from current implementation
- **Example**: `"DKOicvaMxAb"` (Instagram shortcode)

#### `frame_number` (int) [was frame_idx]

- **Type**: Integer
- **Purpose**: Sequential frame index (0-based)
- **Renamed from**: `frame_idx`
- **Example**: `50`

#### `frame_second` (float) [was timestamp_s]

- **Type**: Float
- **Purpose**: Timestamp position in video (seconds)
- **Renamed from**: `timestamp_s`
- **Example**: `6.63`

#### `path` (str)

- **Type**: String
- **Purpose**: Standardized relative path to frame file
- **Format**: `{platform}/{video_code}/{frame_number}_{frame_second}.png`
- **Example**: `"instagram/DKOicvaMxAb/50_6.63.png"`

## Deterministic UUID Recipe

### UUID5 Generation Formula

```python
import uuid

NAMESPACE_URL = uuid.NAMESPACE_URL  # Standard UUID namespace for URLs
uuid_value = uuid.uuid5(
    NAMESPACE_URL,
    f"{video_code}_{frame_number}_{frame_second}"
)
```

### Implementation Example

```python
import uuid
from datetime import datetime

def generate_deterministic_uuid(video_code: str, frame_number: int, frame_second: float) -> str:
    """Generate deterministic UUID5 for frame embedding."""
    identifier = f"{video_code}_{frame_number}_{frame_second}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, identifier))

def create_canonical_payload(video_code: str, frame_number: int, frame_second: float, vector: list) -> dict:
    """Create payload using new canonical schema."""
    uuid_value = generate_deterministic_uuid(video_code, frame_number, frame_second)
    created_at = datetime.utcnow().isoformat() + "Z"

    return {
        "id": uuid_value,
        "vector": vector,
        "payload": {
            "uuid": uuid_value,
            "created_at": created_at,
            "video_code": video_code,
            "frame_number": frame_number,
            "frame_second": frame_second,
            "path": f"instagram/{video_code}/{frame_number}_{frame_second}.png"
        }
    }
```

## Migration Considerations

### Breaking Changes

1. **ID format**: Point IDs will change from `{code}_{frame_idx}` to UUID5 format
2. **Field renames**: `frame_idx` → `frame_number`, `timestamp_s` → `frame_second`
3. **Path format**: Full filesystem paths → Relative paths
4. **New required fields**: `uuid`, `created_at`

### Backwards Compatibility

- Consider implementing a migration script to update existing records
- Both old and new schemas could be supported during transition period
- Verification logic should be updated to handle both formats

## Collection Configuration

### Qdrant Collection Settings

- **Vector dimension**: 512 (CLIP embeddings)
- **Distance metric**: Cosine similarity
- **Collection name**: `watched_frames` (from settings.collection)

### Indexing Recommendations

Consider creating indexes on frequently queried payload fields:

- `video_code` (for video-specific queries)
- `created_at` (for temporal filtering)
- `frame_number` (for sequential access)

---

**Document Version**: 1.0
**Last Updated**: July 2024
**Author**: Alex Colls
**Status**: Approved for Implementation
