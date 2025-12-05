#!/usr/bin/env python3
"""
租户诊断脚本 - 检查默认租户是否存在
"""
import sys
from pathlib import Path

# 添加backend目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from api.config import settings
from models.tenant_models import Tenant

print("=" * 60)
print("租户诊断检查")
print("=" * 60)

# 创建数据库连接
print(f"\n1. 连接数据库: {settings.database_url}")
engine = create_engine(settings.database_url)

try:
    # 测试连接
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   ✅ 数据库连接成功")
        print(f"   PostgreSQL 版本: {version[:50]}...")

    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # 检查默认租户
    print(f"\n2. 检查默认租户 (ID: 00000000-0000-0000-0000-000000000001)")
    default_tenant = db.query(Tenant).filter(
        Tenant.id == "00000000-0000-0000-0000-000000000001"
    ).first()

    if default_tenant:
        print(f"   ✅ 默认租户存在")
        print(f"   名称: {default_tenant.name}")
        print(f"   Slug: {default_tenant.slug}")
        print(f"   状态: {default_tenant.status}")
        print(f"   部署模式: {default_tenant.deploy_mode}")
        print(f"   是否激活: {default_tenant.is_active()}")
    else:
        print(f"   ❌ 默认租户不存在！")
        print(f"   需要运行数据库迁移脚本创建默认租户")

    # 列出所有租户
    print(f"\n3. 所有租户列表:")
    all_tenants = db.query(Tenant).all()
    if all_tenants:
        for tenant in all_tenants:
            status_icon = "✅" if tenant.is_active() else "❌"
            print(f"   {status_icon} {tenant.name} (ID: {tenant.id}, status: {tenant.status})")
    else:
        print(f"   ⚠️  数据库中没有任何租户")

    print(f"\n总计: {len(all_tenants)} 个租户")

    db.close()

    print("\n" + "=" * 60)
    if default_tenant and default_tenant.is_active():
        print("✅ 诊断完成 - 默认租户正常")
    else:
        print("❌ 诊断完成 - 发现问题")
        print("\n建议操作:")
        if not default_tenant:
            print("  1. 运行数据库迁移: python init_db.py")
        elif not default_tenant.is_active():
            print("  1. 激活默认租户")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    engine.dispose()
