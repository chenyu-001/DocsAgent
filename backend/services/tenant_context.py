"""
Tenant Context Service
租户上下文服务 - 管理请求级别的租户上下文
"""
from contextvars import ContextVar
from typing import Optional
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from models.tenant_models import Tenant
from models.tenant_permission_models import TenantUser

logger = logging.getLogger(__name__)

# 使用ContextVar存储当前请求的租户上下文
_tenant_context: ContextVar[Optional[Tenant]] = ContextVar('tenant_context', default=None)
_tenant_user_context: ContextVar[Optional[TenantUser]] = ContextVar('tenant_user_context', default=None)


class TenantContext:
    """租户上下文管理器"""

    @staticmethod
    def set_tenant(tenant: Tenant):
        """设置当前租户"""
        _tenant_context.set(tenant)

    @staticmethod
    def get_tenant() -> Optional[Tenant]:
        """获取当前租户"""
        return _tenant_context.get()

    @staticmethod
    def get_tenant_id() -> Optional[str]:
        """获取当前租户ID"""
        tenant = _tenant_context.get()
        return str(tenant.id) if tenant else None

    @staticmethod
    def set_tenant_user(tenant_user: TenantUser):
        """设置当前租户用户"""
        _tenant_user_context.set(tenant_user)

    @staticmethod
    def get_tenant_user() -> Optional[TenantUser]:
        """获取当前租户用户"""
        return _tenant_user_context.get()

    @staticmethod
    def clear():
        """清除上下文"""
        _tenant_context.set(None)
        _tenant_user_context.set(None)


class TenantExtractor:
    """租户提取器 - 从请求中提取租户信息"""

    @staticmethod
    def extract_tenant_id(request: Request) -> Optional[str]:
        """
        从请求中提取租户ID

        提取优先级:
        1. 路径参数: /api/tenants/{tenant_id}/...
        2. 查询参数: ?tenant_id=xxx
        3. Header: X-Tenant-ID
        4. 子域名: {tenant-slug}.example.com
        5. 默认租户

        Args:
            request: FastAPI请求对象

        Returns:
            Optional[str]: 租户ID或None
        """
        # 1. 从路径参数提取
        path_params = request.path_params
        if "tenant_id" in path_params:
            return path_params["tenant_id"]

        # 2. 从查询参数提取
        query_params = request.query_params
        if "tenant_id" in query_params:
            return query_params["tenant_id"]

        # 3. 从Header提取
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id

        # 4. 从子域名提取
        host = request.headers.get("Host", "")
        tenant_slug = TenantExtractor._extract_slug_from_host(host)
        if tenant_slug:
            # 需要通过slug查询tenant_id(在中间件中处理)
            return tenant_slug

        # 5. 返回默认租户ID(兼容旧系统)
        return "00000000-0000-0000-0000-000000000001"

    @staticmethod
    def _extract_slug_from_host(host: str) -> Optional[str]:
        """
        从Host头提取租户slug

        支持格式:
        - {slug}.example.com
        - {slug}.docsagent.local

        Args:
            host: Host头内容

        Returns:
            Optional[str]: 租户slug或None
        """
        # 移除端口号
        host = host.split(":")[0]

        # 分割域名
        parts = host.split(".")

        # 至少需要3个部分: slug.domain.tld
        if len(parts) >= 3:
            # 排除常见的前缀
            if parts[0] not in ["www", "api", "admin", "app"]:
                return parts[0]

        return None

    @staticmethod
    def get_tenant_by_identifier(db: Session, identifier: str) -> Optional[Tenant]:
        """
        通过标识符获取租户(支持ID或slug)

        Args:
            db: 数据库会话
            identifier: 租户ID或slug

        Returns:
            Optional[Tenant]: 租户对象或None
        """
        # 尝试作为UUID查询
        try:
            import uuid
            uuid.UUID(identifier)
            # 是有效的UUID,按ID查询
            return db.query(Tenant).filter(Tenant.id == identifier).first()
        except (ValueError, AttributeError):
            # 不是UUID,按slug查询
            return db.query(Tenant).filter(Tenant.slug == identifier).first()


