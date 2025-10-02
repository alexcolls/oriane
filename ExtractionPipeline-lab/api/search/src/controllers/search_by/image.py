import io
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

# Local services that wrap the heavy-lifting implementation details
try:
    from services import embeddings_service, qdrant_service  # when 'services' is on PYTHONPATH
except ImportError:  # pragma: no cover – fallback for package-relative layout
    from ...services import embeddings_service, qdrant_service

router = APIRouter()


class ImageSearchRequest(BaseModel):
    limit: int = 5


class SearchResult(BaseModel):
    id: str
    score: float
    payload: dict


@router.post("/", response_model=List[SearchResult])
async def search_by_image(
    file: UploadFile = File(..., description="The image file to search with."), limit: int = 5
) -> List[SearchResult]:
    """Search the **watched_frames** Qdrant collection by an uploaded image."""

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        # Read and validate image
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Empty image file.")

        # Convert bytes to PIL Image for processing
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if image.mode != "RGB":
            image = image.convert("RGB")

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(exc)}")

    # 1️⃣ Convert the image to a CLIP embedding using the central model
    try:
        vector = embeddings_service.get_image_embedding(image)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate image embedding: {str(exc)}"
        )

    # 2️⃣ Run semantic search against Qdrant
    try:
        hits = qdrant_service.search(vector=vector, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(exc)}")

    # 3️⃣ Normalise the raw ScoredPoint objects to the API schema
    results: List[SearchResult] = [
        SearchResult(id=str(hit.id), score=hit.score, payload=hit.payload or {}) for hit in hits
    ]

    return results
