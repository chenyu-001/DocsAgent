"""
Database Models Module
"""
# 原有模型
from models.user_models import User, UserRole
from models.document_models import Document, DocumentStatus, DocumentType
from models.folder_models import Folder
from models.chunk_models import Chunk
from models.acl_models import ACL, ACLRule, PermissionLevel
from models.log_models import QueryLog, OperationLog

# 多租户模型
from models.tenant_models import Tenant, TenantFeature, Department, DeployMode, TenantStatus
from models.tenant_permission_models import (
    TenantRole, TenantUser, ResourcePermission, PlatformAdmin,
    Permission, ResourceType, GranteeType, PlatformRole
)
from models.audit_models import AuditLog, LoginHistory, AuditAction, AuditLevel

__all__ = [
    # 原有模型
    "User",
    "UserRole",
    "Document",
    "DocumentStatus",
    "DocumentType",
    "Folder",
    "Chunk",
    "ACL",
    "ACLRule",
    "PermissionLevel",
    "QueryLog",
    "OperationLog",

    # 多租户模型
    "Tenant",
    "TenantFeature",
    "Department",
    "DeployMode",
    "TenantStatus",
    "TenantRole",
    "TenantUser",
    "ResourcePermission",
    "PlatformAdmin",
    "Permission",
    "ResourceType",
    "GranteeType",
    "PlatformRole",

    # 审计模型
    "AuditLog",
    "LoginHistory",
    "AuditAction",
    "AuditLevel",
]
