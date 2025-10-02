from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local services for embeddings and Qdrant search
try:
    from services import qdrant_service
except ImportError:  # pragma: no cover
    from ...services import qdrant_service

router = APIRouter()


class UserImageSearchRequest(BaseModel):
    user_id: str
    image_id: str
    limit: int = 5


class SearchResult(BaseModel):
    id: str
    score: float
    payload: dict


@router.post("/user-image", response_model=List[SearchResult])
async def search_by_user_image(request: UserImageSearchRequest) -> List[SearchResult]:
    """Search watched_frames collection for embeddings matching a user's image."""

    # Retrieve the image embedding from the user_images collection
    try:
        embedding, _ = qdrant_service.fetch_embedding(
            collection="user_images", user_id=request.user_id, entry_id=request.image_id
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error retrieving image embedding: {str(exc)}")

    # Run semantic search against Qdrant
    try:
        hits = qdrant_service.search(
            vector=embedding, limit=request.limit, collection="watched_frames"
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(exc)}")

    # Convert raw search results to the API schema
    results: List[SearchResult] = [
        SearchResult(id=str(hit.id), score=hit.score, payload=hit.payload or {}) for hit in hits
    ]

    return results
