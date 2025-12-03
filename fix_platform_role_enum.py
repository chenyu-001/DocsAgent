#!/usr/bin/env python3
"""
修复 platform_admins 表的枚举类型问题
解决: invalid input value for enum platformrole 错误
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def get_database_url():
    """获取数据库连接URL"""
    from dotenv import load_dotenv
    load_dotenv()

    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        # 构建默认的数据库URL
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_user = os.getenv('DB_USER', 'docsagent')
        db_pass = os.getenv('DB_PASSWORD', 'docsagent')
        db_name = os.getenv('DB_NAME', 'docsagent')
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    return db_url


def fix_platform_role_enum():
    """修复 platformrole 枚举类型"""

    print("=" * 60)
    print("修复 platform_admins 表的枚举类型")
    print("=" * 60)
    print()

    try:
        # 连接数据库
        db_url = get_database_url()
        print(f"连接数据库...")
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()

            try:
                print("\n步骤 1: 检查现有枚举类型...")
                result = conn.execute(text(
                    "SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'platformrole')"
                ))
                enum_exists = result.scalar()

                if enum_exists:
                    print("  ✓ 找到现有的 platformrole 枚举类型")

                    # 获取当前枚举值
                    result = conn.execute(text(
                        "SELECT enumlabel FROM pg_enum WHERE enumtypid = "
                        "(SELECT oid FROM pg_type WHERE typname = 'platformrole') "
                        "ORDER BY enumsortorder"
                    ))
                    current_values = [row[0] for row in result]
                    print(f"  当前枚举值: {current_values}")

                    # 检查是否需要修复
                    expected_values = ['super_admin', 'ops', 'support', 'auditor']
                    if set(current_values) == set(expected_values):
                        print("  ✓ 枚举值正确，无需修复")
                        trans.commit()
                        print("\n✅ 枚举类型已正确配置！")
                        print_usage_examples()
                        return

                    print(f"  ⚠ 枚举值不匹配，需要修复")
                    print(f"  期望值: {expected_values}")

                    # 临时修改列类型
                    print("\n步骤 2: 临时修改列类型为 VARCHAR...")
                    conn.execute(text(
                        "ALTER TABLE platform_admins ALTER COLUMN role TYPE VARCHAR(20)"
                    ))
                    print("  ✓ 列类型已临时修改")

                    # 删除旧枚举类型
                    print("\n步骤 3: 删除旧的枚举类型...")
                    conn.execute(text("DROP TYPE platformrole CASCADE"))
                    print("  ✓ 旧枚举类型已删除")
                else:
                    print("  ⚠ platformrole 枚举类型不存在")

                # 创建新的枚举类型
                print("\n步骤 4: 创建新的枚举类型...")
                conn.execute(text(
                    "CREATE TYPE platformrole AS ENUM "
                    "('super_admin', 'ops', 'support', 'auditor')"
                ))
                print("  ✓ 新枚举类型已创建")

                # 更新表使用新枚举
                print("\n步骤 5: 更新表使用新枚举类型...")
                conn.execute(text(
                    "ALTER TABLE platform_admins "
                    "ALTER COLUMN role TYPE platformrole "
                    "USING role::platformrole"
                ))
                print("  ✓ 表已更新")

                # 设置默认值
                print("\n步骤 6: 设置默认值...")
                conn.execute(text(
                    "ALTER TABLE platform_admins "
                    "ALTER COLUMN role SET DEFAULT 'support'::platformrole"
                ))
                print("  ✓ 默认值已设置")

                # 提交事务
                trans.commit()

                print("\n" + "=" * 60)
                print("✅ 修复完成！")
                print("=" * 60)
                print()

                print_usage_examples()

            except Exception as e:
                trans.rollback()
                raise e

    except SQLAlchemyError as e:
        print(f"\n❌ 数据库错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


def print_usage_examples():
    """打印使用示例"""
    print("\n📝 有效的角色值:")
    print("  • super_admin - 超级管理员(管理所有租户)")
    print("  • ops         - 运维人员(系统维护)")
    print("  • support     - 客服支持(查看权限)")
    print("  • auditor     - 审计员(只读所有日志)")
    print()
    print("💡 插入示例:")
    print("  INSERT INTO platform_admins (user_id, role)")
    print("  VALUES (1, 'super_admin');")
    print()
    print("  INSERT INTO platform_admins (user_id, role)")
    print("  VALUES (2, 'ops');")
    print()
    print("⚠️  注意:")
    print("  • 不存在 'admin' 这个角色值，请使用 'super_admin'")
    print("  • 枚举值是小写，用下划线分隔")
    print()


def check_status():
    """检查当前状态"""
    print("=" * 60)
    print("检查 platformrole 枚举状态")
    print("=" * 60)
    print()

    try:
        db_url = get_database_url()
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # 检查枚举类型是否存在
            result = conn.execute(text(
                "SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'platformrole')"
            ))
            enum_exists = result.scalar()

            if not enum_exists:
                print("❌ platformrole 枚举类型不存在")
                print("   运行修复脚本: python fix_platform_role_enum.py --fix")
                return

            # 获取枚举值
            result = conn.execute(text(
                "SELECT enumlabel FROM pg_enum WHERE enumtypid = "
                "(SELECT oid FROM pg_type WHERE typname = 'platformrole') "
                "ORDER BY enumsortorder"
            ))
            values = [row[0] for row in result]

            print("✓ platformrole 枚举类型存在")
            print(f"  枚举值: {values}")

            # 检查是否正确
            expected = ['super_admin', 'ops', 'support', 'auditor']
            if set(values) == set(expected):
                print("\n✅ 枚举配置正确！")
                print_usage_examples()
            else:
                print("\n⚠️  枚举值不匹配")
                print(f"  期望: {expected}")
                print(f"  实际: {values}")
                print("\n  运行修复脚本: python fix_platform_role_enum.py --fix")

            # 检查现有数据
            result = conn.execute(text(
                "SELECT user_id, role FROM platform_admins"
            ))
            admins = list(result)

            if admins:
                print(f"\n当前平台管理员 ({len(admins)} 个):")
                for user_id, role in admins:
                    print(f"  • user_id={user_id}, role={role}")
            else:
                print("\n📝 当前没有平台管理员")

    except SQLAlchemyError as e:
        print(f"\n❌ 数据库错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        fix_platform_role_enum()
    else:
        check_status()
        print("\n运行修复: python fix_platform_role_enum.py --fix")
