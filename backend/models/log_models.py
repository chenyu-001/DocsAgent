"""
Log Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Index, JSON
from sqlalchemy.orm import relationship
from api.db import Base


class QueryLog(Base):
    """Query log table"""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="User ID")

    # Query information
    query_text = Column(Text, nullable=False, comment="Query text")
    query_hash = Column(String(64), index=True, nullable=False, comment="Query text SHA256 hash")

    # Search results
    num_results = Column(Integer, nullable=True, comment="Number of results returned")
    top_document_ids = Column(JSON, nullable=True, comment="List of top document IDs")

    # Performance metrics
    retrieval_time = Column(Float, nullable=True, comment="Retrieval time in seconds")
    llm_time = Column(Float, nullable=True, comment="LLM response time in seconds")
    total_time = Column(Float, nullable=True, comment="Total time in seconds")

    # User feedback
    user_feedback = Column(Integer, nullable=True, comment="User feedback rating 1-5")
    feedback_comment = Column(Text, nullable=True, comment="User feedback comment")

    # IP and user agent
    ip_address = Column(String(50), nullable=True, comment="IP address")
    user_agent = Column(String(500), nullable=True, comment="User Agent")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="Creation time")

    # Relationships
    user = relationship("User", back_populates="query_logs")

    # Indexes
    __table_args__ = (
        Index("idx_query_created", "created_at"),
        Index("idx_query_user_created", "user_id", "created_at"),
    )

    def __repr__(self):
        preview = self.query_text[:50] + "..." if len(self.query_text) > 50 else self.query_text
        return f"<QueryLog(id={self.id}, user_id={self.user_id}, query='{preview}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "query_text": self.query_text,
            "num_results": self.num_results,
            "retrieval_time": self.retrieval_time,
            "llm_time": self.llm_time,
            "total_time": self.total_time,
            "user_feedback": self.user_feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OperationLog(Base):
    """Operation log table"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="User ID")

    # Operation information
    operation_type = Column(String(50), nullable=False, index=True, comment="Operation type (upload/delete/update etc)")
    resource_type = Column(String(50), nullable=False, comment="Resource type (document/user/acl etc)")
    resource_id = Column(Integer, nullable=True, comment="Resource ID")

    # Operation details
    description = Column(Text, nullable=True, comment="Operation description")
    details = Column(JSON, nullable=True, comment="Detailed information JSON")

    # Operation result
    success = Column(Boolean, default=True, nullable=False, comment="Is successful")
    error_message = Column(Text, nullable=True, comment="Error message")

    # IP and user agent
    ip_address = Column(String(50), nullable=True, comment="IP address")
    user_agent = Column(String(500), nullable=True, comment="User Agent")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="Creation time")

    # Relationships
    user = relationship("User", back_populates="operation_logs")

    # Indexes
    __table_args__ = (
        Index("idx_operation_type_created", "operation_type", "created_at"),
        Index("idx_operation_user_created", "user_id", "created_at"),
    )

    def __repr__(self):
        return f"<OperationLog(id={self.id}, type='{self.operation_type}', resource='{self.resource_type}:{self.resource_id}')>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "operation_type": self.operation_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "description": self.description,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
