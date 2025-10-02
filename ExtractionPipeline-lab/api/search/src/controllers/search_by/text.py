from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local services that wrap the heavy-lifting implementation details
# from ...services import embeddings_service, qdrant_service
try:
    from services import embeddings_service, qdrant_service  # when 'services' is on PYTHONPATH
except ImportError:  # pragma: no cover – fallback for package-relative layout
    from ...services import embeddings_service, qdrant_service

router = APIRouter()


class TextSearchRequest(BaseModel):
    prompt: str
    limit: int = 5


class SearchResult(BaseModel):
    id: str
    score: float
    payload: dict


@router.post("/", response_model=list[SearchResult])
async def search_by_text(request: TextSearchRequest) -> list[SearchResult]:
    """Search the **watched_frames** Qdrant collection by a text *prompt*."""

    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty.")

    # 1️⃣  Convert the raw prompt to a CLIP embedding using the central model.
    vector = embeddings_service.get_text_embedding(request.prompt)

    # 2️⃣  Run semantic search against Qdrant.
    try:
        hits = qdrant_service.search(vector=vector, limit=request.limit)
    except Exception as exc:  # pragma: no cover – we just forward the error
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # 3️⃣  Normalise the raw ScoredPoint objects to the API schema.
    results: list[SearchResult] = [
        SearchResult(id=str(hit.id), score=hit.score, payload=hit.payload or {}) for hit in hits
    ]

    return results
