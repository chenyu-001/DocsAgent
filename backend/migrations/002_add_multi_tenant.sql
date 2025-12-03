-- ==========================================================
-- Multi-Tenant Architecture Migration
-- Version: 002
-- Description: 添加多租户支持,包括租户管理、权限体系、审计日志
-- ==========================================================

-- ==========================================================
-- Part 1: 租户核心表
-- ==========================================================

-- 租户表
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,

    -- 部署模式
    deploy_mode VARCHAR(20) NOT NULL DEFAULT 'cloud' CHECK (deploy_mode IN ('cloud', 'hybrid', 'local')),

    -- 数据库配置
    db_connection TEXT,
    db_schema VARCHAR(100),

    -- 向量库配置
    vector_db_config JSONB,
    vector_namespace VARCHAR(100),

    -- 存储配置
    storage_config JSONB,

    -- 资源配额
    storage_quota_bytes BIGINT NOT NULL DEFAULT 10737418240,  -- 10GB
    user_quota INTEGER NOT NULL DEFAULT 10,
    document_quota INTEGER NOT NULL DEFAULT 1000,

    -- 当前使用量
    storage_used_bytes BIGINT NOT NULL DEFAULT 0,
    user_count INTEGER NOT NULL DEFAULT 0,
    document_count INTEGER NOT NULL DEFAULT 0,

    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'trial' CHECK (status IN ('active', 'suspended', 'archived', 'trial')),
    expires_at TIMESTAMP,
    trial_ends_at TIMESTAMP,

    -- License
    license_key VARCHAR(500),
    license_data JSONB,

    -- 联系信息
    contact_name VARCHAR(100),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(50),

    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMP,

    CONSTRAINT tenants_slug_format CHECK (slug ~ '^[a-z0-9-]+$')
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_deploy_mode ON tenants(deploy_mode);

COMMENT ON TABLE tenants IS '租户表';
COMMENT ON COLUMN tenants.slug IS '租户标识,用于子域名或路径';


-- 租户功能开关表
CREATE TABLE IF NOT EXISTS tenant_features (
    id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,

    feature_key VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT false,
    config JSONB,

    usage_limit INTEGER,
    usage_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, feature_key)
);

CREATE INDEX idx_tenant_features_tenant ON tenant_features(tenant_id);
CREATE INDEX idx_tenant_features_key ON tenant_features(feature_key);

COMMENT ON TABLE tenant_features IS '租户功能开关表';


-- 部门表
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    description TEXT,

    parent_id UUID,
    path VARCHAR(1000) NOT NULL,
    level INTEGER NOT NULL DEFAULT 0,

    manager_id INTEGER,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_departments_tenant ON departments(tenant_id);
CREATE INDEX idx_departments_path ON departments(path);
CREATE INDEX idx_departments_parent ON departments(parent_id);

COMMENT ON TABLE departments IS '部门表';


-- ==========================================================
-- Part 2: 权限体系
-- ==========================================================

-- 租户角色表
CREATE TABLE IF NOT EXISTS tenant_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,

    name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,

    level INTEGER NOT NULL DEFAULT 0,
    permissions INTEGER NOT NULL DEFAULT 33,  -- READER权限

    is_system BOOLEAN NOT NULL DEFAULT false,
    is_default BOOLEAN NOT NULL DEFAULT false,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_tenant_roles_tenant ON tenant_roles(tenant_id);
CREATE INDEX idx_tenant_roles_level ON tenant_roles(level);

COMMENT ON TABLE tenant_roles IS '租户角色表';
COMMENT ON COLUMN tenant_roles.permissions IS '权限位(位运算)';


-- 租户用户关联表
CREATE TABLE IF NOT EXISTS tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    role_id UUID REFERENCES tenant_roles(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled', 'invited')),

    invited_by INTEGER,
    invited_at TIMESTAMP,
    joined_at TIMESTAMP NOT NULL DEFAULT NOW(),

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMP,

    UNIQUE(tenant_id, user_id)
);

CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_user ON tenant_users(user_id);
CREATE INDEX idx_tenant_users_role ON tenant_users(role_id);
CREATE INDEX idx_tenant_users_dept ON tenant_users(department_id);

COMMENT ON TABLE tenant_users IS '租户用户关联表';


-- 资源权限表
CREATE TABLE IF NOT EXISTS resource_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,

    resource_type VARCHAR(50) NOT NULL CHECK (resource_type IN ('workspace', 'folder', 'document')),
    resource_id VARCHAR(100) NOT NULL,

    grantee_type VARCHAR(50) NOT NULL CHECK (grantee_type IN ('user', 'role', 'department')),
    grantee_id VARCHAR(100) NOT NULL,

    permission INTEGER NOT NULL DEFAULT 33,  -- READER权限
    inherit BOOLEAN NOT NULL DEFAULT true,

    granted_by INTEGER,
    granted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, resource_type, resource_id, grantee_type, grantee_id)
);

