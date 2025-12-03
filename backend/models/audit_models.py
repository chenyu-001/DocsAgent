"""
Audit Models - 审计日志系统
记录所有敏感操作,支持合规要求
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from api.db import Base
import enum


class AuditAction(str, enum.Enum):
    """审计操作类型"""
    # ========== 用户操作 ==========
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_PASSWORD_CHANGE = "user.password_change"
    USER_PASSWORD_RESET = "user.password_reset"

    # ========== 租户操作 ==========
    TENANT_CREATE = "tenant.create"
    TENANT_UPDATE = "tenant.update"
    TENANT_DELETE = "tenant.delete"
    TENANT_SUSPEND = "tenant.suspend"
    TENANT_ACTIVATE = "tenant.activate"

    # ========== 文档操作 ==========
    DOC_UPLOAD = "doc.upload"
    DOC_VIEW = "doc.view"
    DOC_DOWNLOAD = "doc.download"
    DOC_UPDATE = "doc.update"
    DOC_DELETE = "doc.delete"
    DOC_SHARE = "doc.share"
    DOC_MOVE = "doc.move"

    # ========== 文件夹操作 ==========
    FOLDER_CREATE = "folder.create"
    FOLDER_UPDATE = "folder.update"
    FOLDER_DELETE = "folder.delete"
    FOLDER_MOVE = "folder.move"

    # ========== 权限操作 ==========
    PERM_GRANT = "perm.grant"
    PERM_REVOKE = "perm.revoke"
    PERM_UPDATE = "perm.update"

    # ========== 角色操作 ==========
    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"
    ROLE_ASSIGN = "role.assign"
    ROLE_UNASSIGN = "role.unassign"

    # ========== 部门操作 ==========
    DEPT_CREATE = "dept.create"
    DEPT_UPDATE = "dept.update"
    DEPT_DELETE = "dept.delete"

    # ========== 管理操作 ==========
    ADMIN_LOGIN = "admin.login"
    CONFIG_CHANGE = "config.change"
    FEATURE_TOGGLE = "feature.toggle"
    QUOTA_CHANGE = "quota.change"

    # ========== 数据操作 ==========
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    DATA_BACKUP = "data.backup"
    DATA_RESTORE = "data.restore"

    # ========== 查询操作 ==========
    SEARCH_QUERY = "search.query"
    QA_QUERY = "qa.query"


class AuditLevel(str, enum.Enum):
    """审计级别"""
    INFO = "info"        # 普通信息
    WARNING = "warning"  # 警告(异常行为)
    CRITICAL = "critical"  # 关键操作
    SECURITY = "security"  # 安全事件


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, comment="日志ID")
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True, comment="租户ID(平台操作为NULL)")

    # 操作信息
    action = Column(Enum(AuditAction), nullable=False, index=True, comment="操作类型")
    level = Column(Enum(AuditLevel), default=AuditLevel.INFO, nullable=False, comment="审计级别")

    # 操作者信息
    user_id = Column(Integer, nullable=True, index=True, comment="操作用户ID")
    username = Column(String(50), nullable=True, comment="用户名(冗余,防删除后查不到)")
    user_role = Column(String(50), nullable=True, comment="用户角色")

    # 资源信息
    resource_type = Column(String(50), nullable=True, comment="资源类型")
    resource_id = Column(String(100), nullable=True, index=True, comment="资源ID")
    resource_name = Column(String(255), nullable=True, comment="资源名称")

    # 详细信息
    details = Column(JSON, nullable=True, comment="操作详情JSON")
    changes = Column(JSON, nullable=True, comment="变更内容JSON(before/after)")

    # 请求信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="User Agent")
    request_id = Column(String(100), nullable=True, index=True, comment="请求ID")

    # 结果
    success = Column(Boolean, default=True, nullable=False, comment="是否成功")
    error_message = Column(Text, nullable=True, comment="错误消息")
    error_code = Column(String(50), nullable=True, comment="错误码")

    # 性能指标
    duration_ms = Column(Integer, nullable=True, comment="操作耗时(毫秒)")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="创建时间")

    # 索引优化
    __table_args__ = (
        Index("idx_audit_tenant_action", "tenant_id", "action"),
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_time", "created_at"),
        Index("idx_audit_level", "level", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.username}, success={self.success})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "action": self.action.value,
            "level": self.level.value,
            "user_id": self.user_id,
            "username": self.username,
            "user_role": self.user_role,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "details": self.details,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "success": self.success,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LoginHistory(Base):
    """登录历史表 - 专门记录登录事件"""
    __tablename__ = "login_history"

    id = Column(UUID(as_uuid=True), primary_key=True, comment="记录ID")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True, comment="租户ID")

    # 登录信息
    username = Column(String(50), nullable=False, comment="用户名")
    login_type = Column(String(20), default="password", nullable=False, comment="登录方式(password/sso/oauth)")

    # 结果
    success = Column(Boolean, default=True, nullable=False, comment="是否成功")
    failure_reason = Column(String(255), nullable=True, comment="失败原因")

    # 请求信息
    ip_address = Column(String(45), nullable=True, index=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="User Agent")
    location = Column(String(255), nullable=True, comment="地理位置")

    # 设备信息
    device_type = Column(String(50), nullable=True, comment="设备类型")
    browser = Column(String(100), nullable=True, comment="浏览器")
    os = Column(String(100), nullable=True, comment="操作系统")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="登录时间")
    logout_at = Column(DateTime, nullable=True, comment="登出时间")
    session_duration = Column(Integer, nullable=True, comment="会话时长(秒)")

    # 索引
    __table_args__ = (
        Index("idx_login_user_time", "user_id", "created_at"),
        Index("idx_login_tenant_time", "tenant_id", "created_at"),
        Index("idx_login_ip", "ip_address", "created_at"),
    )

    def __repr__(self):
        return f"<LoginHistory(user={self.username}, success={self.success}, ip={self.ip_address})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "username": self.username,
            "login_type": self.login_type,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "ip_address": self.ip_address,
            "device_type": self.device_type,
            "browser": self.browser,
            "os": self.os,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "logout_at": self.logout_at.isoformat() if self.logout_at else None,
            "session_duration": self.session_duration,
        }
