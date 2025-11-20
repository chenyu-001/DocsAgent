"""
Text Chunk Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from api.db import Base


class Chunk(Base):
    """Text chunk table - stored in PostgreSQL, vectors stored in Qdrant"""
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Associated document
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, comment="Document ID")

    # Text content
    text = Column(Text, nullable=False, comment="Chunk text content")
    text_hash = Column(String(64), index=True, nullable=False, comment="Text SHA256 hash")

    # Position information
    chunk_index = Column(Integer, nullable=False, comment="Chunk index in document starting from 0")
    page_number = Column(Integer, nullable=True, comment="Source page number")
    start_char = Column(Integer, nullable=True, comment="Start character position in document")
    end_char = Column(Integer, nullable=True, comment="End character position in document")

    # Vector ID in Qdrant
    vector_id = Column(String(100), unique=True, index=True, nullable=True, comment="Vector database point ID")

    # Additional metadata
    chunk_metadata = Column(Text, nullable=True, comment="Additional metadata JSON string")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Creation time")

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index("idx_document_chunk", "document_id", "chunk_index"),
    )

    def __repr__(self):
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index}, text='{preview}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "vector_id": self.vector_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