CREATE INDEX idx_resource_permissions_tenant ON resource_permissions(tenant_id);
CREATE INDEX idx_resource_permissions_resource ON resource_permissions(tenant_id, resource_type, resource_id);
CREATE INDEX idx_resource_permissions_grantee ON resource_permissions(tenant_id, grantee_type, grantee_id);

COMMENT ON TABLE resource_permissions IS '资源权限表';
COMMENT ON COLUMN resource_permissions.permission IS '权限位(位运算)';


-- 平台角色枚举类型
CREATE TYPE platformrole AS ENUM ('super_admin', 'ops', 'support', 'auditor');

COMMENT ON TYPE platformrole IS '平台管理员角色类型';

-- 平台管理员表
CREATE TABLE IF NOT EXISTS platform_admins (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    role platformrole NOT NULL DEFAULT 'support',

    scope TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP
);

CREATE INDEX idx_platform_admins_role ON platform_admins(role);

COMMENT ON TABLE platform_admins IS '平台管理员表';
COMMENT ON COLUMN platform_admins.role IS '平台角色: super_admin(超级管理员), ops(运维), support(支持), auditor(审计)';


-- ==========================================================
-- Part 3: 审计日志
-- ==========================================================

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,

    action VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL DEFAULT 'info' CHECK (level IN ('info', 'warning', 'critical', 'security')),

    user_id INTEGER,
    username VARCHAR(50),
    user_role VARCHAR(50),

    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    resource_name VARCHAR(255),

    details JSONB,
    changes JSONB,

    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    request_id VARCHAR(100),

    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    error_code VARCHAR(50),

    duration_ms INTEGER,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_tenant_action ON audit_logs(tenant_id, action);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_time ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_level_time ON audit_logs(level, created_at);

COMMENT ON TABLE audit_logs IS '审计日志表';


-- 登录历史表
CREATE TABLE IF NOT EXISTS login_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL,
    tenant_id UUID,

    username VARCHAR(50) NOT NULL,
    login_type VARCHAR(20) NOT NULL DEFAULT 'password',

    success BOOLEAN NOT NULL DEFAULT true,
    failure_reason VARCHAR(255),

    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    location VARCHAR(255),

    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    logout_at TIMESTAMP,
    session_duration INTEGER
);

CREATE INDEX idx_login_history_user ON login_history(user_id);
CREATE INDEX idx_login_history_tenant ON login_history(tenant_id);
CREATE INDEX idx_login_history_user_time ON login_history(user_id, created_at);
CREATE INDEX idx_login_history_tenant_time ON login_history(tenant_id, created_at);
CREATE INDEX idx_login_history_ip ON login_history(ip_address, created_at);

COMMENT ON TABLE login_history IS '登录历史表';


-- ==========================================================
-- Part 4: 更新现有表以支持多租户
-- ==========================================================

-- 为users表添加默认租户关联(兼容旧数据)
-- 注意: 不强制要求tenant_id,保持向后兼容
ALTER TABLE users ADD COLUMN IF NOT EXISTS default_tenant_id UUID;
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(default_tenant_id);

-- 为documents表添加租户ID(新文档必须关联租户)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS tenant_id UUID;
CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant_id);

-- 为folders表添加租户ID
ALTER TABLE folders ADD COLUMN IF NOT EXISTS tenant_id UUID;
CREATE INDEX IF NOT EXISTS idx_folders_tenant ON folders(tenant_id);

-- 为acls表添加租户ID
ALTER TABLE acls ADD COLUMN IF NOT EXISTS tenant_id UUID;
CREATE INDEX IF NOT EXISTS idx_acls_tenant ON acls(tenant_id);


-- ==========================================================
-- Part 5: 初始化默认数据
-- ==========================================================

-- 创建默认租户(用于兼容旧数据)
INSERT INTO tenants (id, name, slug, description, deploy_mode, status)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Default Tenant',
    'default',
    'Default tenant for legacy data',
    'cloud',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- 为默认租户创建系统角色
DO $$
DECLARE
    default_tenant_id UUID := '00000000-0000-0000-0000-000000000001';
    admin_role_id UUID := gen_random_uuid();
    member_role_id UUID := gen_random_uuid();
    guest_role_id UUID := gen_random_uuid();
BEGIN
    -- 租户管理员角色
    INSERT INTO tenant_roles (id, tenant_id, name, display_name, description, level, permissions, is_system, is_default)
    VALUES (
        admin_role_id,
        default_tenant_id,
        'tenant_admin',
        '租户管理员',
        '拥有租户内所有权限',
        100,
        255,  -- OWNER权限
        true,
        false
    ) ON CONFLICT DO NOTHING;

    -- 普通成员角色(默认角色)
    INSERT INTO tenant_roles (id, tenant_id, name, display_name, description, level, permissions, is_system, is_default)
    VALUES (
        member_role_id,
        default_tenant_id,
        'member',
        '成员',
        '普通成员,可以创建和编辑自己的文档',
        10,
        67,  -- EDITOR权限
        true,
        true
    ) ON CONFLICT DO NOTHING;

    -- 访客角色
    INSERT INTO tenant_roles (id, tenant_id, name, display_name, description, level, permissions, is_system, is_default)
    VALUES (
        guest_role_id,
        default_tenant_id,
        'guest',
        '访客',
        '只读访问权限',
        1,
        33,  -- READER权限
        true,
        false
    ) ON CONFLICT DO NOTHING;
