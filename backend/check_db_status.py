#!/usr/bin/env python3
"""
检查数据库状态
Check Database Status
"""
from sqlalchemy import create_engine, text, inspect
from api.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_database_status():
    """检查数据库状态"""
    logger.info("=" * 60)
    logger.info("检查数据库状态")
    logger.info("=" * 60)

    engine = create_engine(settings.database_url)

    try:
        with engine.connect() as conn:
            # 检查表
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            logger.info(f"\n📋 数据库中的表 ({len(tables)}个):")

            # 多租户相关的表
            tenant_tables = [
                'tenants', 'tenant_features', 'departments',
                'tenant_roles', 'tenant_users', 'resource_permissions',
                'platform_admins', 'audit_logs', 'login_history'
            ]

            existing_tenant_tables = []
            missing_tenant_tables = []

            for table in tenant_tables:
                if table in tables:
                    existing_tenant_tables.append(table)
                    logger.info(f"   ✅ {table}")
                else:
                    missing_tenant_tables.append(table)
                    logger.info(f"   ❌ {table} (不存在)")

            # 检查枚举类型
            logger.info(f"\n🔧 PostgreSQL枚举类型:")
            result = conn.execute(text("""
                SELECT typname FROM pg_type
                WHERE typtype = 'e'
                ORDER BY typname
            """))
            enums = [row[0] for row in result.fetchall()]

            for enum in enums:
                logger.info(f"   - {enum}")

            # 检查默认租户
            if 'tenants' in tables:
                logger.info(f"\n🏢 租户信息:")
                result = conn.execute(text("SELECT id, name, slug, status FROM tenants"))
                tenants = result.fetchall()
                if tenants:
                    for tenant in tenants:
                        logger.info(f"   - {tenant[1]} ({tenant[2]}) - {tenant[3]}")
                else:
                    logger.info(f"   ⚠️  没有租户")

            # 检查用户和租户关联
            if 'users' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.fetchone()[0]
                logger.info(f"\n👥 用户数量: {user_count}")

                if 'tenant_users' in tables:
                    result = conn.execute(text("SELECT COUNT(*) FROM tenant_users"))
                    tenant_user_count = result.fetchone()[0]
                    logger.info(f"   - 已加入租户的用户: {tenant_user_count}")

                    if user_count > tenant_user_count:
                        logger.info(f"   ⚠️  有 {user_count - tenant_user_count} 个用户未加入任何租户")

            # 检查平台管理员
            if 'platform_admins' in tables:
                logger.info(f"\n🔐 平台管理员:")
                result = conn.execute(text("""
                    SELECT u.username, pa.role
                    FROM platform_admins pa
                    JOIN users u ON pa.user_id = u.id
                """))
                admins = result.fetchall()
                if admins:
                    for admin in admins:
                        logger.info(f"   - {admin[0]} ({admin[1]})")
                else:
                    logger.info(f"   ⚠️  没有平台管理员")

            logger.info("\n" + "=" * 60)
            logger.info("总结:")
            logger.info("=" * 60)

            if len(missing_tenant_tables) == 0:
                logger.info("✅ 所有多租户表都已创建")
            elif len(existing_tenant_tables) == 0:
                logger.info("❌ 多租户表未创建，需要运行迁移")
            else:
                logger.info(f"⚠️  部分多租户表已创建 ({len(existing_tenant_tables)}/{len(tenant_tables)})")
                logger.info(f"   缺失的表: {', '.join(missing_tenant_tables)}")
                logger.info(f"\n建议: 需要修复数据库状态")

    except Exception as e:
        logger.error(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    check_database_status()
