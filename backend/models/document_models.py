"""
ác!ã
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, BigInteger, JSON
from sqlalchemy.orm import relationship
from api.db import Base
import enum


class DocumentStatus(str, enum.Enum):
    """ác∂ö>"""
    UPLOADING = "uploading"      # 
 -
    PARSING = "parsing"          # „ê-
    EMBEDDING = "embedding"      # œ-
    READY = "ready"              # 1Í
    FAILED = "failed"            # 1%


class DocumentType(str, enum.Enum):
    """ác{ãö>"""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    OTHER = "other"


class Document(Base):
    """ách"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # áˆ·o
    filename = Column(String(255), nullable=False, comment="üÀáˆ")
    file_hash = Column(String(64), unique=True, index=True, nullable=False, comment="áˆ SHA256 »")
    file_type = Column(Enum(DocumentType), nullable=False, comment="áˆ{ã")
    file_size = Column(BigInteger, nullable=False, comment="áˆ'WÇ	")
    mime_type = Column(String(100), nullable=True, comment="MIME {ã")

    # X®ÔÑ
    storage_path = Column(String(500), nullable=False, comment="X®ÔÑ")
    preview_path = Column(String(500), nullable=True, comment="Ñ»áˆÔÑ")

    # ácCpn
    title = Column(String(500), nullable=True, comment="ácò")
    author = Column(String(200), nullable=True, comment="\")
    subject = Column(String(500), nullable=True, comment=";ò")
    keywords = Column(Text, nullable=True, comment="s.Õ˜î	")
    page_count = Column(Integer, nullable=True, comment="up")
    word_count = Column(Integer, nullable=True, comment="Wp")

    # „ê”ú
    parsed_text = Column(Text, nullable=True, comment="„êÑØá,")
    metadata = Column(JSON, nullable=True, comment="ùCpnJSON	")

    # ∂
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADING, nullable=False, comment="∂")
    error_message = Column(Text, nullable=True, comment="Ô·o")

    # @	
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="@	 ID")

    # ˆÙ3
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="˙ˆÙ")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="Ù∞ˆÙ")
    parsed_at = Column(DateTime, nullable=True, comment="„êåˆÙ")

    # s˚
    owner = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    acl = relationship("ACL", back_populates="document", cascade="all, delete-orphan", uselist=False)

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"

    def to_dict(self, include_chunks=False):
        """lb:Wx"""
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
