# Search Modules

This directory contains search utilities for querying the Qdrant vector database using both image and text inputs. These modules leverage the project's centralized embedding models to perform semantic similarity searches.

## Overview

The search modules provide command-line interfaces for:

- **Image Search**: Find similar images in the Qdrant collection using a query image
- **Text Search**: Find images in the Qdrant collection using natural language descriptions

Both modules use the same embedding models as the main extraction pipeline to ensure consistency in vector representations.

## Files

### `search_image.py`

Performs similarity search using image queries. Encodes the input image using the project's centralized embedding model and searches the Qdrant collection for visually similar images.

### `search_text.py`

Performs similarity search using text queries. Encodes the input text using the project's centralized embedding model and searches the Qdrant collection for semantically related images.

### `search_playground.py`

An interactive playground for testing and experimenting with search functionality.

### `samples/`

Directory containing sample images and data for testing the search functionality.

## Prerequisites

1. **Environment Setup**: Ensure you have the required environment variables in your `.env` file:

   ```
   QDRANT_URL=your_qdrant_server_url
   QDRANT_KEY=your_qdrant_api_key
   ```

2. **Dependencies**: Install the required Python packages:

   ```bash
   pip install qdrant-client pillow python-dotenv
   ```

3. **Qdrant Collection**: Ensure the target collection (default: `watched_frames`) exists in your Qdrant instance.

## Usage

### Image Search

Search for similar images using a query image:

```bash
python qdrant/search/search_image.py --image path/to/your/image.jpg
```

**Options:**

- `--image`: Path to the query image file (required)
- `--limit`: Number of results to return (default: 5)
- `--collection`: Name of the Qdrant collection to search (default: "watched_frames")

**Example:**

```bash
python qdrant/search/search_image.py --image samples/images/dog.png --limit 10
```

### Text Search

Search for images using natural language descriptions:

```bash
python qdrant/search/search_text.py --text "a dog playing on the grass"
```

**Options:**

- `--text`: Text query to embed (required)
- `--limit`: Number of results to return (default: 5)
- `--collection`: Name of the Qdrant collection to search (default: "watched_frames")

**Example:**

```bash
python qdrant/search/search_text.py --text "sunset over mountains" --limit 8
```

## Output Format

Both search modules provide consistent output formatting:

```
✅ Found 5 results for 'query_image.jpg':

--- Result 1 ---
  ID             : 12345
  Smiliarity     : 0.8542
  timestamp      : 2024-01-15T10:30:00Z
  frame_path     : /path/to/frame.jpg
  video_id       : video_001

--- Result 2 ---
  ID             : 12346
  Smiliarity     : 0.8234
  timestamp      : 2024-01-15T10:31:00Z
  frame_path     : /path/to/frame2.jpg
  video_id       : video_001
```

## Technical Details

### Embedding Models

Both modules use the centralized embedding functions from `src.infer_embeds`:

- `encode_image_batch()` for image encoding
- `encode_text_batch()` for text encoding

This ensures consistency with the main extraction pipeline and allows for easy model updates across the entire system.

### Vector Search

The modules perform cosine similarity search in the Qdrant vector database:

- Query vectors are computed using the same models as the indexed data
- Results are ranked by similarity score (higher is better)
- Payload data is included in results for context

### Error Handling

- Validates input files and environment variables
- Provides clear error messages for common issues
- Graceful handling of embedding and search failures

## Integration

These search modules are designed to work seamlessly with the main extraction pipeline:

- Use the same embedding models for consistency
- Target the same Qdrant collections
- Follow the same environment configuration patterns
- Maintain compatible data formats

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in your Python path
2. **Environment Variables**: Verify QDRANT_URL and QDRANT_KEY are set in `.env`
3. **Collection Not Found**: Check that the target collection exists in Qdrant
4. **Image Loading**: Ensure the image file exists and is in a supported format

### Debug Mode

For debugging, you can add verbose logging by modifying the scripts to include:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When modifying these search modules:

1. Maintain compatibility with the centralized embedding functions
2. Update this README.md with any new features or changes
3. Test with various input types and edge cases
4. Ensure error handling remains robust
