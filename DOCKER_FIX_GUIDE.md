# Docker 环境修复指南

## 🐳 Docker 环境下修复 platformrole 枚举错误

如果您在使用 Docker 时遇到枚举类型错误，按照以下步骤修复：

```
ERROR: invalid input value for enum platformrole: 'super_admin'
ERROR: invalid input value for enum platformrole: 'admin'
```

## ⚡ 快速修复（推荐）

### 1. 检查当前状态

```bash
./check_enum_docker.sh
```

### 2. 执行修复

```bash
./fix_enum_docker.sh
```

就这么简单！修复脚本会自动：
- ✅ 检查 PostgreSQL 容器是否运行
- ✅ 重建正确的枚举类型
- ✅ 更新表结构
- ✅ 显示修复结果

## 📋 有效的角色值

| 枚举值 | 说明 |
|--------|------|
| `super_admin` | 超级管理员 ⚠️ **不是 `admin`** |
| `ops` | 运维人员 |
| `support` | 客服支持 |
| `auditor` | 审计员 |

## 💡 正确的插入示例

修复后，使用以下方式插入数据：

### 方法 1: 直接使用 psql

```bash
docker compose exec postgres psql -U docsagent -d docsagent -c \
  "INSERT INTO platform_admins (user_id, role) VALUES (1, 'super_admin');"
```

### 方法 2: 进入数据库交互模式

```bash
# 进入 psql
docker compose exec postgres psql -U docsagent -d docsagent

# 然后执行 SQL
INSERT INTO platform_admins (user_id, role) VALUES (1, 'super_admin');
INSERT INTO platform_admins (user_id, role) VALUES (2, 'ops');
INSERT INTO platform_admins (user_id, role) VALUES (3, 'support');
INSERT INTO platform_admins (user_id, role) VALUES (4, 'auditor');
```

### 方法 3: 通过应用程序 API

修复后，重启后端服务：

```bash
docker compose restart backend
```

然后使用 Python 代码：

```python
from backend.models.tenant_permission_models import PlatformAdmin, PlatformRole
from api.db import get_db

admin = PlatformAdmin(
    user_id=1,
    role=PlatformRole.SUPER_ADMIN  # 使用枚举
)
db.add(admin)
db.commit()
```

## 🔍 验证修复

### 查看枚举类型定义

```bash
docker compose exec postgres psql -U docsagent -d docsagent -c "\dT+ platformrole"
```

### 查看表结构

```bash
docker compose exec postgres psql -U docsagent -d docsagent -c "\d platform_admins"
```

### 查看现有管理员

```bash
docker compose exec postgres psql -U docsagent -d docsagent -c \
  "SELECT user_id, role FROM platform_admins;"
```

## ❌ 常见错误

### 错误 1: 使用了不存在的 'admin'

```sql
-- ❌ 错误
INSERT INTO platform_admins (user_id, role) VALUES (1, 'admin');

-- ✅ 正确
INSERT INTO platform_admins (user_id, role) VALUES (1, 'super_admin');
```

### 错误 2: 大小写错误

```sql
-- ❌ 错误
INSERT INTO platform_admins (user_id, role) VALUES (1, 'SUPER_ADMIN');
INSERT INTO platform_admins (user_id, role) VALUES (1, 'Super_Admin');

-- ✅ 正确（小写，下划线分隔）
INSERT INTO platform_admins (user_id, role) VALUES (1, 'super_admin');
```

## 🛠️ 手动修复（高级）

如果脚本无法运行，可以手动执行：

```bash
docker compose exec postgres psql -U docsagent -d docsagent
```

然后在 psql 中执行：

```sql
-- 检查现有枚举
\dT+ platformrole

-- 临时修改为 VARCHAR
ALTER TABLE platform_admins ALTER COLUMN role TYPE VARCHAR(20);

-- 删除旧枚举
DROP TYPE IF EXISTS platformrole CASCADE;

-- 创建新枚举
CREATE TYPE platformrole AS ENUM ('super_admin', 'ops', 'support', 'auditor');

-- 更新表使用新枚举
ALTER TABLE platform_admins
    ALTER COLUMN role TYPE platformrole
    USING role::platformrole;

-- 设置默认值
ALTER TABLE platform_admins
    ALTER COLUMN role SET DEFAULT 'support'::platformrole;
```

## 🚀 启动和重启服务

### 启动所有服务

```bash
docker compose up -d
```

### 只启动数据库

```bash
docker compose up -d postgres
```

### 重启后端服务

```bash
docker compose restart backend
```

### 查看服务状态

```bash
docker compose ps
```

### 查看日志

```bash
# 查看所有日志
docker compose logs

# 查看后端日志
docker compose logs backend

# 查看数据库日志
docker compose logs postgres

# 实时跟踪日志
docker compose logs -f backend
```

## 📁 相关文件

- `fix_enum_docker.sh` - Docker 环境修复脚本
- `check_enum_docker.sh` - Docker 环境检查脚本
- `backend/migrations/003_fix_platform_role_enum.sql` - SQL 修复脚本
- `PLATFORM_ADMIN_FIX.md` - 完整修复指南
- `docker-compose.yml` - Docker 配置文件

## 💬 需要帮助？

### 问题：容器没有运行

```bash
# 启动容器
docker compose up -d postgres

# 检查状态
docker compose ps
```

### 问题：权限错误

```bash
# 给脚本添加执行权限
chmod +x fix_enum_docker.sh check_enum_docker.sh
```

### 问题：数据库连接失败

```bash
# 检查容器健康状态
docker compose ps

# 查看数据库日志
docker compose logs postgres

# 重启数据库
docker compose restart postgres
```

### 问题：修复后仍然报错

1. 重启后端服务：
   ```bash
   docker compose restart backend
   ```

2. 检查枚举是否正确创建：
   ```bash
   ./check_enum_docker.sh
   ```

3. 查看后端日志：
   ```bash
   docker compose logs backend
   ```

## ✅ 完成后

修复完成后，您就可以正常使用了：

```sql
-- ✅ 插入超级管理员
INSERT INTO platform_admins (user_id, role) VALUES (1, 'super_admin');

-- ✅ 插入运维人员
INSERT INTO platform_admins (user_id, role) VALUES (2, 'ops');

-- ✅ 插入客服支持
INSERT INTO platform_admins (user_id, role) VALUES (3, 'support');

-- ✅ 插入审计员
INSERT INTO platform_admins (user_id, role) VALUES (4, 'auditor');
```

记住：**没有 `admin` 这个角色，请使用 `super_admin`！**
