"""
Phase 6 – Embedded status verification
──────────────────────────────────────
After pipeline finishes for a batch, check that each `code` now exists in
Qdrant `watched_frames` (vector count ≥1).

Use the Python Qdrant client with absolute URL from env.
Only if present: add id to `mark_embedded()`, otherwise leave untouched for a later re-run.

Public functions:
──────────────────
* `verify_batch_embedded(codes: List[str]) -> Dict[str, bool]`
    Check which codes have vectors in Qdrant

* `mark_embedded_codes(codes: List[str]) -> None`
    Mark codes as embedded in the database if they have vectors in Qdrant
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List

from config.env_config import settings
from config.logging_config import configure_logging
from config.profiler import profile
from qdrant_client import QdrantClient

log = configure_logging()

# Database imports - handle missing dependencies gracefully
try:
    # Add the qdrant scripts path to sys.path to import db module
    qdrant_scripts_path = "/home/quantium/labs/oriane/ExtractionPipeline/qdrant/scripts/extract"
    if qdrant_scripts_path not in sys.path:
        sys.path.append(qdrant_scripts_path)

    from db import mark_embedded, next_batch
    from models import InstaContent
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    log.warning(f"Database dependencies not available: {e}")

    # Create stub functions if DB not available
    def mark_embedded(id_list: List[int]) -> None:
        log.warning("mark_embedded called but DB not available")

    def _get_content_ids_by_codes(codes: List[str]) -> Dict[str, int]:
        log.warning("_get_content_ids_by_codes called but DB not available")
        return {}


_QD: QdrantClient | None = None  # singleton


def _client() -> QdrantClient:
    """Lazy initialiser for Qdrant client."""
    global _QD
    if _QD is None:
        if not settings.qdrant_url:
            raise ValueError("QDRANT_URL environment variable is required")

        _QD = QdrantClient(
            url=settings.qdrant_url.rstrip("/"),
            api_key=settings.qdrant_key or None,
            prefer_grpc=True,
        )
        log.info(f"🔗 [qdrant] connected → {settings.qdrant_url}/")
    return _QD


def _get_content_ids_by_codes(codes: List[str]) -> Dict[str, int]:
    """
    Get InstaContent IDs for the given codes.

    Args:
        codes: List of video codes to look up

    Returns:
        Dictionary mapping code -> id for found codes
    """
    if not codes:
        return {}

    try:
        # Get database URL from environment
        db_url = os.getenv("ORIANE_ADMIN_DB_URL")
        if not db_url:
            log.warning("ORIANE_ADMIN_DB_URL not set, cannot look up content IDs")
            return {}

        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)

        with Session() as session:
            result = session.execute(
                text(
                    """
                    SELECT code, id FROM public.insta_content
                    WHERE code = ANY(:codes)
                """
                ),
                {"codes": codes},
            )

            return {row.code: row.id for row in result}

    except Exception as e:
        log.error(f"Failed to get content IDs for codes: {e}")
        return {}


@profile
def verify_batch_embedded(codes: List[str]) -> Dict[str, bool]:
    """
    Check which codes have vectors in Qdrant watched_frames collection.

    Args:
        codes: List of video codes to check

    Returns:
        Dictionary mapping code -> boolean (True if vectors exist, False otherwise)
    """
    if not codes:
        log.warning("[verify] no codes to verify")
        return {}

    log.info(f"[verify] checking {len(codes)} codes for embedded vectors")

    try:
        client = _client()
        results = {}

        for code in codes:
            try:
                # Search for vectors with this video_code in payload
                search_result = client.scroll(
                    collection_name=settings.collection,
                    scroll_filter={"must": [{"key": "video_code", "match": {"value": code}}]},
                    limit=1,  # We only need to know if at least 1 exists
                    with_payload=False,  # Don't need payload data, just count
                    with_vectors=False,  # Don't need vectors, just count
                )

                # Check if we found any vectors for this code
                has_vectors = len(search_result[0]) > 0
                results[code] = has_vectors

                if has_vectors:
                    log.info(f"✅ [verify] {code}: vectors found")
                else:
                    log.warning(f"⚠️ [verify] {code}: no vectors found")

            except Exception as e:
                log.error(f"❌ [verify] {code}: error checking vectors - {e}")
                results[code] = False

        embedded_count = sum(results.values())
        log.info(f"[verify] {embedded_count}/{len(codes)} codes have embedded vectors")

        return results

    except Exception as e:
        log.error(f"Failed to verify embedded status: {e}")
        return {code: False for code in codes}


@profile
def mark_embedded_codes(codes: List[str]) -> None:
    """
    Mark codes as embedded in the database if they have vectors in Qdrant.
    Only codes with vectors present will be marked as embedded.

    Args:
        codes: List of video codes to check and potentially mark as embedded
    """
    if not codes:
        log.warning("[mark_embedded] no codes to process")
        return

    log.info(f"[mark_embedded] processing {len(codes)} codes")

    # First, verify which codes have vectors in Qdrant
    verification_results = verify_batch_embedded(codes)

    # Get codes that have vectors
    codes_with_vectors = [code for code, has_vectors in verification_results.items() if has_vectors]

    if not codes_with_vectors:
        log.info("[mark_embedded] no codes have vectors, skipping database update")
        return

    # Get database IDs for codes with vectors
    code_to_id = _get_content_ids_by_codes(codes_with_vectors)

    if not code_to_id:
        log.warning("[mark_embedded] no database IDs found for codes with vectors")
        return

    # Mark the IDs as embedded
    ids_to_mark = list(code_to_id.values())

    try:
        mark_embedded(ids_to_mark)
        log.info(
            f"✅ [mark_embedded] marked {len(ids_to_mark)} records as embedded: {list(code_to_id.keys())}"
        )

        # Log codes that were not marked
        not_marked = set(codes_with_vectors) - set(code_to_id.keys())
        if not_marked:
            log.warning(
                f"⚠️ [mark_embedded] codes with vectors but no DB records: {list(not_marked)}"
            )

    except Exception as e:
        log.error(f"❌ [mark_embedded] failed to mark codes as embedded: {e}")


def verify_single_code(code: str) -> bool:
    """
    Check if a single code has vectors in Qdrant.

    Args:
        code: Video code to check

    Returns:
        True if vectors exist, False otherwise
    """
    results = verify_batch_embedded([code])
    return results.get(code, False)


if __name__ == "__main__":
    # Example usage for testing
    test_codes = ["sample_code_1", "sample_code_2"]

    log.info("Testing embedded status verification...")

    # Test verification
    results = verify_batch_embedded(test_codes)
    log.info(f"Verification results: {results}")

    # Test marking embedded (only if vectors exist)
    mark_embedded_codes(test_codes)
