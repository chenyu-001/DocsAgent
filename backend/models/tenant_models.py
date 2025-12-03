"""
Tenant Models - Multi-tenant architecture
支持 Cloud / Hybrid / Local 三种部署模式
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, BigInteger, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.db import Base
import enum
import uuid


class DeployMode(str, enum.Enum):
    """部署模式"""
    CLOUD = "cloud"      # 云端部署,共享基础设施
    HYBRID = "hybrid"    # 混合模式,元数据云端+数据本地
    LOCAL = "local"      # 完全本地部署


class TenantStatus(str, enum.Enum):
    """租户状态"""
    ACTIVE = "active"        # 活跃
    SUSPENDED = "suspended"  # 暂停(欠费/违规)
    ARCHIVED = "archived"    # 已归档(数据保留但不可用)
    TRIAL = "trial"         # 试用期


class Tenant(Base):
    """租户表 - 企业/组织的顶层隔离"""
    __tablename__ = "tenants"

    # 主键使用UUID以支持分布式部署
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="租户ID")

    # 基本信息
    name = Column(String(255), nullable=False, comment="租户名称(企业名)")
    slug = Column(String(100), unique=True, nullable=False, index=True, comment="租户标识(用于子域名)")
    description = Column(Text, nullable=True, comment="租户描述")

    # 部署模式
    deploy_mode = Column(Enum(DeployMode), default=DeployMode.CLOUD, nullable=False, comment="部署模式")

    # 数据库连接配置(本地部署时使用,加密存储)
    db_connection = Column(Text, nullable=True, comment="数据库连接字符串(加密)")
    db_schema = Column(String(100), nullable=True, comment="数据库Schema名称")

    # 向量库配置
    vector_db_config = Column(JSON, nullable=True, comment="向量库配置JSON")
    vector_namespace = Column(String(100), nullable=True, comment="向量库命名空间")

    # 存储配置
    storage_config = Column(JSON, nullable=True, comment="存储配置(OSS/本地)")

    # 资源配额
    storage_quota_bytes = Column(BigInteger, default=10737418240, nullable=False, comment="存储配额(bytes,默认10GB)")
    user_quota = Column(Integer, default=10, nullable=False, comment="用户数上限")
    document_quota = Column(Integer, default=1000, nullable=False, comment="文档数上限")

    # 当前使用量
    storage_used_bytes = Column(BigInteger, default=0, nullable=False, comment="已使用存储(bytes)")
    user_count = Column(Integer, default=0, nullable=False, comment="当前用户数")
    document_count = Column(Integer, default=0, nullable=False, comment="当前文档数")

    # 状态与订阅
    status = Column(Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False, comment="租户状态")
    expires_at = Column(DateTime, nullable=True, comment="订阅到期时间")
    trial_ends_at = Column(DateTime, nullable=True, comment="试用期结束时间")

    # License信息(本地部署)
    license_key = Column(String(500), nullable=True, comment="License密钥")
    license_data = Column(JSON, nullable=True, comment="License解析数据")

    # 联系信息
    contact_name = Column(String(100), nullable=True, comment="联系人姓名")
    contact_email = Column(String(100), nullable=True, comment="联系人邮箱")
    contact_phone = Column(String(50), nullable=True, comment="联系电话")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    last_active_at = Column(DateTime, nullable=True, comment="最后活跃时间")

    # 关系
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    roles = relationship("TenantRole", back_populates="tenant", cascade="all, delete-orphan")
    features = relationship("TenantFeature", back_populates="tenant", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', mode={self.deploy_mode})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "deploy_mode": self.deploy_mode.value,
            "status": self.status.value,
            "storage_quota_bytes": self.storage_quota_bytes,
            "storage_used_bytes": self.storage_used_bytes,
            "storage_usage_percent": round(self.storage_used_bytes / self.storage_quota_bytes * 100, 2) if self.storage_quota_bytes > 0 else 0,
            "user_quota": self.user_quota,
            "user_count": self.user_count,
            "document_quota": self.document_quota,
            "document_count": self.document_count,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }

    def is_quota_exceeded(self, quota_type: str) -> bool:
        """检查配额是否超限"""
        if quota_type == "storage":
            return self.storage_used_bytes >= self.storage_quota_bytes
        elif quota_type == "user":
            return self.user_count >= self.user_quota
        elif quota_type == "document":
            return self.document_count >= self.document_quota
        return False

    def is_active(self) -> bool:
        """检查租户是否可用"""
        if self.status != TenantStatus.ACTIVE and self.status != TenantStatus.TRIAL:
            return False

        # 检查订阅是否过期
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False

        # 检查试用期是否结束
        if self.status == TenantStatus.TRIAL and self.trial_ends_at:
            if self.trial_ends_at < datetime.utcnow():
                return False

        return True


class TenantFeature(Base):
    """租户功能开关表 - 控制租户可用的功能"""
    __tablename__ = "tenant_features"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True, comment="租户ID")

    # 功能标识
    feature_key = Column(String(50), nullable=False, comment="功能键(ocr/reranker/api_access)")
    enabled = Column(Boolean, default=False, nullable=False, comment="是否启用")

    # 功能配置
    config = Column(JSON, nullable=True, comment="功能特定配置")

    # 使用限制
    usage_limit = Column(Integer, nullable=True, comment="使用次数限制(NULL=无限)")
    usage_count = Column(Integer, default=0, nullable=False, comment="已使用次数")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 关系
    tenant = relationship("Tenant", back_populates="features")

    def __repr__(self):
        return f"<TenantFeature(tenant_id={self.tenant_id}, key='{self.feature_key}', enabled={self.enabled})>"

    def to_dict(self):
        return {
            "id": self.id,
            "feature_key": self.feature_key,
            "enabled": self.enabled,
            "config": self.config,
            "usage_limit": self.usage_limit,
            "usage_count": self.usage_count,
        }


class Department(Base):
    """部门表 - 租户内的组织结构"""
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="部门ID")
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True, comment="租户ID")

    # 基本信息
    name = Column(String(255), nullable=False, comment="部门名称")
    description = Column(Text, nullable=True, comment="部门描述")

    # 层级结构
    parent_id = Column(UUID(as_uuid=True), nullable=True, comment="父部门ID")
    path = Column(String(1000), nullable=False, index=True, comment="部门路径")
    level = Column(Integer, default=0, nullable=False, comment="层级深度")

    # 部门负责人
    manager_id = Column(Integer, nullable=True, comment="部门负责人用户ID")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 关系
    tenant = relationship("Tenant", back_populates="departments")

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', path='{self.path}')>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "description": self.description,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "path": self.path,
            "level": self.level,
            "manager_id": self.manager_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
