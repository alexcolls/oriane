from collections import defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local services for embeddings and Qdrant search
try:
    from services import qdrant_service
except ImportError:  # pragma: no cover
    from ...services import qdrant_service

router = APIRouter()


class UserVideoSearchRequest(BaseModel):
    user_id: str
    video_id: str
    limit: int = 5


class FrameSearchResult(BaseModel):
    frame_id: str
    frame_number: int
    frame_second: float
    score: float
    payload: dict
    source_video_id: str


class VideoSearchResult(BaseModel):
    video_id: str
    total_frames: int
    frame_results: List[FrameSearchResult]


@router.post("/user-video", response_model=List[FrameSearchResult])
async def search_by_user_video(request: UserVideoSearchRequest) -> List[FrameSearchResult]:
    """Search watched_frames collection for embeddings matching a user's video frames."""

    # Retrieve all frame embeddings for the video from the user_videos collection
    try:
        frame_embeddings = qdrant_service.fetch_all_video_embeddings(
            collection="user_videos", user_id=request.user_id, video_id=request.video_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving video embeddings: {str(exc)}"
        )

    if not frame_embeddings:
        raise HTTPException(status_code=404, detail=f"No frames found for video {request.video_id}")

    # Search watched_frames for each frame embedding
    all_results = []

    for frame_vector, frame_metadata in frame_embeddings:
        try:
            hits = qdrant_service.search(
                vector=frame_vector, limit=request.limit, collection="watched_frames"
            )

            # Add frame metadata to each result
            for hit in hits:
                all_results.append(
                    FrameSearchResult(
                        frame_id=str(hit.id),
                        frame_number=(
                            frame_metadata.get("frame_number", 0) if frame_metadata else 0
                        ),
                        frame_second=(
                            frame_metadata.get("frame_second", 0.0) if frame_metadata else 0.0
                        ),
                        score=hit.score,
                        payload=hit.payload or {},
                        source_video_id=hit.payload.get("video_id", "unknown") if hit.payload else "unknown",
                    )
                )

        except Exception as exc:
            # Log error but continue with other frames
            print(f"Error searching with frame {frame_metadata}: {exc}")
            continue

    if not all_results:
        return []

    # Sort all results by score (highest to lowest - most similar to least similar)
    all_results.sort(key=lambda x: x.score, reverse=True)

    return all_results
