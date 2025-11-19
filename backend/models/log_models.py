"""
Â◊!ã
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Index, JSON
from sqlalchemy.orm import relationship
from api.db import Base


class QueryLog(Base):
    """Â‚Â◊h"""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # (7·o
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="(7 ID")

    # Â‚·o
    query_text = Column(Text, nullable=False, comment="Â‚á,")
    query_hash = Column(String(64), index=True, nullable=False, comment="Â‚á, SHA256 »")

    # ¿"”ú
    num_results = Column(Integer, nullable=True, comment="‘ﬁ”úp")
    top_document_ids = Column(JSON, nullable=True, comment="‘ﬁÑác ID h")

    # '˝
    retrieval_time = Column(Float, nullable=True, comment="¿"ˆÎ“	")
    llm_time = Column(Float, nullable=True, comment="LLM ˆÎ“	")
    total_time = Column(Float, nullable=True, comment=";ˆÎ“	")

    # Õà
    user_feedback = Column(Integer, nullable=True, comment="(7Õàƒ1-5	")
    feedback_comment = Column(Text, nullable=True, comment="(7Õàƒ∫")

    # IP åæ·o
    ip_address = Column(String(50), nullable=True, comment="IP 0@")
    user_agent = Column(String(500), nullable=True, comment="User Agent")

    # ˆÙ3
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="˙ˆÙ")

    # s˚
    user = relationship("User", back_populates="query_logs")

    # "†Â‚
    __table_args__ = (
        Index("idx_query_created", "created_at"),
        Index("idx_query_user_created", "user_id", "created_at"),
    )

    def __repr__(self):
        preview = self.query_text[:50] + "..." if len(self.query_text) > 50 else self.query_text
        return f"<QueryLog(id={self.id}, user_id={self.user_id}, query='{preview}')>"

    def to_dict(self):
        """lb:Wx"""
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
    """Õ\Â◊h"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # (7·o
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="(7 ID")

    # Õ\·o
    operation_type = Column(String(50), nullable=False, index=True, comment="Õ\{ãupload/delete/updateI	")
    resource_type = Column(String(50), nullable=False, comment="Dê{ãdocument/user/aclI	")
    resource_id = Column(Integer, nullable=True, comment="Dê ID")

    # Õ\Ê≈
    description = Column(Text, nullable=True, comment="Õ\œ")
    details = Column(JSON, nullable=True, comment="Ê∆·oJSON	")

    # Õ\”ú
    success = Column(Boolean, default=True, nullable=False, comment="/&ü")
    error_message = Column(Text, nullable=True, comment="Ô·o")

    # IP åæ·o
    ip_address = Column(String(50), nullable=True, comment="IP 0@")
    user_agent = Column(String(500), nullable=True, comment="User Agent")

    # ˆÙ3
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="˙ˆÙ")

    # s˚
    user = relationship("User", back_populates="operation_logs")

    # "†Â‚
    __table_args__ = (
        Index("idx_operation_type_created", "operation_type", "created_at"),
        Index("idx_operation_user_created", "user_id", "created_at"),
    )

    def __repr__(self):
        return f"<OperationLog(id={self.id}, type='{self.operation_type}', resource='{self.resource_type}:{self.resource_id}')>"

    def to_dict(self):
        """lb:Wx"""
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
