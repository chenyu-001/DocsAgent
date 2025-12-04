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


class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    full_name: Optional[str] = None
    email: Optional[str] = None


class UpdateUserStatusRequest(BaseModel):
    """更新用户状态请求"""
    status: str = Field(..., pattern="^(active|disabled)$")


class UpdateUserRoleRequest(BaseModel):
    """更新用户角色请求"""
    role_name: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., min_length=6)


class RoleUpdate(BaseModel):
    """更新角色请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[int] = None


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
    列出租户的所有用户（包含用户详细信息）
    """
    tenant = get_current_tenant(request)

    tenant_users = db.query(TenantUser).filter(
        TenantUser.tenant_id == tenant.id
    ).offset(skip).limit(limit).all()

    # Enrich with user details
    users_with_details = []
    for tu in tenant_users:
        user_dict = tu.to_dict()
        # Get user details
        user = db.query(User).filter(User.id == tu.user_id).first()
        if user:
            user_dict['username'] = user.username
            user_dict['email'] = user.email
            user_dict['full_name'] = user.full_name
            user_dict['is_active'] = user.is_active
        users_with_details.append(user_dict)

    return {"users": users_with_details}


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


# ========== User Management Routes ==========

@router.patch("/current/users/{tenant_user_id}", dependencies=[Depends(require_tenant_admin)])
async def update_user(
    request: Request,
    tenant_user_id: str,
    user_data: UpdateUserRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新租户用户信息 (租户管理员)
    """
    tenant = get_current_tenant(request)

    # 查找租户用户
    tenant_user = db.query(TenantUser).filter(
        TenantUser.id == tenant_user_id,
        TenantUser.tenant_id == tenant.id
    ).first()

    if not tenant_user:
        raise HTTPException(status_code=404, detail="Tenant user not found")

    # 获取实际用户对象
    user = db.query(User).filter(User.id == tenant_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 保存变更前的数据
    old_data = {"full_name": user.full_name, "email": user.email}

    # 更新用户信息
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.email is not None:
        # 检查邮箱是否已被使用
        existing_email = db.query(User).filter(
            User.email == user_data.email,
            User.id != user.id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = user_data.email

    db.commit()

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.USER_UPDATE,
        user=current_user,
        resource_type="user",
        resource_id=str(user.id),
        resource_name=user.username,
        changes={"before": old_data, "after": {"full_name": user.full_name, "email": user.email}},
        level=AuditLevel.INFO,
        success=True
    )

    return {"message": "User updated successfully", "user": user.to_dict()}


@router.delete("/current/users/{tenant_user_id}", dependencies=[Depends(require_tenant_admin)])
async def remove_user(
    request: Request,
    tenant_user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    从租户移除用户 (租户管理员)
    """
    tenant = get_current_tenant(request)

    # 查找租户用户
    tenant_user = db.query(TenantUser).filter(
        TenantUser.id == tenant_user_id,
        TenantUser.tenant_id == tenant.id
    ).first()

    if not tenant_user:
        raise HTTPException(status_code=404, detail="Tenant user not found")

    # 防止删除自己
    if tenant_user.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself"
        )

    # 获取用户信息用于日志
    user = db.query(User).filter(User.id == tenant_user.user_id).first()
    username = user.username if user else "unknown"

    # 删除租户用户关联
    db.delete(tenant_user)
    db.commit()

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.USER_REMOVE,
        user=current_user,
        resource_type="tenant_user",
        resource_id=str(tenant_user_id),
        resource_name=username,
        level=AuditLevel.WARN,
        success=True
    )

    return {"message": "User removed from tenant successfully"}


