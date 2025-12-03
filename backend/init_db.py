#!/usr/bin/env python3
"""
Database Initialization Script
初始化数据库表和多租户架构
"""
import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from api.config import settings
from api.db import Base
import logging

# 导入所有模型以确保它们被注册到Base.metadata
from models import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration_file(engine, migration_file: str):
    """
    执行SQL迁移文件

    Args:
        engine: SQLAlchemy引擎
        migration_file: 迁移文件路径
    """
    logger.info(f"Running migration: {migration_file}")

    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 分割SQL语句并执行
        with engine.connect() as conn:
            # 使用事务执行
            trans = conn.begin()
            try:
                # 执行整个SQL文件
                conn.execute(text(sql_content))
                trans.commit()
                logger.info(f"Successfully executed migration: {migration_file}")
            except Exception as e:
                trans.rollback()
                logger.error(f"Failed to execute migration {migration_file}: {e}")
                raise

    except FileNotFoundError:
        logger.warning(f"Migration file not found: {migration_file}")
    except Exception as e:
        logger.error(f"Error reading migration file {migration_file}: {e}")
        raise


def init_database(drop_existing: bool = False):
    """
    初始化数据库

    Args:
        drop_existing: 是否删除现有表
    """
    logger.info("=" * 60)
    logger.info("DocsAgent - Multi-Tenant Database Initialization")
    logger.info("=" * 60)

    # 创建数据库引擎
    logger.info(f"Connecting to database: {settings.database_url}")
    engine = create_engine(settings.database_url)

    try:
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"Connected to PostgreSQL: {version}")

        if drop_existing:
            logger.warning("⚠️  Dropping all existing tables...")
            Base.metadata.drop_all(bind=engine)
            logger.info("✓ All tables dropped")

        # 创建所有表
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ All tables created")

        # 执行迁移脚本
        migrations_dir = Path(__file__).parent / "migrations"
        if migrations_dir.exists():
            logger.info("Running migration scripts...")

            # 按顺序执行迁移
            migration_files = sorted(migrations_dir.glob("*.sql"))
            for migration_file in migration_files:
                run_migration_file(engine, str(migration_file))

            logger.info("✓ All migrations completed")
        else:
            logger.warning("No migrations directory found")

        # 验证表创建
        logger.info("Verifying table creation...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]

            logger.info(f"Created {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table}")

        logger.info("=" * 60)
        logger.info("✅ Database initialization completed successfully!")
        logger.info("=" * 60)

        # 显示默认租户信息
        logger.info("\n📋 Default Tenant Information:")
        logger.info("   Tenant ID: 00000000-0000-0000-0000-000000000001")
        logger.info("   Tenant Name: Default Tenant")
        logger.info("   Tenant Slug: default")
        logger.info("\n   All existing users have been migrated to the default tenant.")
        logger.info("   System roles created: tenant_admin, member, guest")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        engine.dispose()


def create_test_tenant():
    """创建测试租户(用于开发测试)"""
    from api.db import get_db
    from models.tenant_models import Tenant, DeployMode, TenantStatus
    from models.tenant_permission_models import TenantRole, Permission
    import uuid

    logger.info("\n" + "=" * 60)
    logger.info("Creating Test Tenant")
    logger.info("=" * 60)

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 创建测试租户
        test_tenant_id = uuid.uuid4()
        test_tenant = Tenant(
            id=test_tenant_id,
            name="Test Company",
            slug="test-company",
            description="Test tenant for development",
            deploy_mode=DeployMode.CLOUD,
            status=TenantStatus.ACTIVE,
            storage_quota_bytes=10737418240,  # 10GB
            user_quota=50,
            document_quota=5000
        )

        db.add(test_tenant)
        db.commit()
        logger.info(f"✓ Created test tenant: {test_tenant_id}")

        # 创建角色
        roles_data = [
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
                "name": "manager",
                "display_name": "管理者",
                "description": "可以管理团队和文档",
                "level": 50,
                "permissions": Permission.EDITOR | Permission.SHARE | Permission.ADMIN,
                "is_system": True,
                "is_default": False
            },
            {
                "name": "member",
                "display_name": "成员",
                "description": "普通成员,可以创建和编辑文档",
                "level": 10,
                "permissions": Permission.EDITOR,
                "is_system": True,
                "is_default": True
            },
            {
                "name": "guest",
                "display_name": "访客",
                "description": "只读访问权限",
                "level": 1,
                "permissions": Permission.READER,
                "is_system": True,
                "is_default": False
            }
        ]

        for role_data in roles_data:
            role = TenantRole(
                id=uuid.uuid4(),
                tenant_id=test_tenant_id,
                **role_data
            )
            db.add(role)

        db.commit()
        logger.info("✓ Created tenant roles")

        logger.info("\n📋 Test Tenant Information:")
        logger.info(f"   Tenant ID: {test_tenant_id}")
        logger.info(f"   Tenant Name: Test Company")
        logger.info(f"   Tenant Slug: test-company")
        logger.info(f"   Access URL: http://test-company.localhost:8000")

        logger.info("=" * 60)
        logger.info("✅ Test tenant created successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Failed to create test tenant: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize DocsAgent database with multi-tenant support")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all existing tables before initialization (⚠️  WARNING: This will delete all data!)"
    )
    parser.add_argument(
        "--create-test-tenant",
        action="store_true",
        help="Create a test tenant for development"
    )

    args = parser.parse_args()

    if args.drop:
        confirm = input("⚠️  WARNING: This will delete all existing data. Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            logger.info("Aborted.")
            sys.exit(0)

    # 初始化数据库
    init_database(drop_existing=args.drop)

    # 创建测试租户
    if args.create_test_tenant:
        create_test_tenant()

    logger.info("\n✅ All done! You can now start the application.")
