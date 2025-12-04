#!/bin/bash
# Docker 环境下检查 platform_admins 枚举类型状态

set -e

echo "========================================"
echo "检查 platformrole 枚举状态"
echo "========================================"
echo ""

# 获取数据库配置
DB_USER="${POSTGRES_USER:-docsagent}"
DB_NAME="${POSTGRES_DB:-docsagent}"

# 检查 Docker 服务
if ! docker compose ps | grep -q "docsagent-postgres.*running"; then
    echo "❌ PostgreSQL 容器未运行"
    echo "   请先启动: docker compose up -d postgres"
    exit 1
fi

echo "🔍 检查枚举类型..."
echo ""

docker compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" <<'EOF'
-- 检查枚举类型是否存在
DO $$
DECLARE
    enum_exists BOOLEAN;
    enum_values TEXT;
BEGIN
    SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'platformrole') INTO enum_exists;

    IF NOT enum_exists THEN
        RAISE NOTICE '❌ platformrole 枚举类型不存在';
        RAISE NOTICE '   运行修复脚本: ./fix_enum_docker.sh';
    ELSE
        -- 获取枚举值
        SELECT string_agg(enumlabel, ', ' ORDER BY enumsortorder)
        INTO enum_values
        FROM pg_enum
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'platformrole');

        RAISE NOTICE '✓ platformrole 枚举类型存在';
        RAISE NOTICE '  枚举值: %', enum_values;

        -- 检查是否正确
        IF enum_values = 'super_admin, ops, support, auditor' THEN
            RAISE NOTICE '';
            RAISE NOTICE '✅ 枚举配置正确！';
        ELSE
            RAISE NOTICE '';
            RAISE NOTICE '⚠️  枚举值可能不匹配';
            RAISE NOTICE '  期望: super_admin, ops, support, auditor';
            RAISE NOTICE '  运行修复: ./fix_enum_docker.sh';
        END IF;
    END IF;
END $$;

\echo ''
\echo '当前平台管理员:'

-- 查看现有管理员
SELECT
    CASE
        WHEN COUNT(*) = 0 THEN '  📝 当前没有平台管理员'
        ELSE ''
    END
FROM platform_admins;

SELECT
    '  • user_id=' || user_id || ', role=' || role AS admin_info
FROM platform_admins
ORDER BY user_id;

\echo ''
\echo '📝 有效的角色值:'
\echo '  • super_admin - 超级管理员'
\echo '  • ops         - 运维人员'
\echo '  • support     - 客服支持'
\echo '  • auditor     - 审计员'

EOF

echo ""
