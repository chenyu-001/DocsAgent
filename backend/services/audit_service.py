"""
Audit Service
审计服务 - 记录所有敏感操作
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Request
import logging
import uuid
import json

from models.audit_models import AuditLog, LoginHistory, AuditAction, AuditLevel
from models.user_models import User
from services.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class AuditService:
    """审计服务"""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: AuditAction,
        user: Optional[User] = None,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.INFO,
        success: bool = True,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> AuditLog:
        """
        记录审计日志

        Args:
            action: 操作类型
            user: 用户对象
            user_id: 用户ID(如果user为None)
            resource_type: 资源类型
            resource_id: 资源ID
            resource_name: 资源名称
            details: 详细信息
            changes: 变更内容(before/after)
            level: 审计级别
            success: 是否成功
            error_message: 错误消息
            error_code: 错误码
            ip_address: IP地址
            user_agent: User Agent
            request_id: 请求ID
            duration_ms: 操作耗时

        Returns:
            AuditLog: 审计日志对象
        """
        try:
            # 获取租户ID
            tenant = TenantContext.get_tenant()
            tenant_id = str(tenant.id) if tenant else None

            # 获取用户信息
            if user:
                user_id = user.id
                username = user.username
                user_role = user.role.value if hasattr(user, 'role') else None
            else:
                username = None
                user_role = None
                if user_id:
                    # 尝试查询用户名
                    user_obj = self.db.query(User).filter(User.id == user_id).first()
                    if user_obj:
                        username = user_obj.username
                        user_role = user_obj.role.value if hasattr(user_obj, 'role') else None

            # 创建审计日志
            audit_log = AuditLog(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                action=action,
                level=level,
                user_id=user_id,
                username=username,
                user_role=user_role,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                details=details,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                success=success,
                error_message=error_message,
                error_code=error_code,
                duration_ms=duration_ms
            )

            self.db.add(audit_log)
            self.db.commit()

            logger.info(
                f"Audit log created: action={action.value}, user={username}, "
                f"resource={resource_type}:{resource_id}, success={success}"
            )

            return audit_log

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            self.db.rollback()
            # 审计日志失败不应该影响主流程
            return None

    def log_from_request(
        self,
        request: Request,
        action: AuditAction,
        user: Optional[User] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.INFO,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        从Request对象记录审计日志

        Args:
            request: FastAPI Request对象
            action: 操作类型
            user: 用户对象
            resource_type: 资源类型
            resource_id: 资源ID
            resource_name: 资源名称
            details: 详细信息
            level: 审计级别
            success: 是否成功
            error_message: 错误消息

        Returns:
            AuditLog: 审计日志对象
        """
        # 从请求中提取信息
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent")
        request_id = request.headers.get("X-Request-ID")

        return self.log(
            action=action,
            user=user,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            details=details,
            level=level,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id
        )

    def log_login(
        self,
        user: User,
        success: bool,
        login_type: str = "password",
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[Dict[str, str]] = None
    ) -> LoginHistory:
        """
        记录登录历史

        Args:
            user: 用户对象
            success: 是否成功
            login_type: 登录方式
            failure_reason: 失败原因
            ip_address: IP地址
            user_agent: User Agent
            device_info: 设备信息(device_type, browser, os)

        Returns:
            LoginHistory: 登录历史对象
        """
        try:
            # 获取租户ID
            tenant = TenantContext.get_tenant()
            tenant_id = str(tenant.id) if tenant else None

            # 创建登录历史
            login_history = LoginHistory(
                id=uuid.uuid4(),
                user_id=user.id,
                tenant_id=tenant_id,
                username=user.username,
                login_type=login_type,
                success=success,
                failure_reason=failure_reason,
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_info.get("device_type") if device_info else None,
                browser=device_info.get("browser") if device_info else None,
                os=device_info.get("os") if device_info else None
            )

            self.db.add(login_history)
            self.db.commit()

            # 同时记录审计日志
            if success:
                self.log(
                    action=AuditAction.USER_LOGIN,
                    user=user,
                    level=AuditLevel.INFO,
                    success=True,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={"login_type": login_type}
                )
            else:
                self.log(
                    action=AuditAction.USER_LOGIN,
                    user_id=user.id,
                    level=AuditLevel.WARNING,
                    success=False,
                    error_message=failure_reason,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={"login_type": login_type}
                )

            return login_history

        except Exception as e:
            logger.error(f"Failed to create login history: {e}", exc_info=True)
            self.db.rollback()
            return None

    def log_logout(self, user: User, login_history_id: Optional[str] = None):
        """
        记录登出

        Args:
            user: 用户对象
            login_history_id: 登录历史ID
        """
        try:
            # 更新登录历史
            if login_history_id:
                login_history = self.db.query(LoginHistory).filter(
                    LoginHistory.id == login_history_id
                ).first()

                if login_history:
                    login_history.logout_at = datetime.utcnow()
                    if login_history.created_at:
                        duration = (datetime.utcnow() - login_history.created_at).total_seconds()
                        login_history.session_duration = int(duration)
                    self.db.commit()

            # 记录审计日志
            self.log(
                action=AuditAction.USER_LOGOUT,
                user=user,
                level=AuditLevel.INFO,
                success=True
            )

        except Exception as e:
            logger.error(f"Failed to log logout: {e}", exc_info=True)
            self.db.rollback()

    @staticmethod
    def _get_client_ip(request: Request) -> Optional[str]:
        """
        获取客户端真实IP

        Args:
            request: Request对象

        Returns:
            Optional[str]: IP地址
        """
        # 尝试从X-Forwarded-For获取
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # 尝试从X-Real-IP获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 使用客户端地址
        if request.client:
            return request.client.host

        return None


def audit_decorator(action: AuditAction, level: AuditLevel = AuditLevel.INFO):
    """
    审计装饰器 - 自动记录函数调用

    用法:
    ```python
    @audit_decorator(AuditAction.DOC_DELETE, level=AuditLevel.CRITICAL)
    async def delete_document(doc_id: int, current_user: User, db: Session):
        # 删除逻辑
        pass
    ```

    Args:
        action: 审计操作类型
        level: 审计级别

    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 提取参数
            db = kwargs.get("db")
            current_user = kwargs.get("current_user")
            request = kwargs.get("request")

            if not db:
                # 如果没有db参数,直接执行函数
                return await func(*args, **kwargs)

            audit_service = AuditService(db)
            start_time = datetime.utcnow()

            try:
                # 执行函数
                result = await func(*args, **kwargs)

                # 计算耗时
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                # 记录成功日志
                if request:
                    audit_service.log_from_request(
                        request=request,
                        action=action,
                        user=current_user,
                        level=level,
                        success=True,
                        details={"duration_ms": duration_ms}
                    )
                else:
                    audit_service.log(
                        action=action,
                        user=current_user,
                        level=level,
                        success=True,
                        duration_ms=duration_ms
                    )

                return result

            except Exception as e:
                # 计算耗时
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                # 记录失败日志
                if request:
                    audit_service.log_from_request(
                        request=request,
                        action=action,
                        user=current_user,
                        level=AuditLevel.WARNING,
                        success=False,
                        error_message=str(e),
                        details={"duration_ms": duration_ms}
                    )
                else:
                    audit_service.log(
                        action=action,
                        user=current_user,
                        level=AuditLevel.WARNING,
                        success=False,
                        error_message=str(e),
                        duration_ms=duration_ms
                    )

                # 重新抛出异常
                raise

        return wrapper
    return decorator