@router.patch("/current/users/{tenant_user_id}/status", dependencies=[Depends(require_tenant_admin)])
async def update_user_status(
    request: Request,
    tenant_user_id: str,
    status_data: UpdateUserStatusRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新用户状态 (租户管理员)
    """
    tenant = get_current_tenant(request)

    # 查找租户用户
    tenant_user = db.query(TenantUser).filter(
        TenantUser.id == tenant_user_id,
        TenantUser.tenant_id == tenant.id
    ).first()

    if not tenant_user:
        raise HTTPException(status_code=404, detail="Tenant user not found")

    # 防止禁用自己
    if tenant_user.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status"
        )

    old_status = tenant_user.status
    tenant_user.status = status_data.status

    db.commit()

    # 获取用户信息用于日志
    user = db.query(User).filter(User.id == tenant_user.user_id).first()
    username = user.username if user else "unknown"

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.USER_UPDATE if status_data.status == "active" else AuditAction.USER_DISABLE,
        user=current_user,
        resource_type="tenant_user",
        resource_id=str(tenant_user_id),
        resource_name=username,
        changes={"before": old_status, "after": status_data.status},
        level=AuditLevel.WARN if status_data.status == "disabled" else AuditLevel.INFO,
        success=True
    )

    return {"message": f"User status updated to {status_data.status}"}


@router.patch("/current/users/{tenant_user_id}/role", dependencies=[Depends(require_tenant_admin)])
async def update_user_role(
    request: Request,
    tenant_user_id: str,
    role_data: UpdateUserRoleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新用户角色 (租户管理员)
    """
    tenant = get_current_tenant(request)

    # 查找租户用户
    tenant_user = db.query(TenantUser).filter(
        TenantUser.id == tenant_user_id,
        TenantUser.tenant_id == tenant.id
    ).first()

    if not tenant_user:
        raise HTTPException(status_code=404, detail="Tenant user not found")

    # 查找新角色
    new_role = db.query(TenantRole).filter(
        TenantRole.tenant_id == tenant.id,
        TenantRole.name == role_data.role_name
    ).first()

    if not new_role:
        raise HTTPException(status_code=404, detail="Role not found")

    old_role_name = tenant_user.role.name if tenant_user.role else "none"
    tenant_user.role_id = new_role.id

    db.commit()

    # 获取用户信息用于日志
    user = db.query(User).filter(User.id == tenant_user.user_id).first()
    username = user.username if user else "unknown"

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.ROLE_ASSIGN,
        user=current_user,
        resource_type="tenant_user",
        resource_id=str(tenant_user_id),
        resource_name=username,
        changes={"before": old_role_name, "after": role_data.role_name},
        level=AuditLevel.INFO,
        success=True
    )

    return {"message": "User role updated successfully"}


@router.post("/current/users/{tenant_user_id}/reset-password", dependencies=[Depends(require_tenant_admin)])
async def reset_user_password(
    request: Request,
    tenant_user_id: str,
    password_data: ResetPasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    重置用户密码 (租户管理员)
    """
    from api.auth import get_password_hash

    tenant = get_current_tenant(request)

    # 查找租户用户
    tenant_user = db.query(TenantUser).filter(
        TenantUser.id == tenant_user_id,
        TenantUser.tenant_id == tenant.id
    ).first()

    if not tenant_user:
        raise HTTPException(status_code=404, detail="Tenant user not found")

    # 获取实际用户对象
    user = db.query(User).filter(User.id == tenant_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 更新密码
    user.hashed_password = get_password_hash(password_data.new_password)

    db.commit()

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.PASSWORD_RESET,
        user=current_user,
        resource_type="user",
        resource_id=str(user.id),
        resource_name=user.username,
        level=AuditLevel.WARN,
        success=True
    )

    return {"message": "Password reset successfully"}


# ========== Role Management Routes ==========

@router.get("/current/roles/{role_id}")
async def get_role(
    request: Request,
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取角色详情
    """
    tenant = get_current_tenant(request)

    role = db.query(TenantRole).filter(
        TenantRole.id == role_id,
        TenantRole.tenant_id == tenant.id
    ).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return role.to_dict()


@router.patch("/current/roles/{role_id}", dependencies=[Depends(require_tenant_admin)])
async def update_role(
    request: Request,
    role_id: str,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新角色 (租户管理员)
    """
    tenant = get_current_tenant(request)

    # 查找角色
    role = db.query(TenantRole).filter(
        TenantRole.id == role_id,
        TenantRole.tenant_id == tenant.id
    ).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # 系统角色不可修改
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles"
        )

    # 保存变更前的数据
    old_data = role.to_dict()

    # 更新字段
    for key, value in role_data.dict(exclude_unset=True).items():
        setattr(role, key, value)

    db.commit()

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.ROLE_UPDATE,
        user=current_user,
        resource_type="role",
        resource_id=str(role_id),
        resource_name=role.name,
        changes={"before": old_data, "after": role.to_dict()},
        level=AuditLevel.INFO,
        success=True
    )

    return role.to_dict()


@router.delete("/current/roles/{role_id}", dependencies=[Depends(require_tenant_admin)])
async def delete_role(
    request: Request,
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    删除角色 (租户管理员)
    """
    tenant = get_current_tenant(request)

    # 查找角色
    role = db.query(TenantRole).filter(
        TenantRole.id == role_id,
        TenantRole.tenant_id == tenant.id
    ).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # 系统角色不可删除
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles"
        )

    # 检查是否有用户使用此角色
    users_with_role = db.query(TenantUser).filter(
        TenantUser.role_id == role_id
    ).count()

    if users_with_role > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role: {users_with_role} user(s) still assigned to this role"
        )

    role_name = role.name

    # 删除角色
    db.delete(role)
    db.commit()

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.ROLE_DELETE,
        user=current_user,
        resource_type="role",
        resource_id=str(role_id),
        resource_name=role_name,
        level=AuditLevel.WARN,
        success=True
    )

    return {"message": "Role deleted successfully"}


