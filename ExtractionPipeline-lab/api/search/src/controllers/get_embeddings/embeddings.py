import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local services for Qdrant operations
try:
    from services import qdrant_service
except ImportError:
    from ...services import qdrant_service

logger = logging.getLogger(__name__)

# Constants
ALLOWED_COLLECTIONS = ["user_images", "user_videos", "watched_frames"]

router = APIRouter()


class GetEmbeddingsRequest(BaseModel):
    collection_name: str
    embedding_id: str


class EmbeddingsResponse(BaseModel):
    embedding_id: str
    collection_name: str
    vector: List[float]
    payload: Dict[str, Any]


@router.post("/", response_model=EmbeddingsResponse)
async def get_embeddings(request: GetEmbeddingsRequest) -> EmbeddingsResponse:
    """
    Retrieve embeddings by collection name and embedding ID.

    Args:
        request (GetEmbeddingsRequest): Contains collection_name and embedding_id

    Returns:
        EmbeddingsResponse: Response with the embedding vector and payload

    Raises:
        HTTPException(400): If the collection name is invalid or embedding_id is empty.
        HTTPException(404): If no embedding is found.
        HTTPException(500): If retrieval from Qdrant fails.
    """

    # Validate collection name
    if request.collection_name not in ALLOWED_COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid collection name. Must be one of: {', '.join(ALLOWED_COLLECTIONS)}",
        )

    # Validate embedding id is not empty
    if not request.embedding_id.strip():
        raise HTTPException(status_code=400, detail="Embedding ID must be a non-empty string.")

    try:
        # Fetch the embedding by ID from the specified collection
        client = qdrant_service._client()

        points = client.retrieve(
            collection_name=request.collection_name,
            ids=[request.embedding_id],
            with_payload=True,
            with_vectors=True,
        )

        if not points:
            raise HTTPException(
                status_code=404,
                detail=f"No embedding found with ID {request.embedding_id} in collection {request.collection_name}",
            )

        point = points[0]

        if not point.vector:
            raise HTTPException(
                status_code=404, detail=f"No vector found for embedding ID {request.embedding_id}"
            )

        return EmbeddingsResponse(
            embedding_id=request.embedding_id,
            collection_name=request.collection_name,
            vector=point.vector,
            payload=point.payload or {},
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as exc:
        logger.error(
            f"Failed to fetch embedding ID {request.embedding_id} from collection {request.collection_name}: {exc}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve embeddings: {str(exc)}")
