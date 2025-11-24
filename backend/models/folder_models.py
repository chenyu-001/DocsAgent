"""
Folder Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from api.db import Base


class Folder(Base):
    """Folder table for organizing documents"""
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Folder information
    name = Column(String(255), nullable=False, comment="Folder name")
    description = Column(String(500), nullable=True, comment="Folder description")

    # Hierarchical structure
    parent_id = Column(
        Integer,
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        comment="Parent folder ID (NULL for root folders)"
    )

    # Path for efficient querying (e.g., "/parent/child")
    path = Column(String(1000), nullable=False, index=True, comment="Folder path")

    # Owner
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Owner user ID"
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Creation time")
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Update time"
    )

    # Relationships
    owner = relationship("User", back_populates="folders")
    parent = relationship("Folder", remote_side=[id], backref="children")
    documents = relationship("Document", back_populates="folder", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Folder(id={self.id}, name='{self.name}', path='{self.path}')>"

    def to_dict(self, include_children=False, include_documents=False):
        """Convert to dictionary"""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "path": self.path,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_children and hasattr(self, 'children'):
            result["children"] = [child.to_dict() for child in self.children]

        if include_documents:
            result["documents"] = [doc.to_dict() for doc in self.documents]
            result["document_count"] = len(self.documents)

        return result
