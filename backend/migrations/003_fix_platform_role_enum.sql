-- ==========================================================
-- Fix Platform Role Enum
-- Version: 003
-- Description: 修复 platform_admins 表的角色枚举类型
-- ==========================================================

-- Step 1: 检查并删除现有的枚举类型(如果存在)
DO $$
BEGIN
    -- 如果表使用了枚举类型,先将列改为 VARCHAR
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'platformrole') THEN
        -- 临时修改列类型为 VARCHAR
        ALTER TABLE platform_admins ALTER COLUMN role TYPE VARCHAR(20);

        -- 删除旧的枚举类型
        DROP TYPE IF EXISTS platformrole CASCADE;
    END IF;
END $$;

-- Step 2: 创建新的枚举类型
CREATE TYPE platformrole AS ENUM ('super_admin', 'ops', 'support', 'auditor');

-- Step 3: 更新表使用新的枚举类型
ALTER TABLE platform_admins
    ALTER COLUMN role TYPE platformrole
    USING role::platformrole;

-- Step 4: 设置默认值
ALTER TABLE platform_admins
    ALTER COLUMN role SET DEFAULT 'support'::platformrole;

-- Step 5: 添加注释
COMMENT ON TYPE platformrole IS '平台管理员角色类型: super_admin(超级管理员), ops(运维人员), support(客服支持), auditor(审计员)';
COMMENT ON COLUMN platform_admins.role IS '平台角色 - 使用 platformrole 枚举类型';

-- 显示结果
\echo '✓ platformrole 枚举类型已创建/更新'
\echo '✓ 有效的角色值: super_admin, ops, support, auditor'
\echo ''
\echo '示例插入命令:'
\echo "  INSERT INTO platform_admins (user_id, role) VALUES (1, 'super_admin');"
\echo "  INSERT INTO platform_admins (user_id, role) VALUES (2, 'ops');"
\echo "  INSERT INTO platform_admins (user_id, role) VALUES (3, 'support');"
\echo "  INSERT INTO platform_admins (user_id, role) VALUES (4, 'auditor');"
