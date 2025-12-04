"""
User Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from api.db import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"  # Administrator
    USER = "user"    # Regular user
    GUEST = "guest"  # Guest user


class User(Base):
    """User table"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="Username")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="Email")
    hashed_password = Column(String(255), nullable=False, comment="Hashed password")

    # User information
    full_name = Column(String(100), nullable=True, comment="Full name")
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False, comment="User role")
    is_active = Column(Boolean, default=True, nullable=False, comment="Is active")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Creation time")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="Update time")
    last_login = Column(DateTime, nullable=True, comment="Last login time")

    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="owner", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="user", cascade="all, delete-orphan")
    operation_logs = relationship("OperationLog", back_populates="user", cascade="all, delete-orphan")
    acl_rules = relationship("ACLRule", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_dict(self, db=None):
        """Convert to dictionary"""
        result = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

        # Add platform admin role if available
        if db:
            from models.tenant_permission_models import PlatformAdmin
            platform_admin = db.query(PlatformAdmin).filter(
                PlatformAdmin.user_id == self.id
            ).first()
            if platform_admin:
                result["platform_role"] = platform_admin.role.value
                result["is_platform_admin"] = True
            else:
                result["platform_role"] = None
                result["is_platform_admin"] = False

        return result
