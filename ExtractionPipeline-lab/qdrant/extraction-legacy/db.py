"""
Connect to OrianeAdmin database and extract insta_content table and proceed with the extraction pipeline
"""

import os
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from models import Base, ExtractionCheckpoint, ExtractionError, InstaContent
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

engine = create_engine(os.getenv("ORIANE_ADMIN_DB_URL"))
Session = sessionmaker(bind=engine)


@contextmanager
def DbSession():
    """
    Context manager for database sessions.
    Automatically handles session lifecycle and rollback on exceptions.
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def next_batch(size: int = 1000, last_id: Optional[str] = None) -> List[dict]:
    """
    Fetch the next batch of InstaContent records that need to be extracted.

    Args:
        size: Number of records to fetch (default: 1000)
        last_id: ID of the last processed record for pagination (default: None)

    Returns:
        List of dictionaries containing InstaContent data
    """
    with DbSession() as session:
        # For UUID-based records, we'll use a simple approach:
        # Get all unprocessed records, order by created_at, then filter in memory if we have a last_id
        query = (
            session.query(InstaContent)
            .filter(InstaContent.is_extracted == False)
            .order_by(InstaContent.created_at.asc())
        )

        # If we have a last_id, we need to skip records until we find the one after last_id
        if last_id:
            # First get the created_at timestamp of the last processed record
            last_record = session.query(InstaContent).filter(InstaContent.id == last_id).first()
            if last_record:
                # Get records with created_at greater than the last processed record
                # or created_at equal but id greater (for stable pagination)
                query = query.filter(
                    (InstaContent.created_at > last_record.created_at)
                    | (
                        (InstaContent.created_at == last_record.created_at)
                        & (InstaContent.id > last_id)
                    )
                )

        records = query.limit(size).all()
        # Convert SQLAlchemy objects to dictionaries to avoid detached instance errors
        return [
            {
                "id": record.id,
                "code": record.code,
                "username": record.username,
                "is_extracted": record.is_extracted,
                "is_embedded": record.is_embedded,
                "created_at": record.created_at,
            }
            for record in records
        ]


def mark_extracted(id_list: List[str]) -> None:
    """
    Mark the specified InstaContent records as extracted.

    Args:
        id_list: List of InstaContent IDs (UUIDs) to mark as extracted
    """
    if not id_list:
        return

    with DbSession() as session:
        session.execute(
            text(
                """
            UPDATE public.insta_content
            SET is_extracted = true
            WHERE id = ANY(:id_list)
            """
            ),
            {"id_list": id_list},
        )


def mark_embedded(id_list: List[str]) -> None:
    """
    Mark the specified InstaContent records as embedded.

    Args:
        id_list: List of InstaContent IDs (UUIDs) to mark as embedded
    """
    if not id_list:
        return

    with DbSession() as session:
        session.execute(
            text(
                """
            UPDATE public.insta_content
            SET is_embedded = true
            WHERE id = ANY(:id_list)
            """
            ),
            {"id_list": id_list},
        )


def get_checkpoint() -> Optional[str]:
    """
    Get the last processed ID from the checkpoint table.

    Returns:
        The last processed ID, or None if no checkpoint exists
    """
    with DbSession() as session:
        checkpoint = session.query(ExtractionCheckpoint).first()
        return str(checkpoint.id) if checkpoint else None


def update_checkpoint(last_processed_id: str) -> None:
    """
    Update the checkpoint with the last processed ID.

    Args:
        last_processed_id: The ID of the last successfully processed record
    """
    with DbSession() as session:
        checkpoint = session.query(ExtractionCheckpoint).first()
        if checkpoint:
            checkpoint.id = last_processed_id
            checkpoint.updated_at = datetime.utcnow()
        else:
            checkpoint = ExtractionCheckpoint(id=last_processed_id)
            session.add(checkpoint)


def extract_insta_content():
    """
    Legacy function for backward compatibility.
    Extract all insta_content records.
    """
    with DbSession() as session:
        insta_content = (
            session.query(InstaContent)
            .from_statement(text("SELECT * FROM public.insta_content"))
            .all()
        )
        return insta_content


if __name__ == "__main__":
    extract_insta_content()