class TenantMiddleware(BaseHTTPMiddleware):
    """租户中间件 - FastAPI中间件"""

    def __init__(self, app, get_db_func):
        """
        初始化租户中间件

        Args:
            app: FastAPI应用
            get_db_func: 获取数据库会话的函数
        """
        super().__init__(app)
        self.get_db = get_db_func
        logger.info("✅ TenantMiddleware initialized successfully")

    async def dispatch(self, request: Request, call_next):
        """
        中间件处理逻辑

        Args:
            request: 请求对象
            call_next: 下一个中间件

        Returns:
            Response: 响应对象
        """
        # 清除之前的上下文
        TenantContext.clear()

        # 跳过不需要租户验证的路径
        if self._should_skip(request.url.path):
            logger.debug(f"Skipping tenant middleware for path: {request.url.path}")
            return await call_next(request)

        try:
            # 提取租户ID
            tenant_identifier = TenantExtractor.extract_tenant_id(request)
            logger.info(f"Extracted tenant identifier: {tenant_identifier} for path: {request.url.path}")

            if tenant_identifier:
                # 获取数据库会话
                db = next(self.get_db())

                try:
                    # 查询租户
                    tenant = TenantExtractor.get_tenant_by_identifier(db, tenant_identifier)

                    if not tenant:
                        logger.error(f"❌ Tenant not found in database: {tenant_identifier}")
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Tenant not found: {tenant_identifier}"
                        )

                    # 检查租户状态
                    if not tenant.is_active():
                        logger.warning(f"Tenant inactive: {tenant.id}, status={tenant.status}")
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Tenant is not active"
                        )

                    # 设置租户上下文
                    TenantContext.set_tenant(tenant)

                    # 将租户信息附加到请求状态
                    request.state.tenant = tenant
                    request.state.tenant_id = str(tenant.id)

                    # 更新租户最后活跃时间
                    from datetime import datetime
                    tenant.last_active_at = datetime.utcnow()
                    db.commit()

                    logger.info(f"✅ Tenant context set: {tenant.id} ({tenant.name}) for path: {request.url.path}")

                finally:
                    db.close()

            # 处理请求
            response = await call_next(request)

            # 添加租户ID到响应头(便于调试)
            if hasattr(request.state, 'tenant_id'):
                response.headers["X-Tenant-ID"] = request.state.tenant_id

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tenant middleware error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Tenant context initialization failed"
            )
        finally:
            # 清除上下文
            TenantContext.clear()

    @staticmethod
    def _should_skip(path: str) -> bool:
        """
        判断是否跳过租户验证

        Args:
            path: 请求路径

        Returns:
            bool: 是否跳过
        """
        skip_paths = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/me",
            "/api/platform",  # 平台管理接口
        ]

        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return True

        return False


def get_current_tenant(request: Request) -> Tenant:
    """
    依赖注入: 获取当前租户

    用法:
    ```python
    @app.get("/api/info")
    def get_info(tenant: Tenant = Depends(get_current_tenant)):
        return {"tenant": tenant.name}
    ```

    Args:
        request: 请求对象

    Returns:
        Tenant: 当前租户

    Raises:
        HTTPException: 租户未设置时抛出401
    """
    if not hasattr(request.state, "tenant"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context not found"
        )
    return request.state.tenant


def get_current_tenant_id(request: Request) -> str:
    """
    依赖注入: 获取当前租户ID

    Args:
        request: 请求对象

    Returns:
        str: 当前租户ID

    Raises:
        HTTPException: 租户未设置时抛出401
    """
    tenant = get_current_tenant(request)
    return str(tenant.id)


def require_tenant_active():
    """
    装饰器: 要求租户处于活跃状态

    用法:
    ```python
    @app.get("/api/data")
    @require_tenant_active()
    def get_data(tenant: Tenant = Depends(get_current_tenant)):
        return {"data": "..."}
    ```
    """
    def decorator(tenant: Tenant = Depends(get_current_tenant)):
        if not tenant.is_active():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant is {tenant.status}"
            )
        return tenant
    return decorator
