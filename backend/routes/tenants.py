"""
Tenant Management Routes
租户管理API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timedelta

from api.db import get_db
from api.auth import get_current_user, get_current_active_user
from models.user_models import User
from models.tenant_models import Tenant, TenantFeature, Department, DeployMode, TenantStatus
from models.tenant_permission_models import (
    TenantRole, TenantUser, ResourcePermission, PlatformAdmin,
    Permission, ResourceType, GranteeType, PlatformRole
)
from models.audit_models import AuditAction, AuditLevel
from services.permission_checker import PermissionChecker, PermissionContext, PermissionManager
from services.tenant_context import get_current_tenant, get_current_tenant_id
from services.audit_service import AuditService

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])


# ========== Pydantic Models ==========

class TenantCreate(BaseModel):
    """创建租户请求"""
    name: str = Field(..., min_length=1, max_length=255, description="租户名称")
    slug: str = Field(..., min_length=1, max_length=100, description="租户标识(URL友好)")
    description: Optional[str] = None
    deploy_mode: DeployMode = DeployMode.CLOUD
    storage_quota_bytes: int = Field(default=10737418240, description="存储配额(bytes,默认10GB)")
    user_quota: int = Field(default=10, description="用户数上限")
    document_quota: int = Field(default=1000, description="文档数上限")
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None


class TenantUpdate(BaseModel):
    """更新租户请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TenantStatus] = None
    storage_quota_bytes: Optional[int] = None
    user_quota: Optional[int] = None
    document_quota: Optional[int] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None


class TenantResponse(BaseModel):
    """租户响应"""
    id: str
    name: str
    slug: str
    description: Optional[str]
    deploy_mode: str
    status: str
    storage_quota_bytes: int
    storage_used_bytes: int
    storage_usage_percent: float
    user_quota: int
    user_count: int
    document_quota: int
    document_count: int
    created_at: str
    expires_at: Optional[str]


class InviteUserRequest(BaseModel):
    """邀请用户请求"""
    user_id: int
    role_name: str = "member"
    department_id: Optional[str] = None


class RoleCreate(BaseModel):
    """创建角色请求"""
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: int = Permission.READER


class GrantPermissionRequest(BaseModel):
    """授权请求"""
    resource_type: ResourceType
    resource_id: str
    grantee_type: GranteeType
    grantee_id: str
    permission: int
    expires_at: Optional[str] = None


# ========== Helper Functions ==========

def require_platform_admin(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """要求平台管理员权限"""
    admin = db.query(PlatformAdmin).filter(PlatformAdmin.user_id == current_user.id).first()
    if not admin or admin.role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required"
        )
    return current_user


def require_tenant_admin(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """要求租户管理员权限"""
    tenant = get_current_tenant(request)

    # 查找租户用户
    tenant_user = db.query(TenantUser).filter(
        TenantUser.tenant_id == tenant.id,
        TenantUser.user_id == current_user.id,
        TenantUser.status == "active"
    ).first()

    if not tenant_user or not tenant_user.role or tenant_user.role.name != "tenant_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access required"
        )

    return current_user


# ========== Platform Admin Routes ==========

@router.post("/", response_model=TenantResponse, dependencies=[Depends(require_platform_admin)])
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建租户 (平台管理员)

    创建新租户并初始化默认角色
    """
    # 检查slug是否已存在
    existing = db.query(Tenant).filter(Tenant.slug == tenant_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant slug '{tenant_data.slug}' already exists"
        )

    # 创建租户
    tenant_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        **tenant_data.dict()
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # 创建默认角色
    default_roles = [
        {
            "name": "tenant_admin",
            "display_name": "租户管理员",
            "description": "拥有租户内所有权限",
            "level": 100,
            "permissions": Permission.OWNER,
            "is_system": True,
            "is_default": False
        },
        {
            "name": "member",
            "display_name": "成员",
            "description": "普通成员",
            "level": 10,
            "permissions": Permission.EDITOR,
            "is_system": True,
            "is_default": True
        },
        {
            "name": "guest",
            "display_name": "访客",
            "description": "只读权限",
            "level": 1,
            "permissions": Permission.READER,
            "is_system": True,
            "is_default": False
        }
    ]

    for role_data in default_roles:
        role = TenantRole(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            **role_data
        )
        db.add(role)

    db.commit()

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.TENANT_CREATE,
        user=current_user,
        resource_type="tenant",
        resource_id=str(tenant_id),
        resource_name=tenant.name,
        level=AuditLevel.CRITICAL,
        success=True
    )

    return TenantResponse(**tenant.to_dict())


@router.get("/", response_model=List[TenantResponse], dependencies=[Depends(require_platform_admin)])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TenantStatus] = None,
    db: Session = Depends(get_db)
):
    """
    列出所有租户 (平台管理员)
    """
    query = db.query(Tenant)

    if status:
        query = query.filter(Tenant.status == status)

    tenants = query.offset(skip).limit(limit).all()
    return [TenantResponse(**t.to_dict()) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantResponse, dependencies=[Depends(require_platform_admin)])
async def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """
    获取租户详情 (平台管理员)
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TenantResponse(**tenant.to_dict())


