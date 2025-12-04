#!/usr/bin/env python3
"""
修复迁移冲突
Fix Migration Conflicts
"""
from sqlalchemy import create_engine, text
from api.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def fix_migration_conflicts():
    """修复迁移冲突"""
    logger.info("=" * 60)
    logger.info("修复数据库迁移冲突")
    logger.info("=" * 60)

    engine = create_engine(settings.database_url)

    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                # 1. 检查并创建枚举类型（如果不存在）
                logger.info("\n步骤 1: 检查枚举类型...")

                enums_to_create = [
                    ("deploymode", ["cloud", "hybrid", "local"]),
                    ("tenantstatus", ["active", "suspended", "archived", "trial"]),
                    ("resourcetype", ["workspace", "folder", "document"]),
                    ("granteetype", ["user", "role", "department"]),
                    ("platformrole", ["super_admin", "ops", "support", "auditor"]),
                    ("auditaction", ["USER_CREATE", "USER_UPDATE", "USER_DELETE", "DOC_CREATE", "DOC_UPDATE", "DOC_DELETE", "FOLDER_CREATE", "FOLDER_UPDATE", "FOLDER_DELETE", "ACL_GRANT", "ACL_REVOKE", "LOGIN", "LOGOUT", "PERMISSION_CHANGE", "TENANT_CREATE", "TENANT_UPDATE", "CONFIG_CHANGE"]),
                    ("auditlevel", ["info", "warning", "error", "critical"])
                ]

                for enum_name, enum_values in enums_to_create:
                    # 检查枚举是否存在
                    result = conn.execute(text(f"""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_type WHERE typname = '{enum_name}'
                        )
                    """))
                    exists = result.fetchone()[0]

                    if not exists:
                        values_str = "', '".join(enum_values)
                        conn.execute(text(f"""
                            CREATE TYPE {enum_name} AS ENUM ('{values_str}')
                        """))
                        logger.info(f"   ✓ 创建枚举类型: {enum_name}")
                    else:
                        logger.info(f"   ✓ 枚举类型已存在: {enum_name}")

                # 2. 创建表（使用 IF NOT EXISTS）
                logger.info("\n步骤 2: 创建表...")

                # Tenants 表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS tenants (
                        id UUID PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        slug VARCHAR(100) UNIQUE NOT NULL,
                        description TEXT,
                        deploy_mode deploymode NOT NULL DEFAULT 'cloud',
                        db_connection TEXT,
                        db_schema VARCHAR(100),
                        vector_db_config JSON,
                        vector_namespace VARCHAR(100),
                        storage_config JSON,
                        storage_quota_bytes BIGINT NOT NULL DEFAULT 10737418240,
                        user_quota INTEGER NOT NULL DEFAULT 10,
                        document_quota INTEGER NOT NULL DEFAULT 1000,
                        storage_used_bytes BIGINT NOT NULL DEFAULT 0,
                        user_count INTEGER NOT NULL DEFAULT 0,
                        document_count INTEGER NOT NULL DEFAULT 0,
                        status tenantstatus NOT NULL DEFAULT 'trial',
                        expires_at TIMESTAMP,
                        trial_ends_at TIMESTAMP,
                        license_key VARCHAR(500),
                        license_data JSON,
                        contact_name VARCHAR(100),
                        contact_email VARCHAR(100),
                        contact_phone VARCHAR(50),
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        last_active_at TIMESTAMP
                    )
                """))
                logger.info("   ✓ 表: tenants")

                # Tenant Features 表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS tenant_features (
                        id SERIAL PRIMARY KEY,
                        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                        feature_key VARCHAR(50) NOT NULL,
                        enabled BOOLEAN NOT NULL DEFAULT false,
                        config JSON,
                        usage_limit INTEGER,
                        usage_count INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """))
                logger.info("   ✓ 表: tenant_features")

                # Departments 表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS departments (
                        id UUID PRIMARY KEY,
                        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        parent_id UUID,
                        path VARCHAR(1000) NOT NULL,
                        level INTEGER NOT NULL DEFAULT 0,
                        manager_id INTEGER,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """))
                logger.info("   ✓ 表: departments")

                # Tenant Roles 表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS tenant_roles (
                        id UUID PRIMARY KEY,
                        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                        name VARCHAR(50) NOT NULL,
                        display_name VARCHAR(100) NOT NULL,
                        description TEXT,
                        level INTEGER NOT NULL DEFAULT 0,
                        permissions INTEGER NOT NULL DEFAULT 33,
                        is_system BOOLEAN NOT NULL DEFAULT false,
                        is_default BOOLEAN NOT NULL DEFAULT false,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """))
                logger.info("   ✓ 表: tenant_roles")

                # Tenant Users 表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS tenant_users (
                        id UUID PRIMARY KEY,
                        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        role_id UUID REFERENCES tenant_roles(id) ON DELETE SET NULL,
                        department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'active',
                        invited_by INTEGER,
                        invited_at TIMESTAMP,
                        joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        last_active_at TIMESTAMP,
                        UNIQUE(tenant_id, user_id)
                    )
                """))
                logger.info("   ✓ 表: tenant_users")

                # Resource Permissions 表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS resource_permissions (
                        id UUID PRIMARY KEY,
                        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                        resource_type resourcetype NOT NULL,
                        resource_id VARCHAR(100) NOT NULL,
                        grantee_type granteetype NOT NULL,
                        grantee_id VARCHAR(100) NOT NULL,
                        permission INTEGER NOT NULL DEFAULT 33,
                        inherit BOOLEAN NOT NULL DEFAULT true,
                        granted_by INTEGER,
                        granted_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """))
                logger.info("   ✓ 表: resource_permissions")

                # Platform Admins 表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS platform_admins (
                        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                        role platformrole NOT NULL DEFAULT 'support',
                        scope TEXT,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        last_login_at TIMESTAMP
                    )
                """))
                logger.info("   ✓ 表: platform_admins")

                # Audit Logs 表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id BIGSERIAL PRIMARY KEY,
                        tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
                        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        username VARCHAR(50),
                        action auditaction NOT NULL,
                        resource_type VARCHAR(50),
                        resource_id VARCHAR(100),
                        details JSON,
                        ip_address VARCHAR(50),
                        user_agent TEXT,
                        level auditlevel NOT NULL DEFAULT 'info',
                        success BOOLEAN NOT NULL DEFAULT true,
                        error_message TEXT,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """))
                logger.info("   ✓ 表: audit_logs")

                # Login History 表
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS login_history (
                        id BIGSERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        username VARCHAR(50) NOT NULL,
                        login_type VARCHAR(20) NOT NULL DEFAULT 'password',
                        ip_address VARCHAR(50),
                        user_agent TEXT,
                        location VARCHAR(100),
                        success BOOLEAN NOT NULL DEFAULT true,
                        failure_reason TEXT,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """))
                logger.info("   ✓ 表: login_history")

                # 3. 创建索引
                logger.info("\n步骤 3: 创建索引...")

                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant ON tenant_users(tenant_id)",
                    "CREATE INDEX IF NOT EXISTS idx_tenant_users_user ON tenant_users(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_resource_permissions_tenant ON resource_permissions(tenant_id)",
                    "CREATE INDEX IF NOT EXISTS idx_resource_permissions_resource ON resource_permissions(tenant_id, resource_type, resource_id)",
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id)",
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_login_history_user ON login_history(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_login_history_created ON login_history(created_at DESC)"
                ]

                for index_sql in indexes:
                    conn.execute(text(index_sql))
                    logger.info(f"   ✓ 索引已创建")

                # 4. 创建默认租户
                logger.info("\n步骤 4: 创建默认租户...")

                conn.execute(text("""
                    INSERT INTO tenants (
                        id, name, slug, description, deploy_mode, status,
                        storage_quota_bytes, user_quota, document_quota,
                        storage_used_bytes, user_count, document_count,
                        created_at, updated_at
                    )
                    VALUES (
                        '00000000-0000-0000-0000-000000000001',
                        'Default Tenant',
                        'default',
                        'Default tenant for legacy data',
                        'CLOUD',
                        'ACTIVE',
                        10737418240,
                        100,
                        10000,
                        0,
                        0,
                        0,
                        NOW(),
                        NOW()
                    ) ON CONFLICT (id) DO NOTHING
                """))
                logger.info("   ✓ 默认租户已创建")

                # 5. 创建默认角色
                logger.info("\n步骤 5: 创建默认角色...")

                conn.execute(text("""
                    INSERT INTO tenant_roles (id, tenant_id, name, display_name, description, level, permissions, is_system, is_default, created_at, updated_at)
                    VALUES
                        (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'tenant_admin', '租户管理员', '拥有租户内所有权限', 100, 255, true, false, NOW(), NOW()),
                        (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'member', '成员', '普通成员,可以创建和编辑自己的文档', 10, 67, true, true, NOW(), NOW()),
                        (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'guest', '访客', '只读访问权限', 1, 33, true, false, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """))
                logger.info("   ✓ 默认角色已创建")

                # 6. 迁移现有用户
                logger.info("\n步骤 6: 迁移现有用户到默认租户...")

                conn.execute(text("""
                    INSERT INTO tenant_users (id, tenant_id, user_id, role_id, status, joined_at, created_at, updated_at)
                    SELECT
                        gen_random_uuid(),
                        '00000000-0000-0000-0000-000000000001',
                        u.id,
                        (SELECT id FROM tenant_roles WHERE tenant_id = '00000000-0000-0000-0000-000000000001' AND is_default = true LIMIT 1),
                        'active',
                        NOW(),
                        NOW(),
                        NOW()
                    FROM users u
                    WHERE NOT EXISTS (
                        SELECT 1 FROM tenant_users tu
                        WHERE tu.user_id = u.id AND tu.tenant_id = '00000000-0000-0000-0000-000000000001'
                    )
                """))
                logger.info("   ✓ 用户已迁移到默认租户")

                # 7. 添加租户字段到现有表（如果不存在）
                logger.info("\n步骤 7: 更新现有表...")

                # 检查documents表是否有tenant_id字段
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'documents' AND column_name = 'tenant_id'
                """))
                if not result.fetchone():
                    conn.execute(text("""
                        ALTER TABLE documents ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE
                    """))
                    logger.info("   ✓ documents表添加tenant_id字段")

                # 更新documents的tenant_id
                conn.execute(text("""
                    UPDATE documents SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL
                """))

                # 检查folders表
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'folders' AND column_name = 'tenant_id'
                """))
                if not result.fetchone():
                    conn.execute(text("""
                        ALTER TABLE folders ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE
                    """))
                    logger.info("   ✓ folders表添加tenant_id字段")

                conn.execute(text("""
                    UPDATE folders SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL
                """))

                # 检查acls表
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'acls' AND column_name = 'tenant_id'
                """))
                if not result.fetchone():
                    conn.execute(text("""
                        ALTER TABLE acls ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE
                    """))
                    logger.info("   ✓ acls表添加tenant_id字段")

                conn.execute(text("""
                    UPDATE acls SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL
                """))

                trans.commit()

                logger.info("\n" + "=" * 60)
                logger.info("✅ 数据库迁移修复完成!")
                logger.info("=" * 60)

            except Exception as e:
                trans.rollback()
                raise e

    except Exception as e:
        logger.error(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    fix_migration_conflicts()
