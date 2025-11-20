"""
Document Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, BigInteger, JSON
from sqlalchemy.orm import relationship
from api.db import Base
import enum


class DocumentStatus(str, enum.Enum):
    """Document status enumeration"""
    UPLOADING = "uploading"      # Uploading
    PARSING = "parsing"          # Parsing
    EMBEDDING = "embedding"      # Generating embeddings
    READY = "ready"              # Ready
    FAILED = "failed"            # Failed


class DocumentType(str, enum.Enum):
    """Document type enumeration"""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    OTHER = "other"


class Document(Base):
    """Document table"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Basic information
    filename = Column(String(255), nullable=False, comment="Filename")
    file_hash = Column(String(64), unique=True, index=True, nullable=False, comment="File SHA256 hash")
    file_type = Column(Enum(DocumentType), nullable=False, comment="File type")
    file_size = Column(BigInteger, nullable=False, comment="File size in bytes")
    mime_type = Column(String(100), nullable=True, comment="MIME type")

    # Storage paths
    storage_path = Column(String(500), nullable=False, comment="Storage path")
    preview_path = Column(String(500), nullable=True, comment="Preview path")

    # Document metadata
    title = Column(String(500), nullable=True, comment="Document title")
    author = Column(String(200), nullable=True, comment="Author")
    subject = Column(String(500), nullable=True, comment="Subject")
    keywords = Column(Text, nullable=True, comment="Keywords comma-separated")
    page_count = Column(Integer, nullable=True, comment="Page count")
    word_count = Column(Integer, nullable=True, comment="Word count")

    # Parsed content
    parsed_text = Column(Text, nullable=True, comment="Parsed text content")
    metadata = Column(JSON, nullable=True, comment="Additional metadata JSON")

    # Status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADING, nullable=False, comment="Status")
    error_message = Column(Text, nullable=True, comment="Error message")

    # Owner
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="Owner user ID")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Creation time")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="Update time")
    parsed_at = Column(DateTime, nullable=True, comment="Parsing completion time")

    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    acl = relationship("ACL", back_populates="document", cascade="all, delete-orphan", uselist=False)

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"

    def to_dict(self, include_chunks=False):
        """Convert to dictionary"""
        result = {
            "id": self.id,
            "filename": self.filename,
            "file_hash": self.file_hash,
            "file_type": self.file_type.value,
            "file_size": self.file_size,
            "title": self.title,
            "author": self.author,
            "subject": self.subject,
            "keywords": self.keywords,
            "page_count": self.page_count,
            "word_count": self.word_count,
            "status": self.status.value,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "parsed_at": self.parsed_at.isoformat() if self.parsed_at else None,
        }

        if include_chunks:
            result["chunks"] = [chunk.to_dict() for chunk in self.chunks]

        return result
