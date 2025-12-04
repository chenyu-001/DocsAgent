#!/usr/bin/env python3
"""
修复Admin权限脚本
Fix Admin Permissions Script

功能：
1. 将 admin 用户设置为 PlatformAdmin (SUPER_ADMIN)
2. 将 admin 用户加入默认租户，并设置为 tenant_admin
3. 检查并修复运维账号的权限

使用方法:
python fix_admin_permissions.py --username admin
"""
import sys
from pathlib import Path

# 添加backend目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.config import settings
from models.user_models import User
from models.tenant_models import Tenant
from models.tenant_permission_models import (
    PlatformAdmin, PlatformRole, TenantUser, TenantRole
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def fix_admin_permissions(username: str = "admin"):
    """
    修复admin权限

    Args:
        username: 要修复的用户名
    """
    logger.info("=" * 60)
    logger.info(f"修复 {username} 用户的权限")
    logger.info("=" * 60)

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 1. 查找用户
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.error(f"❌ 用户 {username} 不存在")
            return

        logger.info(f"✓ 找到用户: {user.username} (ID: {user.id})")

        # 2. 检查并创建 PlatformAdmin
        platform_admin = db.query(PlatformAdmin).filter(
            PlatformAdmin.user_id == user.id
        ).first()

        if platform_admin:
            logger.info(f"✓ 用户已是平台管理员: {platform_admin.role.value}")
            # 更新为 SUPER_ADMIN（如果不是）
            if platform_admin.role != PlatformRole.SUPER_ADMIN:
                platform_admin.role = PlatformRole.SUPER_ADMIN
                db.commit()
                logger.info(f"✓ 已升级为 SUPER_ADMIN")
        else:
            # 创建 PlatformAdmin
            platform_admin = PlatformAdmin(
                user_id=user.id,
                role=PlatformRole.SUPER_ADMIN,
                scope=None  # 无限制
            )
            db.add(platform_admin)
            db.commit()
            logger.info("✓ 已设置为平台超级管理员 (SUPER_ADMIN)")

        # 3. 查找默认租户
        default_tenant = db.query(Tenant).filter(
            Tenant.id == DEFAULT_TENANT_ID
        ).first()

        if not default_tenant:
            logger.warning("⚠️  默认租户不存在，请先运行数据库迁移")
            return

        logger.info(f"✓ 找到默认租户: {default_tenant.name}")

        # 4. 查找 tenant_admin 角色
        tenant_admin_role = db.query(TenantRole).filter(
            TenantRole.tenant_id == default_tenant.id,
            TenantRole.name == "tenant_admin"
        ).first()

        if not tenant_admin_role:
            logger.error("❌ tenant_admin 角色不存在")
            return

        logger.info(f"✓ 找到租户管理员角色: {tenant_admin_role.display_name}")

        # 5. 检查并创建 TenantUser
        tenant_user = db.query(TenantUser).filter(
            TenantUser.user_id == user.id,
            TenantUser.tenant_id == default_tenant.id
        ).first()

        if tenant_user:
            logger.info(f"✓ 用户已在租户中")
            # 更新角色为 tenant_admin
            if tenant_user.role_id != tenant_admin_role.id:
                tenant_user.role_id = tenant_admin_role.id
                tenant_user.status = "active"
                db.commit()
                logger.info(f"✓ 已设置为租户管理员")
            else:
                logger.info(f"✓ 用户已是租户管理员")
        else:
            # 创建 TenantUser
            import uuid
            tenant_user = TenantUser(
                id=uuid.uuid4(),
                tenant_id=default_tenant.id,
                user_id=user.id,
                role_id=tenant_admin_role.id,
                status="active"
            )
            db.add(tenant_user)
            db.commit()
            logger.info("✓ 已将用户加入默认租户并设置为管理员")

        logger.info("\n" + "=" * 60)
        logger.info("✅ 权限修复完成!")
        logger.info("=" * 60)
        logger.info(f"\n📋 用户 {username} 现在拥有:")
        logger.info(f"   1️⃣ 平台管理员权限 (SUPER_ADMIN)")
        logger.info(f"      - 可以管理所有租户")
        logger.info(f"      - 可以跨租户访问数据")
        logger.info(f"   2️⃣ 租户管理员权限 (tenant_admin)")
        logger.info(f"      - 可以管理租户内的用户和权限")
        logger.info(f"      - 可以使用所有业务功能（上传文档、问答等）")
        logger.info(f"\n🔐 登录信息:")
        logger.info(f"   用户名: {username}")
        logger.info(f"   默认密码: admin123 (如未修改)")
        logger.info(f"   租户ID: {DEFAULT_TENANT_ID}")

    except Exception as e:
        logger.error(f"❌ 修复失败: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
        engine.dispose()


def check_user_permissions(username: str):
    """
    检查用户的当前权限

    Args:
        username: 用户名
    """
    logger.info("=" * 60)
    logger.info(f"检查用户权限: {username}")
    logger.info("=" * 60)

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 查找用户
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.error(f"❌ 用户 {username} 不存在")
            return

        logger.info(f"\n👤 用户信息:")
        logger.info(f"   ID: {user.id}")
        logger.info(f"   用户名: {user.username}")
        logger.info(f"   邮箱: {user.email}")
        logger.info(f"   老角色(User.role): {user.role.value}")

        # 检查 PlatformAdmin
        platform_admin = db.query(PlatformAdmin).filter(
            PlatformAdmin.user_id == user.id
        ).first()

        logger.info(f"\n🔧 平台管理员权限:")
        if platform_admin:
            logger.info(f"   ✅ 是平台管理员")
            logger.info(f"   角色: {platform_admin.role.value}")
            logger.info(f"   权限范围: {platform_admin.scope or '无限制'}")
        else:
            logger.info(f"   ❌ 不是平台管理员")

        # 检查租户归属
        tenant_users = db.query(TenantUser).filter(
            TenantUser.user_id == user.id
        ).all()

        logger.info(f"\n🏢 租户归属:")
        if tenant_users:
            for tu in tenant_users:
                tenant = db.query(Tenant).filter(Tenant.id == tu.tenant_id).first()
                role = db.query(TenantRole).filter(TenantRole.id == tu.role_id).first()
                logger.info(f"   - 租户: {tenant.name if tenant else 'Unknown'} ({tu.tenant_id})")
                logger.info(f"     角色: {role.display_name if role else 'None'} ({role.name if role else 'None'})")
                logger.info(f"     状态: {tu.status}")
                logger.info(f"     权限位: {role.permissions if role else 0}")
        else:
            logger.info(f"   ❌ 未加入任何租户")

        logger.info("\n" + "=" * 60)

    except Exception as e:
        logger.error(f"❌ 检查失败: {e}", exc_info=True)
    finally:
        db.close()
        engine.dispose()


def create_ops_user(username: str, email: str, password: str = "ops123", full_name: str = "运维人员"):
    """
    创建运维账号

    Args:
        username: 用户名
        email: 邮箱
        password: 密码
        full_name: 全名
    """
    logger.info("=" * 60)
    logger.info(f"创建运维账号: {username}")
    logger.info("=" * 60)

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            logger.info(f"⚠️  用户 {username} 已存在 (ID: {existing_user.id})")
            user = existing_user
        else:
            # 创建用户
            user = User(
                username=username,
                email=email,
                hashed_password=pwd_context.hash(password),
                full_name=full_name,
                role="user",  # 老的角色字段设为 user
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"✓ 创建用户: {username} (ID: {user.id})")

        # 创建 PlatformAdmin
        platform_admin = db.query(PlatformAdmin).filter(
            PlatformAdmin.user_id == user.id
        ).first()

        if platform_admin:
            logger.info(f"✓ 用户已是平台管理员: {platform_admin.role.value}")
            # 更新为 OPS
            if platform_admin.role != PlatformRole.OPS:
                platform_admin.role = PlatformRole.OPS
                db.commit()
                logger.info(f"✓ 已更新为 OPS")
        else:
            platform_admin = PlatformAdmin(
                user_id=user.id,
                role=PlatformRole.OPS,
                scope=None
            )
            db.add(platform_admin)
            db.commit()
            logger.info("✓ 已设置为平台运维人员 (OPS)")

        # 查找默认租户和 member 角色
        default_tenant = db.query(Tenant).filter(
            Tenant.id == DEFAULT_TENANT_ID
        ).first()

        if default_tenant:
            member_role = db.query(TenantRole).filter(
                TenantRole.tenant_id == default_tenant.id,
                TenantRole.name == "member"
            ).first()

            if member_role:
                # 将运维人员加入租户（普通成员权限）
                tenant_user = db.query(TenantUser).filter(
                    TenantUser.user_id == user.id,
                    TenantUser.tenant_id == default_tenant.id
                ).first()

                if not tenant_user:
                    import uuid
                    tenant_user = TenantUser(
                        id=uuid.uuid4(),
                        tenant_id=default_tenant.id,
                        user_id=user.id,
                        role_id=member_role.id,
                        status="active"
                    )
                    db.add(tenant_user)
                    db.commit()
                    logger.info("✓ 已将运维人员加入默认租户（普通成员权限）")
                else:
                    logger.info("✓ 运维人员已在租户中")

        logger.info("\n" + "=" * 60)
        logger.info("✅ 运维账号创建完成!")
        logger.info("=" * 60)
        logger.info(f"\n📋 账号信息:")
        logger.info(f"   用户名: {username}")
        logger.info(f"   密码: {password}")
        logger.info(f"   邮箱: {email}")
        logger.info(f"   平台权限: OPS (运维人员)")
        logger.info(f"   租户权限: member (普通成员)")
        logger.info(f"\n💡 权限说明:")
        logger.info(f"   - 可以管理系统（平台级）")
        logger.info(f"   - 可以使用业务功能（上传文档、问答等）")

    except Exception as e:
        logger.error(f"❌ 创建失败: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="修复Admin权限")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="修复admin用户的权限"
    )
    parser.add_argument(
        "--username",
        default="admin",
        help="要修复的用户名（默认: admin）"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查用户的当前权限"
    )
    parser.add_argument(
        "--create-ops",
        action="store_true",
        help="创建运维账号"
    )
    parser.add_argument(
        "--ops-username",
        default="ops",
        help="运维账号用户名（默认: ops）"
    )
    parser.add_argument(
        "--ops-email",
        default="ops@docsagent.com",
        help="运维账号邮箱（默认: ops@docsagent.com）"
    )
    parser.add_argument(
        "--ops-password",
        default="ops123",
        help="运维账号密码（默认: ops123）"
    )

    args = parser.parse_args()

    if args.fix:
        fix_admin_permissions(args.username)
    elif args.check:
        check_user_permissions(args.username)
    elif args.create_ops:
        create_ops_user(
            username=args.ops_username,
            email=args.ops_email,
            password=args.ops_password
        )
    else:
        parser.print_help()
        print("\n示例:")
        print("  # 修复admin用户权限")
        print("  python fix_admin_permissions.py --fix")
        print()
        print("  # 检查admin用户权限")
        print("  python fix_admin_permissions.py --check --username admin")
        print()
        print("  # 创建运维账号")
        print("  python fix_admin_permissions.py --create-ops")
        print()
        print("  # 创建自定义运维账号")
        print("  python fix_admin_permissions.py --create-ops --ops-username ops2 --ops-password mypass123")