@router.patch("/{tenant_id}", response_model=TenantResponse, dependencies=[Depends(require_platform_admin)])
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新租户 (平台管理员)
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # 保存变更前的状态
    old_data = tenant.to_dict()

    # 更新字段
    for key, value in tenant_data.dict(exclude_unset=True).items():
        setattr(tenant, key, value)

    db.commit()
    db.refresh(tenant)

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.TENANT_UPDATE,
        user=current_user,
        resource_type="tenant",
        resource_id=str(tenant_id),
        resource_name=tenant.name,
        level=AuditLevel.CRITICAL,
        changes={"before": old_data, "after": tenant.to_dict()},
        success=True
    )

    return TenantResponse(**tenant.to_dict())


# ========== Tenant Admin Routes ==========

@router.get("/current/info", response_model=TenantResponse)
async def get_current_tenant_info(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前租户信息
    """
    tenant = get_current_tenant(request)
    return TenantResponse(**tenant.to_dict())


@router.post("/current/users/invite")
async def invite_user_to_tenant(
    request: Request,
    invite_data: InviteUserRequest,
    current_user: User = Depends(require_tenant_admin),
    db: Session = Depends(get_db)
):
    """
    邀请用户加入租户 (租户管理员)
    """
    tenant = get_current_tenant(request)

    # 检查配额
    if tenant.is_quota_exceeded("user"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User quota exceeded"
        )

    # 检查用户是否存在
    user = db.query(User).filter(User.id == invite_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 检查是否已经是成员
    existing = db.query(TenantUser).filter(
        TenantUser.tenant_id == tenant.id,
        TenantUser.user_id == invite_data.user_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already in tenant"
        )

    # 查找角色
    role = db.query(TenantRole).filter(
        TenantRole.tenant_id == tenant.id,
        TenantRole.name == invite_data.role_name
    ).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # 创建租户用户关联
    tenant_user = TenantUser(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=invite_data.user_id,
        role_id=role.id,
        department_id=invite_data.department_id,
        status="active",
        invited_by=current_user.id,
        invited_at=datetime.utcnow()
    )

    db.add(tenant_user)
    db.commit()

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.ROLE_ASSIGN,
        user=current_user,
        resource_type="tenant_user",
        resource_id=str(tenant_user.id),
        resource_name=user.username,
        details={"role": invite_data.role_name},
        level=AuditLevel.INFO,
        success=True
    )

    return {"message": "User invited successfully", "tenant_user_id": str(tenant_user.id)}


@router.get("/current/users")
async def list_tenant_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    列出租户的所有用户
    """
    tenant = get_current_tenant(request)

    tenant_users = db.query(TenantUser).filter(
        TenantUser.tenant_id == tenant.id,
        TenantUser.status == "active"
    ).offset(skip).limit(limit).all()

    return {"users": [tu.to_dict() for tu in tenant_users]}


@router.post("/current/roles", dependencies=[Depends(require_tenant_admin)])
async def create_role(
    request: Request,
    role_data: RoleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建自定义角色 (租户管理员)
    """
    tenant = get_current_tenant(request)

    # 检查角色名是否已存在
    existing = db.query(TenantRole).filter(
        TenantRole.tenant_id == tenant.id,
        TenantRole.name == role_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )

    # 创建角色
    role = TenantRole(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        **role_data.dict(),
        is_system=False,
        is_default=False
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.ROLE_CREATE,
        user=current_user,
        resource_type="role",
        resource_id=str(role.id),
        resource_name=role.name,
        level=AuditLevel.INFO,
        success=True
    )

    return role.to_dict()


@router.get("/current/roles")
async def list_roles(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    列出租户的所有角色
    """
    tenant = get_current_tenant(request)

    roles = db.query(TenantRole).filter(
        TenantRole.tenant_id == tenant.id
    ).order_by(TenantRole.level.desc()).all()

    return {"roles": [r.to_dict() for r in roles]}


# ========== Permission Management Routes ==========

@router.post("/current/permissions/grant", dependencies=[Depends(require_tenant_admin)])
async def grant_permission(
    request: Request,
    perm_data: GrantPermissionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    授予权限 (租户管理员)
    """
    tenant = get_current_tenant(request)

    perm_manager = PermissionManager(db)

    permission = perm_manager.grant_permission(
        tenant_id=str(tenant.id),
        resource_type=perm_data.resource_type,
        resource_id=perm_data.resource_id,
        grantee_type=perm_data.grantee_type,
        grantee_id=perm_data.grantee_id,
        permission=perm_data.permission,
        granted_by=current_user.id,
        expires_at=perm_data.expires_at
    )

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.PERM_GRANT,
        user=current_user,
        resource_type=perm_data.resource_type.value,
        resource_id=perm_data.resource_id,
        details={
            "grantee_type": perm_data.grantee_type.value,
            "grantee_id": perm_data.grantee_id,
            "permission": Permission.to_string(perm_data.permission)
        },
        level=AuditLevel.INFO,
        success=True
    )

    return permission.to_dict()


@router.get("/current/permissions/{resource_type}/{resource_id}")
async def list_resource_permissions(
    request: Request,
    resource_type: ResourceType,
    resource_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    列出资源的所有权限
    """
    tenant = get_current_tenant(request)

    perm_manager = PermissionManager(db)
    permissions = perm_manager.list_resource_permissions(
        tenant_id=str(tenant.id),
        resource_type=resource_type,
        resource_id=resource_id
    )

    return {"permissions": [p.to_dict() for p in permissions]}