# ========== Department Management Routes ==========

class DepartmentCreate(BaseModel):
    """创建部门请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[str] = None
    manager_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    """更新部门请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    manager_id: Optional[int] = None


@router.post("/current/departments", dependencies=[Depends(require_tenant_admin)])
async def create_department(
    request: Request,
    dept_data: DepartmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建部门 (租户管理员)
    """
    tenant = get_current_tenant(request)

    # 检查父部门是否存在
    parent_dept = None
    if dept_data.parent_id:
        parent_dept = db.query(Department).filter(
            Department.id == dept_data.parent_id,
            Department.tenant_id == tenant.id
        ).first()
        if not parent_dept:
            raise HTTPException(status_code=404, detail="Parent department not found")

    # 计算部门路径和层级
    if parent_dept:
        path = f"{parent_dept.path}/{dept_data.name}"
        level = parent_dept.level + 1
    else:
        path = f"/{dept_data.name}"
        level = 0

    # 创建部门
    department = Department(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name=dept_data.name,
        description=dept_data.description,
        parent_id=dept_data.parent_id,
        path=path,
        level=level,
        manager_id=dept_data.manager_id
    )

    db.add(department)
    db.commit()
    db.refresh(department)

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.DEPT_CREATE,
        user=current_user,
        resource_type="department",
        resource_id=str(department.id),
        resource_name=department.name,
        level=AuditLevel.INFO,
        success=True
    )

    return department.to_dict()


@router.get("/current/departments")
async def list_departments(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取部门列表（树形结构）
    """
    tenant = get_current_tenant(request)

    departments = db.query(Department).filter(
        Department.tenant_id == tenant.id
    ).order_by(Department.path).all()

    # Build tree structure
    dept_dict = {str(d.id): d.to_dict() for d in departments}

    # Add children array to each department
    for dept_id, dept in dept_dict.items():
        dept['children'] = []
        dept['member_count'] = db.query(TenantUser).filter(
            TenantUser.department_id == dept_id
        ).count()

    # Build parent-child relationships
    root_depts = []
    for dept_id, dept in dept_dict.items():
        if dept['parent_id']:
            parent = dept_dict.get(dept['parent_id'])
            if parent:
                parent['children'].append(dept)
        else:
            root_depts.append(dept)

    return {"departments": root_depts, "total": len(departments)}


@router.get("/current/departments/{dept_id}")
async def get_department(
    request: Request,
    dept_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取部门详情
    """
    tenant = get_current_tenant(request)

    department = db.query(Department).filter(
        Department.id == dept_id,
        Department.tenant_id == tenant.id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    dept_dict = department.to_dict()

    # Add member count
    dept_dict['member_count'] = db.query(TenantUser).filter(
        TenantUser.department_id == dept_id
    ).count()

    return dept_dict


@router.patch("/current/departments/{dept_id}", dependencies=[Depends(require_tenant_admin)])
async def update_department(
    request: Request,
    dept_id: str,
    dept_data: DepartmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新部门 (租户管理员)
    """
    tenant = get_current_tenant(request)

    department = db.query(Department).filter(
        Department.id == dept_id,
        Department.tenant_id == tenant.id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    old_data = department.to_dict()

    # Update fields
    if dept_data.name is not None:
        # Update path for this department and all children
        old_path = department.path
        new_path = old_path.rsplit('/', 1)[0] + '/' + dept_data.name if '/' in old_path else '/' + dept_data.name

        department.name = dept_data.name
        department.path = new_path

        # Update children paths
        children = db.query(Department).filter(
            Department.tenant_id == tenant.id,
            Department.path.like(f"{old_path}/%")
        ).all()

        for child in children:
            child.path = child.path.replace(old_path, new_path, 1)

    if dept_data.description is not None:
        department.description = dept_data.description

    if dept_data.manager_id is not None:
        department.manager_id = dept_data.manager_id

    db.commit()

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.DEPT_UPDATE,
        user=current_user,
        resource_type="department",
        resource_id=str(dept_id),
        resource_name=department.name,
        changes={"before": old_data, "after": department.to_dict()},
        level=AuditLevel.INFO,
        success=True
    )

    return department.to_dict()


@router.delete("/current/departments/{dept_id}", dependencies=[Depends(require_tenant_admin)])
async def delete_department(
    request: Request,
    dept_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    删除部门 (租户管理员)
    """
    tenant = get_current_tenant(request)

    department = db.query(Department).filter(
        Department.id == dept_id,
        Department.tenant_id == tenant.id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Check if department has children
    children_count = db.query(Department).filter(
        Department.parent_id == dept_id
    ).count()

    if children_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete department: {children_count} sub-department(s) exist"
        )

    # Check if department has members
    member_count = db.query(TenantUser).filter(
        TenantUser.department_id == dept_id
    ).count()

    if member_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete department: {member_count} member(s) assigned"
        )

    dept_name = department.name

    db.delete(department)
    db.commit()

    # 审计日志
    audit = AuditService(db)
    audit.log(
        action=AuditAction.DEPT_DELETE,
        user=current_user,
        resource_type="department",
        resource_id=str(dept_id),
        resource_name=dept_name,
        level=AuditLevel.WARN,
        success=True
    )

    return {"message": "Department deleted successfully"}


@router.get("/current/departments/{dept_id}/members")
async def get_department_members(
    request: Request,
    dept_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取部门成员列表
    """
    tenant = get_current_tenant(request)

    # Check if department exists
    department = db.query(Department).filter(
        Department.id == dept_id,
        Department.tenant_id == tenant.id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Get members
    members = db.query(TenantUser).filter(
        TenantUser.department_id == dept_id
    ).all()

    # Enrich with user details
    members_with_details = []
    for member in members:
        member_dict = member.to_dict()
        user = db.query(User).filter(User.id == member.user_id).first()
        if user:
            member_dict['username'] = user.username
            member_dict['email'] = user.email
            member_dict['full_name'] = user.full_name
        members_with_details.append(member_dict)

    return {"members": members_with_details}


# ========== Audit Log Routes ==========

@router.get("/current/audit-logs")
async def list_audit_logs(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    level: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(require_tenant_admin),
    db: Session = Depends(get_db)
):
    """
    获取审计日志列表 (租户管理员)
    支持筛选和分页
    """
    from models.audit_models import AuditLog, AuditAction, AuditLevel
    from datetime import datetime as dt

    tenant = get_current_tenant(request)

    # Build query
    query = db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant.id
    )

    # Apply filters
    if action:
        try:
            query = query.filter(AuditLog.action == AuditAction(action))
        except ValueError:
            pass  # Invalid action, ignore filter

    if level:
        try:
            query = query.filter(AuditLog.level == AuditLevel(level))
        except ValueError:
            pass  # Invalid level, ignore filter

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if start_date:
        try:
            start_dt = dt.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start_dt)
        except ValueError:
            pass  # Invalid date format, ignore

    if end_date:
        try:
            end_dt = dt.fromisoformat(end_date)
            query = query.filter(AuditLog.timestamp <= end_dt)
        except ValueError:
            pass  # Invalid date format, ignore

    # Get total count
    total = query.count()

    # Apply pagination
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    return {
        "logs": [log.to_dict() for log in logs],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/current/audit-logs/export")
async def export_audit_logs(
    request: Request,
    action: Optional[str] = None,
    level: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    format: str = "json",
    current_user: User = Depends(require_tenant_admin),
    db: Session = Depends(get_db)
):
    """
    导出审计日志 (租户管理员)
    支持 JSON 和 CSV 格式
    """
    from models.audit_models import AuditLog, AuditAction, AuditLevel
    from datetime import datetime as dt
    from fastapi.responses import StreamingResponse
    import json
    import io
    import csv

    tenant = get_current_tenant(request)

    # Build query (same as list)
    query = db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant.id
    )

    if action:
        try:
            query = query.filter(AuditLog.action == AuditAction(action))
        except ValueError:
            pass

    if level:
        try:
            query = query.filter(AuditLog.level == AuditLevel(level))
        except ValueError:
            pass

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if start_date:
        try:
            start_dt = dt.fromisoformat(start_date)
            query = query.filter(AuditLog.timestamp >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = dt.fromisoformat(end_date)
            query = query.filter(AuditLog.timestamp <= end_dt)
        except ValueError:
            pass

    logs = query.order_by(AuditLog.timestamp.desc()).all()

    if format == "csv":
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "时间", "操作", "级别", "用户", "资源类型", "资源名称", "IP地址", "结果"
        ])

        # Data
        for log in logs:
            writer.writerow([
                log.timestamp.isoformat() if log.timestamp else "",
                log.action.value if log.action else "",
                log.level.value if log.level else "",
                log.username or "",
                log.resource_type or "",
                log.resource_name or "",
                log.ip_address or "",
                "成功" if log.success else "失败"
            ])

        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    else:
        # Return JSON
        data = [log.to_dict() for log in logs]
        return StreamingResponse(
            io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{dt.now().strftime('%Y%m%d_%H%M%S')}.json"}
        )


@router.get("/current/audit-logs/stats")
async def get_audit_stats(
    request: Request,
    current_user: User = Depends(require_tenant_admin),
    db: Session = Depends(get_db)
):
    """
    获取审计日志统计 (租户管理员)
    """
    from models.audit_models import AuditLog, AuditAction, AuditLevel
    from sqlalchemy import func
    from datetime import datetime, timedelta

    tenant = get_current_tenant(request)

    # Total logs
    total_logs = db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant.id
    ).count()

    # Logs by level
    logs_by_level = db.query(
        AuditLog.level,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.tenant_id == tenant.id
    ).group_by(AuditLog.level).all()

    # Logs by action (top 10)
    logs_by_action = db.query(
        AuditLog.action,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.tenant_id == tenant.id
    ).group_by(AuditLog.action).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()

    # Recent activity (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_logs = db.query(
        func.date(AuditLog.timestamp).label('date'),
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.tenant_id == tenant.id,
        AuditLog.timestamp >= seven_days_ago
    ).group_by(func.date(AuditLog.timestamp)).all()

    return {
        "total_logs": total_logs,
        "logs_by_level": {str(level): count for level, count in logs_by_level},
        "logs_by_action": {str(action): count for action, count in logs_by_action},
        "recent_activity": [
            {"date": str(date), "count": count}
            for date, count in recent_logs
        ]
    }
