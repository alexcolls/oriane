"""
SQLAlchemy models for the extraction pipeline.
"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class InstaContent(Base):
    """
    SQLAlchemy model for Instagram content data.
    Maps to the public.insta_content table.
    """

    __tablename__ = "insta_content"
    __table_args__ = {"schema": "public"}

    # Primary key - UUID type
    id = Column(String, primary_key=True)

    # Core content fields
    media_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    status = Column(String(50), default="active")
    code = Column(String(255), nullable=False)
    caption = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    publish_date = Column(DateTime(timezone=True), nullable=False)
    last_refreshed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Status flags
    is_monitored = Column(Boolean, default=False)
    is_watched = Column(Boolean, default=False)
    is_extracted = Column(Boolean, default=False)
    is_embedded = Column(Boolean, default=False)
    is_removed = Column(Boolean, default=False)
    is_downloaded = Column(Boolean, default=True)
    is_cropped = Column(Boolean, default=False)

    # Metrics
    ig_play_count = Column(Integer, default=0)
    reshare_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)

    # Media URLs
    video_url = Column(String)
    image_url = Column(String)

    # Additional metadata
    duration = Column(String)  # Real type in DB
    frames = Column(Integer)
    search_text = Column(Text)

    # Array fields (stored as text in simplified model)
    coauthor_producers = Column(Text)
    monitored_by = Column(Text)

    # Relationship to extraction errors
    extraction_errors = relationship("ExtractionError", back_populates="insta_content")

    def __repr__(self):
        return f"<InstaContent(id={self.id}, code='{self.code}', is_extracted={self.is_extracted}, is_embedded={self.is_embedded})>"


class ExtractionError(Base):
    """
    SQLAlchemy model for tracking extraction failures.
    Maps to the public.extraction_errors table.
    """

    __tablename__ = "extraction_errors"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    insta_content_id = Column(Integer, ForeignKey("public.insta_content.id"), nullable=False)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    error_details = Column(Text)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to insta_content
    insta_content = relationship("InstaContent", back_populates="extraction_errors")

    def __repr__(self):
        return f"<ExtractionError(id={self.id}, insta_content_id={self.insta_content_id}, error_type='{self.error_type}')>"


class ExtractionCheckpoint(Base):
    """
    SQLAlchemy model for tracking extraction progress.
    Maps to the public.extraction_checkpoint table.
    """

    __tablename__ = "extraction_checkpoint"
    __table_args__ = {"schema": "public"}

    id = Column(String, primary_key=True)  # Store UUID as string
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ExtractionCheckpoint(id={self.id}, updated_at={self.updated_at})>"
