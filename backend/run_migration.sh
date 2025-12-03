#!/bin/bash
# 数据库迁移脚本 - Docker环境
# 使用方法:
#   在宿主机上运行: bash run_migration.sh
#   或在容器内运行: docker-compose exec backend bash /app/run_migration.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "DocsAgent 多租户数据库迁移"
echo "=========================================="

# 数据库连接信息
DB_HOST=${POSTGRES_HOST:-postgres}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-docsagent}
DB_USER=${POSTGRES_USER:-docsagent}
DB_PASSWORD=${POSTGRES_PASSWORD:-docsagent_password}

echo "连接数据库: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"

# 检查PostgreSQL是否可用
echo "检查数据库连接..."
export PGPASSWORD=$DB_PASSWORD
if ! psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ 无法连接到数据库!"
    echo "请检查数据库是否已启动: docker-compose ps"
    exit 1
fi

echo "✓ 数据库连接成功"

# 执行迁移脚本
echo ""
echo "执行迁移脚本..."
echo "=========================================="

# 002_add_multi_tenant.sql
if [ -f "/app/migrations/002_add_multi_tenant.sql" ]; then
    echo "运行: 002_add_multi_tenant.sql"
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f /app/migrations/002_add_multi_tenant.sql
    echo "✓ 迁移完成"
else
    echo "❌ 找不到迁移文件: /app/migrations/002_add_multi_tenant.sql"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 数据库迁移完成!"
echo "=========================================="
echo ""
echo "默认租户信息:"
echo "  Tenant ID: 00000000-0000-0000-0000-000000000001"
echo "  Tenant Name: Default Tenant"
echo "  Tenant Slug: default"
echo ""
echo "系统角色已创建:"
echo "  - tenant_admin (租户管理员)"
echo "  - member (普通成员)"
echo "  - guest (访客)"
echo ""
echo "所有现有用户已迁移到默认租户"
echo ""
echo "=========================================="

# 验证表创建
echo ""
echo "验证表创建..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('tenants', 'tenant_users', 'tenant_roles', 'resource_permissions', 'audit_logs')
ORDER BY table_name;
"

echo ""
echo "✅ 全部完成! 现在可以启动应用了。"
