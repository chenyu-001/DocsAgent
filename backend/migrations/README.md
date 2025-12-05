# Database Migrations

## 迁移文件列表

- `001_add_folders.sql` - 添加文件夹功能
- `002_add_multi_tenant.sql` - 添加多租户支持
- `003_fix_platform_role_enum.sql` - 修复平台角色枚举
- `004_add_document_summary.sql` - 添加文档摘要字段 ⭐ **NEW**

## 使用 Docker 执行迁移

### 方法 1：使用 docker exec 直接执行（推荐）

```bash
# 1. 确保 Docker 容器正在运行
docker-compose up -d postgres

# 2. 执行迁移（按顺序执行所有迁移文件）
docker exec -i docsagent-postgres psql -U docsagent -d docsagent < backend/migrations/001_add_folders.sql
docker exec -i docsagent-postgres psql -U docsagent -d docsagent < backend/migrations/002_add_multi_tenant.sql
docker exec -i docsagent-postgres psql -U docsagent -d docsagent < backend/migrations/003_fix_platform_role_enum.sql
docker exec -i docsagent-postgres psql -U docsagent -d docsagent < backend/migrations/004_add_document_summary.sql
```

### 方法 2：仅执行最新迁移

如果之前的迁移已经执行过，只需执行最新的：

```bash
docker exec -i docsagent-postgres psql -U docsagent -d docsagent < backend/migrations/004_add_document_summary.sql
```

### 方法 3：进入容器内部执行

```bash
# 1. 进入 Postgres 容器
docker exec -it docsagent-postgres bash

# 2. 连接到数据库
psql -U docsagent -d docsagent

# 3. 在 psql 中执行 SQL
\i /path/to/migration.sql

# 4. 或者直接粘贴 SQL 内容
ALTER TABLE documents ADD COLUMN IF NOT EXISTS summary TEXT;
COMMENT ON COLUMN documents.summary IS 'AI-generated document summary';

# 5. 退出
\q
exit
```

## 验证迁移是否成功

```bash
# 查看 documents 表结构
docker exec -it docsagent-postgres psql -U docsagent -d docsagent -c "\d documents"

# 应该能看到 summary 字段：
# summary | text | | |
```

## 回滚（如果需要）

```bash
# 删除 summary 列
docker exec -it docsagent-postgres psql -U docsagent -d docsagent -c "ALTER TABLE documents DROP COLUMN IF EXISTS summary;"
```

## 环境变量说明

默认配置（来自 docker-compose.yml）：
- 数据库名：`docsagent`
- 用户名：`docsagent`
- 密码：`docsagent_password`
- 容器名：`docsagent-postgres`

如果你使用了自定义配置，请相应修改命令中的参数。