END $$;

-- 将现有用户关联到默认租户
DO $$
DECLARE
    default_tenant_id UUID := '00000000-0000-0000-0000-000000000001';
    default_role_id UUID;
    user_record RECORD;
BEGIN
    -- 获取默认角色ID
    SELECT id INTO default_role_id FROM tenant_roles
    WHERE tenant_id = default_tenant_id AND is_default = true LIMIT 1;

    -- 为所有现有用户创建租户关联
    FOR user_record IN SELECT id FROM users LOOP
        INSERT INTO tenant_users (tenant_id, user_id, role_id, status)
        VALUES (default_tenant_id, user_record.id, default_role_id, 'active')
        ON CONFLICT (tenant_id, user_id) DO NOTHING;
    END LOOP;

    -- 更新租户用户计数
    UPDATE tenants SET user_count = (SELECT COUNT(*) FROM tenant_users WHERE tenant_id = default_tenant_id)
    WHERE id = default_tenant_id;
END $$;

-- 将现有文档关联到默认租户
UPDATE documents SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE folders SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;
UPDATE acls SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL;

-- 更新租户文档计数
UPDATE tenants SET document_count = (SELECT COUNT(*) FROM documents WHERE tenant_id = '00000000-0000-0000-0000-000000000001')
WHERE id = '00000000-0000-0000-0000-000000000001';


-- ==========================================================
-- Part 6: 触发器和函数
-- ==========================================================

-- 自动更新 updated_at 字段的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为各表添加 updated_at 触发器
DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants;
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tenant_features_updated_at ON tenant_features;
CREATE TRIGGER update_tenant_features_updated_at BEFORE UPDATE ON tenant_features
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_departments_updated_at ON departments;
CREATE TRIGGER update_departments_updated_at BEFORE UPDATE ON departments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tenant_roles_updated_at ON tenant_roles;
CREATE TRIGGER update_tenant_roles_updated_at BEFORE UPDATE ON tenant_roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tenant_users_updated_at ON tenant_users;
CREATE TRIGGER update_tenant_users_updated_at BEFORE UPDATE ON tenant_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_resource_permissions_updated_at ON resource_permissions;
CREATE TRIGGER update_resource_permissions_updated_at BEFORE UPDATE ON resource_permissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_platform_admins_updated_at ON platform_admins;
CREATE TRIGGER update_platform_admins_updated_at BEFORE UPDATE ON platform_admins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- 自动更新租户统计信息的触发器
CREATE OR REPLACE FUNCTION update_tenant_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'tenant_users' THEN
        IF TG_OP = 'INSERT' THEN
            UPDATE tenants SET user_count = user_count + 1 WHERE id = NEW.tenant_id;
        ELSIF TG_OP = 'DELETE' THEN
            UPDATE tenants SET user_count = GREATEST(user_count - 1, 0) WHERE id = OLD.tenant_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'documents' THEN
        IF TG_OP = 'INSERT' THEN
            UPDATE tenants SET
                document_count = document_count + 1,
                storage_used_bytes = storage_used_bytes + NEW.file_size
            WHERE id = NEW.tenant_id;
        ELSIF TG_OP = 'DELETE' THEN
            UPDATE tenants SET
                document_count = GREATEST(document_count - 1, 0),
                storage_used_bytes = GREATEST(storage_used_bytes - OLD.file_size, 0)
            WHERE id = OLD.tenant_id;
        ELSIF TG_OP = 'UPDATE' AND NEW.file_size != OLD.file_size THEN
            UPDATE tenants SET
                storage_used_bytes = storage_used_bytes + (NEW.file_size - OLD.file_size)
            WHERE id = NEW.tenant_id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- 应用触发器
DROP TRIGGER IF EXISTS tenant_users_stats_trigger ON tenant_users;
CREATE TRIGGER tenant_users_stats_trigger AFTER INSERT OR DELETE ON tenant_users
    FOR EACH ROW EXECUTE FUNCTION update_tenant_stats();

DROP TRIGGER IF EXISTS documents_stats_trigger ON documents;
CREATE TRIGGER documents_stats_trigger AFTER INSERT OR DELETE OR UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_tenant_stats();


-- ==========================================================
-- 迁移完成
-- ==========================================================

COMMENT ON SCHEMA public IS 'Multi-tenant architecture migration v002 completed';
