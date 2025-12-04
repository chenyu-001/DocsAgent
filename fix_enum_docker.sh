#!/bin/bash
# Docker 环境下修复 platform_admins 枚举类型

set -e  # 遇到错误立即退出

echo "========================================"
echo "修复 platform_admins 枚举类型"
echo "========================================"
echo ""

# 获取数据库配置（从 .env 或使用默认值）
DB_USER="${POSTGRES_USER:-docsagent}"
DB_NAME="${POSTGRES_DB:-docsagent}"

echo "📋 配置信息:"
echo "  数据库: $DB_NAME"
echo "  用户: $DB_USER"
echo ""

# 检查 Docker 服务是否运行
echo "🔍 检查 Docker 服务状态..."
if ! docker compose ps | grep -q "docsagent-postgres.*running"; then
    echo "❌ PostgreSQL 容器未运行"
    echo "   请先启动服务: docker compose up -d postgres"
    exit 1
fi
echo "✓ PostgreSQL 容器正在运行"
echo ""

# 执行修复 SQL
echo "🔧 执行修复脚本..."
echo ""

docker compose exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" <<'EOF'
-- ==========================================================
-- 修复 platform_admins 表的角色枚举类型
-- ==========================================================

\echo '步骤 1: 检查现有枚举类型...'

-- 检查并显示当前枚举值
DO $$
DECLARE
    enum_exists BOOLEAN;
    current_values TEXT;
BEGIN
    SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'platformrole') INTO enum_exists;

    IF enum_exists THEN
        SELECT string_agg(enumlabel, ', ' ORDER BY enumsortorder)
        INTO current_values
        FROM pg_enum
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'platformrole');

        RAISE NOTICE '  ✓ 找到现有枚举类型: %', current_values;

        -- 临时修改列类型
        RAISE NOTICE '步骤 2: 临时修改列类型...';
        ALTER TABLE platform_admins ALTER COLUMN role TYPE VARCHAR(20);
        RAISE NOTICE '  ✓ 列类型已临时修改';

        -- 删除旧枚举
        RAISE NOTICE '步骤 3: 删除旧枚举类型...';
        DROP TYPE platformrole CASCADE;
        RAISE NOTICE '  ✓ 旧枚举类型已删除';
    ELSE
        RAISE NOTICE '  ⚠ platformrole 枚举类型不存在';
    END IF;
END $$;

\echo '步骤 4: 创建新的枚举类型...'

-- 创建新枚举类型
CREATE TYPE platformrole AS ENUM ('super_admin', 'ops', 'support', 'auditor');

\echo '  ✓ 新枚举类型已创建'
\echo ''
\echo '步骤 5: 更新表使用新枚举...'

-- 更新表使用新枚举
ALTER TABLE platform_admins
    ALTER COLUMN role TYPE platformrole
    USING role::platformrole;

\echo '  ✓ 表已更新'
\echo ''
\echo '步骤 6: 设置默认值...'

-- 设置默认值
ALTER TABLE platform_admins
    ALTER COLUMN role SET DEFAULT 'support'::platformrole;

\echo '  ✓ 默认值已设置'
\echo ''

-- 添加注释
COMMENT ON TYPE platformrole IS '平台管理员角色类型: super_admin(超级管理员), ops(运维人员), support(客服支持), auditor(审计员)';
COMMENT ON COLUMN platform_admins.role IS '平台角色 - 使用 platformrole 枚举类型';

\echo '========================================'
\echo '✅ 修复完成！'
\echo '========================================'
\echo ''
\echo '📝 有效的角色值:'
\echo '  • super_admin - 超级管理员(管理所有租户)'
\echo '  • ops         - 运维人员(系统维护)'
\echo '  • support     - 客服支持(查看权限)'
\echo '  • auditor     - 审计员(只读所有日志)'
\echo ''
\echo '💡 插入示例:'
\echo '  INSERT INTO platform_admins (user_id, role) VALUES (1, '\''super_admin'\'');'
\echo '  INSERT INTO platform_admins (user_id, role) VALUES (2, '\''ops'\'');'
\echo ''
\echo '⚠️  注意:'
\echo '  • 不存在 '\''admin'\'' 这个角色值，请使用 '\''super_admin'\'''
\echo '  • 枚举值是小写，用下划线分隔'
\echo ''

EOF

echo ""
echo "✅ 修复完成！现在您可以使用正确的枚举值了"
echo ""
echo "验证修复："
echo "  docker compose exec postgres psql -U $DB_USER -d $DB_NAME -c \"\\dT+ platformrole\""
echo ""
