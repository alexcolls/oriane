# User Content Search Endpoints

This document describes the user content search endpoints that allow users to search the `watched_frames` collection using their own uploaded images and videos as queries.

## Overview

These endpoints enable searching the watched content database using embeddings from user-uploaded content:

- **Image Search**: Uses a single embedding from a user's uploaded image to search `watched_frames`
- **Video Search**: Uses multiple embeddings from all frames of a user's uploaded video to search `watched_frames`, returning results grouped by matched videos

## Architecture

### User Collections
- `user_images`: Stores embeddings and metadata for user-uploaded images
- `user_videos`: Stores embeddings and metadata for individual frames of user-uploaded videos

### Search Target
- `watched_frames`: The collection containing embeddings from watched content (movies, shows, etc.)

## API Endpoints

### 1. Search by User Image

**Endpoint**: `POST /search-by-user-content/user-image`

Retrieves the embedding for a specific user image and searches the `watched_frames` collection.

**Request Body**:
```json
{
  "user_id": "string",
  "image_id": "string",
  "limit": 5
}
```

**Response**:
```json
[
  {
    "id": "string",
    "score": 0.95,
    "payload": {
      "video_id": "matched-video-id",
      "frame_number": 42,
      "timestamp": "2024-01-15T10:30:00Z",
      "...": "other metadata"
    }
  }
]
```

### 2. Search by User Video

**Endpoint**: `POST /search-by-user-content/user-video`

Retrieves embeddings for all frames of a user's video and searches the `watched_frames` collection with each frame. Results are grouped by matched video and sorted by highest scoring frame.

**Request Body**:
```json
{
  "user_id": "string",
  "video_id": "string",
  "limit": 5
}
```

**Response**:
```json
[
  {
    "video_id": "matched-video-1",
    "total_frames": 3,
    "frame_results": [
      {
        "frame_id": "result-frame-1",
        "frame_number": 1,
        "frame_second": 1.5,
        "score": 0.95,
        "payload": {
          "video_id": "matched-video-1",
          "frame_number": 10,
          "...": "other metadata"
        }
      },
      {
        "frame_id": "result-frame-2",
        "frame_number": 2,
        "frame_second": 3.0,
        "score": 0.88,
        "payload": {
          "video_id": "matched-video-1",
          "frame_number": 15,
          "...": "other metadata"
        }
      }
    ]
  }
]
```

## Implementation Details

### Qdrant Service Functions

#### `fetch_embedding(collection, user_id, entry_id)`
- Retrieves a single embedding vector and payload from the specified collection
- Validates that the entry belongs to the specified user
- Returns `(vector, payload)` tuple

#### `fetch_all_video_embeddings(collection, user_id, video_id)`
- Retrieves all frame embeddings for a specific video
- Filters by both `user_id` and `video_id`
- Sorts results by `frame_number`
- Returns list of `(vector, payload)` tuples

### Video Search Logic

1. **Retrieve Video Frames**: Fetch all embeddings for the user's video from `user_videos`
2. **Multi-Frame Search**: Search `watched_frames` with each frame embedding
3. **Result Aggregation**: Collect all search results with frame metadata
4. **Video Grouping**: Group results by `video_id` from search payload
5. **Sorting**: Sort frames within videos by `frame_number`, sort videos by highest scoring frame

## Error Handling

### Common Error Responses

**401 Unauthorized**: Missing or invalid API key
```json
{
  "detail": "Unauthorized"
}
```

**500 Internal Server Error**: Embedding retrieval failed
```json
{
  "detail": "Error retrieving image embedding: No entry found with ID xyz"
}
```

**404 Not Found**: Video has no frames (video search only)
```json
{
  "detail": "No frames found for video abc123"
}
```

## Authentication

All endpoints require API key authentication via the `X-API-Key` header.

## Performance Considerations

- **Video Search**: Performs multiple searches (one per video frame), so larger videos will take longer
- **Result Limits**: The `limit` parameter applies to each individual frame search, not the final grouped results
- **Caching**: Consider caching video frame embeddings for frequently searched videos

## Testing

Tests are located in `tests/test_user_content_search.py` and cover:

- Successful image and video searches
- Error handling for missing content
- Authentication requirements
- Response format validation

## Dependencies

- **FastAPI**: Web framework
- **Qdrant Client**: Vector database operations
- **Pydantic**: Request/response validation
- **Services**: `qdrant_service` for database operations

## Related Documentation

- [Video Processing Pipeline](VIDEO_PROCESSING.md): How user videos are processed and stored
- [Add Content Endpoints](controllers/add_content/README.md): How to upload images and videos
