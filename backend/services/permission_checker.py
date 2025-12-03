"""
Permission Checker Service
权限检查服务 - 核心权限验证逻辑
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
import logging

from models.tenant_permission_models import (
    Permission, ResourcePermission, TenantUser, TenantRole,
    ResourceType, GranteeType, PlatformAdmin, PlatformRole
)
from models.tenant_models import Tenant
from models.user_models import User

logger = logging.getLogger(__name__)


class PermissionContext:
    """权限检查上下文"""

    def __init__(
        self,
        user_id: int,
        tenant_id: str,
        resource_type: ResourceType,
        resource_id: str,
        required_permission: int
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.required_permission = required_permission


class PermissionChecker:
    """权限检查器"""

    def __init__(self, db: Session):
        self.db = db

    def check(self, ctx: PermissionContext) -> bool:
        """
        检查用户是否拥有所需权限

        检查顺序:
        1. 平台管理员检查
        2. 租户归属检查
        3. 租户管理员直接放行
        4. 资源权限检查(含继承)

        Args:
            ctx: 权限上下文

        Returns:
            bool: 是否有权限

        Raises:
            HTTPException: 权限不足时抛出403
        """
        try:
            # 1. 平台管理员检查
            if self._is_platform_admin(ctx.user_id):
                logger.info(f"Platform admin access granted: user_id={ctx.user_id}")
                return True

            # 2. 租户归属检查
            if not self._belongs_to_tenant(ctx.user_id, ctx.tenant_id):
                logger.warning(f"User {ctx.user_id} does not belong to tenant {ctx.tenant_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: user not in tenant"
                )

            # 3. 租户管理员检查
            tenant_user = self._get_tenant_user(ctx.user_id, ctx.tenant_id)
            if tenant_user and tenant_user.role:
                if tenant_user.role.name == "tenant_admin":
                    logger.info(f"Tenant admin access granted: user_id={ctx.user_id}, tenant_id={ctx.tenant_id}")
                    return True

            # 4. 资源权限检查
            has_permission = self._check_resource_permission(ctx, tenant_user)

            if not has_permission:
                logger.warning(
                    f"Permission denied: user_id={ctx.user_id}, resource={ctx.resource_type}:{ctx.resource_id}, "
                    f"required={Permission.to_string(ctx.required_permission)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {Permission.to_string(ctx.required_permission)} required"
                )

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Permission check error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission check failed"
            )

    def check_silent(self, ctx: PermissionContext) -> bool:
        """
        静默检查权限(不抛出异常)

        Args:
            ctx: 权限上下文

        Returns:
            bool: 是否有权限
        """
        try:
            return self.check(ctx)
        except HTTPException:
            return False

    def get_user_permission(self, ctx: PermissionContext) -> int:
        """
        获取用户对资源的实际权限位

        Args:
            ctx: 权限上下文

        Returns:
            int: 权限位
        """
        # 平台管理员拥有所有权限
        if self._is_platform_admin(ctx.user_id):
            return Permission.OWNER

        # 租户管理员拥有所有权限
        tenant_user = self._get_tenant_user(ctx.user_id, ctx.tenant_id)
        if tenant_user and tenant_user.role and tenant_user.role.name == "tenant_admin":
            return Permission.OWNER

        # 获取资源权限
        return self._get_resource_permission(ctx, tenant_user)

    def _is_platform_admin(self, user_id: int) -> bool:
        """检查是否为平台管理员"""
        admin = self.db.query(PlatformAdmin).filter(
            PlatformAdmin.user_id == user_id
        ).first()
        return admin is not None

    def _belongs_to_tenant(self, user_id: int, tenant_id: str) -> bool:
        """检查用户是否属于租户"""
        tenant_user = self.db.query(TenantUser).filter(
            TenantUser.user_id == user_id,
            TenantUser.tenant_id == tenant_id,
            TenantUser.status == "active"
        ).first()
        return tenant_user is not None

    def _get_tenant_user(self, user_id: int, tenant_id: str) -> Optional[TenantUser]:
        """获取租户用户关联"""
        return self.db.query(TenantUser).filter(
            TenantUser.user_id == user_id,
            TenantUser.tenant_id == tenant_id,
            TenantUser.status == "active"
        ).first()

    def _check_resource_permission(self, ctx: PermissionContext, tenant_user: Optional[TenantUser]) -> bool:
        """检查资源权限"""
        user_perm = self._get_resource_permission(ctx, tenant_user)
        return Permission.has_permission(user_perm, ctx.required_permission)

    def _get_resource_permission(self, ctx: PermissionContext, tenant_user: Optional[TenantUser]) -> int:
        """
        获取资源权限(支持向上继承)

        查找顺序:
        1. 用户直接授权
        2. 角色授权
        3. 部门授权
        4. 父资源权限(递归)
        5. 角色默认权限
        """
        resource_id = ctx.resource_id
        max_depth = 10  # 防止无限递归

        for depth in range(max_depth):
            if not resource_id:
                break

            # 查询所有相关权限
            permissions = self._query_resource_permissions(
                ctx.tenant_id,
                ctx.resource_type,
                resource_id,
                ctx.user_id,
                tenant_user
            )

            if permissions:
                # 返回最高权限
                return max(permissions)

            # 向上查找父资源
            parent_resource = self._get_parent_resource(ctx.resource_type, resource_id)
            if not parent_resource:
                break

            resource_id = parent_resource["id"]
            ctx.resource_type = parent_resource["type"]

        # 使用角色默认权限
        if tenant_user and tenant_user.role:
            return tenant_user.role.permissions

        # 没有任何权限
        return Permission.NONE

    def _query_resource_permissions(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        resource_id: str,
        user_id: int,
        tenant_user: Optional[TenantUser]
    ) -> List[int]:
        """查询资源的所有相关权限"""
        conditions = [
            ResourcePermission.tenant_id == tenant_id,
            ResourcePermission.resource_type == resource_type,
            ResourcePermission.resource_id == resource_id,
        ]

        # 构建授权对象条件
        grantee_conditions = []

        # 用户直接授权
        grantee_conditions.append(
            (ResourcePermission.grantee_type == GranteeType.USER) &
            (ResourcePermission.grantee_id == str(user_id))
        )

        if tenant_user:
            # 角色授权
            if tenant_user.role_id:
                grantee_conditions.append(
                    (ResourcePermission.grantee_type == GranteeType.ROLE) &
                    (ResourcePermission.grantee_id == str(tenant_user.role_id))
                )

            # 部门授权
            if tenant_user.department_id:
                grantee_conditions.append(
                    (ResourcePermission.grantee_type == GranteeType.DEPARTMENT) &
                    (ResourcePermission.grantee_id == str(tenant_user.department_id))
                )

        conditions.append(or_(*grantee_conditions))

        # 查询权限
        perms = self.db.query(ResourcePermission).filter(*conditions).all()

        # 过滤过期权限,返回权限位列表
        return [
            perm.permission
            for perm in perms
            if not perm.is_expired()
        ]

    def _get_parent_resource(self, resource_type: ResourceType, resource_id: str) -> Optional[dict]:
        """
        获取父资源

        资源层级:
        document -> folder -> workspace -> tenant
        folder -> folder(parent) -> workspace -> tenant
        """
        if resource_type == ResourceType.DOCUMENT:
            # 文档的父资源是文件夹
            from models.document_models import Document
            doc = self.db.query(Document).filter(Document.id == int(resource_id)).first()
            if doc and doc.folder_id:
                return {"type": ResourceType.FOLDER, "id": str(doc.folder_id)}

        elif resource_type == ResourceType.FOLDER:
            # 文件夹的父资源是父文件夹或工作空间
            from models.folder_models import Folder
            folder = self.db.query(Folder).filter(Folder.id == int(resource_id)).first()
            if folder and folder.parent_id:
                return {"type": ResourceType.FOLDER, "id": str(folder.parent_id)}

        # 没有父资源
        return None


class PermissionManager:
    """权限管理器 - 用于授权和撤销权限"""

    def __init__(self, db: Session):
        self.db = db

    def grant_permission(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        resource_id: str,
        grantee_type: GranteeType,
        grantee_id: str,
        permission: int,
        granted_by: int,
        expires_at: Optional[str] = None
    ) -> ResourcePermission:
        """
        授予权限

        Args:
            tenant_id: 租户ID
            resource_type: 资源类型
            resource_id: 资源ID
            grantee_type: 被授权者类型
            grantee_id: 被授权者ID
            permission: 权限位
            granted_by: 授权人用户ID
            expires_at: 过期时间

        Returns:
            ResourcePermission: 权限记录
        """
        # 查找已存在的权限
        existing = self.db.query(ResourcePermission).filter(
            ResourcePermission.tenant_id == tenant_id,
            ResourcePermission.resource_type == resource_type,
            ResourcePermission.resource_id == resource_id,
            ResourcePermission.grantee_type == grantee_type,
            ResourcePermission.grantee_id == grantee_id
        ).first()

        if existing:
            # 更新权限
            existing.permission = permission
            existing.granted_by = granted_by
            existing.expires_at = expires_at
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # 创建新权限
            new_perm = ResourcePermission(
                tenant_id=tenant_id,
                resource_type=resource_type,
                resource_id=resource_id,
                grantee_type=grantee_type,
                grantee_id=grantee_id,
                permission=permission,
                granted_by=granted_by,
                expires_at=expires_at
            )
            self.db.add(new_perm)
            self.db.commit()
            self.db.refresh(new_perm)
            return new_perm

    def revoke_permission(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        resource_id: str,
        grantee_type: GranteeType,
        grantee_id: str
    ) -> bool:
        """
        撤销权限

        Args:
            tenant_id: 租户ID
            resource_type: 资源类型
            resource_id: 资源ID
            grantee_type: 被授权者类型
            grantee_id: 被授权者ID

        Returns:
            bool: 是否成功撤销
        """
        deleted = self.db.query(ResourcePermission).filter(
            ResourcePermission.tenant_id == tenant_id,
            ResourcePermission.resource_type == resource_type,
            ResourcePermission.resource_id == resource_id,
            ResourcePermission.grantee_type == grantee_type,
            ResourcePermission.grantee_id == grantee_id
        ).delete()

        self.db.commit()
        return deleted > 0

    def list_resource_permissions(
        self,
        tenant_id: str,
        resource_type: ResourceType,
        resource_id: str
    ) -> List[ResourcePermission]:
        """
        列出资源的所有权限

        Args:
            tenant_id: 租户ID
            resource_type: 资源类型
            resource_id: 资源ID

        Returns:
            List[ResourcePermission]: 权限列表
        """
        return self.db.query(ResourcePermission).filter(
            ResourcePermission.tenant_id == tenant_id,
            ResourcePermission.resource_type == resource_type,
            ResourcePermission.resource_id == resource_id
        ).all()
