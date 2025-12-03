"""
Tenant Permission Models - 租户权限体系
支持基于位运算的灵活权限控制
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from api.db import Base
import enum


# ========== 权限位定义 ==========
class Permission:
    """权限位运算常量"""
    NONE = 0                  # 无权限
    READ = 1 << 0            # 读取 (1)
    WRITE = 1 << 1           # 写入 (2)
    DELETE = 1 << 2          # 删除 (4)
    SHARE = 1 << 3           # 分享 (8)
    ADMIN = 1 << 4           # 管理(含授权他人) (16)
    DOWNLOAD = 1 << 5        # 下载 (32)
    COMMENT = 1 << 6         # 评论 (64)
    EXPORT = 1 << 7          # 导出 (128)

    # 预设权限组合
    READER = READ | DOWNLOAD                                # 读者 (33)
    EDITOR = READ | WRITE | DOWNLOAD | COMMENT              # 编辑者 (67)
    CONTRIBUTOR = READ | WRITE | DELETE | DOWNLOAD | COMMENT # 贡献者 (71)
    OWNER = READ | WRITE | DELETE | SHARE | ADMIN | DOWNLOAD | COMMENT | EXPORT  # 所有者 (255)

    @classmethod
    def has_permission(cls, user_perm: int, required_perm: int) -> bool:
        """检查用户是否拥有所需权限"""
        return (user_perm & required_perm) == required_perm

    @classmethod
    def to_string(cls, perm: int) -> str:
        """将权限位转换为可读字符串"""
        perms = []
        if perm & cls.READ:
            perms.append("READ")
        if perm & cls.WRITE:
            perms.append("WRITE")
        if perm & cls.DELETE:
            perms.append("DELETE")
        if perm & cls.SHARE:
            perms.append("SHARE")
        if perm & cls.ADMIN:
            perms.append("ADMIN")
        if perm & cls.DOWNLOAD:
            perms.append("DOWNLOAD")
        if perm & cls.COMMENT:
            perms.append("COMMENT")
        if perm & cls.EXPORT:
            perms.append("EXPORT")
        return "|".join(perms) if perms else "NONE"


class TenantRole(Base):
    """租户角色表 - 定义租户内的角色"""
    __tablename__ = "tenant_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, comment="角色ID")
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True, comment="租户ID")

    # 角色信息
    name = Column(String(50), nullable=False, comment="角色名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, nullable=True, comment="角色描述")

    # 权限级别
    level = Column(Integer, default=0, nullable=False, comment="权限等级(数字越大权限越高)")
    permissions = Column(Integer, default=Permission.READER, nullable=False, comment="默认权限位")

    # 系统角色标识
    is_system = Column(Boolean, default=False, nullable=False, comment="是否为系统预设角色(不可删除)")
    is_default = Column(Boolean, default=False, nullable=False, comment="是否为默认角色(新用户自动分配)")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 关系
    tenant = relationship("Tenant", back_populates="roles")

    # 唯一约束
    __table_args__ = (
        Index("idx_tenant_role_name", "tenant_id", "name", unique=True),
    )

    def __repr__(self):
        return f"<TenantRole(id={self.id}, name='{self.name}', level={self.level})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "level": self.level,
            "permissions": self.permissions,
            "permissions_string": Permission.to_string(self.permissions),
            "is_system": self.is_system,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TenantUser(Base):
    """租户用户关联表 - 用户在租户中的身份"""
    __tablename__ = "tenant_users"

    id = Column(UUID(as_uuid=True), primary_key=True, comment="关联ID")
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True, comment="租户ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")

    # 角色与部门
    role_id = Column(UUID(as_uuid=True), ForeignKey("tenant_roles.id", ondelete="SET NULL"), nullable=True, comment="角色ID")
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, comment="部门ID")

    # 状态
    status = Column(Enum("active", "disabled", "invited", name="tenant_user_status"), default="active", nullable=False, comment="状态")

    # 邀请信息
    invited_by = Column(Integer, nullable=True, comment="邀请人用户ID")
    invited_at = Column(DateTime, nullable=True, comment="邀请时间")
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="加入时间")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    last_active_at = Column(DateTime, nullable=True, comment="最后活跃时间")

    # 关系
    tenant = relationship("Tenant", back_populates="users")
    user = relationship("User", backref="tenant_memberships")
    role = relationship("TenantRole")
    department = relationship("Department")

    # 唯一约束
    __table_args__ = (
        Index("idx_tenant_user", "tenant_id", "user_id", unique=True),
    )

    def __repr__(self):
        return f"<TenantUser(tenant_id={self.tenant_id}, user_id={self.user_id}, status={self.status})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "user_id": self.user_id,
            "role_id": str(self.role_id) if self.role_id else None,
            "role_name": self.role.name if self.role else None,
            "department_id": str(self.department_id) if self.department_id else None,
            "department_name": self.department.name if self.department else None,
            "status": self.status,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }


class ResourceType(str, enum.Enum):
    """资源类型"""
    WORKSPACE = "workspace"      # 工作空间(最高层)
    FOLDER = "folder"           # 文件夹
    DOCUMENT = "document"       # 文档


class GranteeType(str, enum.Enum):
    """授权对象类型"""
    USER = "user"               # 用户
    ROLE = "role"              # 角色
    DEPARTMENT = "department"  # 部门


class ResourcePermission(Base):
    """资源权限表 - 资源级别的细粒度权限控制"""
    __tablename__ = "resource_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, comment="权限ID")
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True, comment="租户ID")

    # 资源标识
    resource_type = Column(Enum(ResourceType), nullable=False, comment="资源类型")
    resource_id = Column(String(100), nullable=False, index=True, comment="资源ID")

    # 授权对象(三选一)
    grantee_type = Column(Enum(GranteeType), nullable=False, comment="被授权者类型")
    grantee_id = Column(String(100), nullable=False, index=True, comment="被授权者ID")

    # 权限位
    permission = Column(Integer, default=Permission.READER, nullable=False, comment="权限位")

    # 继承控制
    inherit = Column(Boolean, default=True, nullable=False, comment="是否继承父级权限")

    # 授权信息
    granted_by = Column(Integer, nullable=True, comment="授权人用户ID")
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="授权时间")

    # 过期时间(用于临时授权)
    expires_at = Column(DateTime, nullable=True, comment="权限过期时间")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    # 唯一约束
    __table_args__ = (
        Index("idx_resource_permission", "tenant_id", "resource_type", "resource_id", "grantee_type", "grantee_id", unique=True),
        Index("idx_resource_lookup", "tenant_id", "resource_type", "resource_id"),
        Index("idx_grantee_lookup", "tenant_id", "grantee_type", "grantee_id"),
    )

    def __repr__(self):
        return f"<ResourcePermission(resource={self.resource_type}:{self.resource_id}, grantee={self.grantee_type}:{self.grantee_id}, perm={self.permission})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "resource_type": self.resource_type.value,
            "resource_id": self.resource_id,
            "grantee_type": self.grantee_type.value,
            "grantee_id": self.grantee_id,
            "permission": self.permission,
            "permission_string": Permission.to_string(self.permission),
            "inherit": self.inherit,
            "granted_by": self.granted_by,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def is_expired(self) -> bool:
        """检查权限是否已过期"""
        if self.expires_at:
            return self.expires_at < datetime.utcnow()
        return False


class PlatformRole(str, enum.Enum):
    """平台角色 - 超级管理员"""
    SUPER_ADMIN = "super_admin"      # 超级管理员(管理所有租户)
    OPS = "ops"                      # 运维人员(系统维护)
    SUPPORT = "support"              # 客服支持(查看权限)
    AUDITOR = "auditor"              # 审计员(只读所有日志)


class PlatformAdmin(Base):
    """平台管理员表 - 系统级管理员"""
    __tablename__ = "platform_admins"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, comment="用户ID")
    role = Column(Enum(PlatformRole), default=PlatformRole.SUPPORT, nullable=False, comment="平台角色")

    # 权限范围限制(JSON数组,例如只能管理特定租户)
    scope = Column(Text, nullable=True, comment="权限范围JSON")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")

    # 关系
    user = relationship("User", backref="platform_admin")

    def __repr__(self):
        return f"<PlatformAdmin(user_id={self.user_id}, role={self.role})>"

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "role": self.role.value,
            "scope": self.scope,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
