# Platform Admin 枚举类型错误修复指南

## 问题描述

在尝试向 `platform_admins` 表插入数据时，出现以下错误：

```
ERROR: invalid input value for enum platformrole: 'super_admin'
ERROR: invalid input value for enum platformrole: 'admin'
```

## 问题原因

1. **枚举值不匹配**：PostgreSQL 的 `platformrole` 枚举类型可能没有正确创建或值不匹配
2. **错误的角色值**：代码中**不存在 `'admin'` 这个角色**，只有 `'super_admin'`

## 有效的角色值

根据 `backend/models/tenant_permission_models.py` 的定义，有效的平台角色包括：

| 枚举值 | 说明 | 权限范围 |
|--------|------|----------|
| `super_admin` | 超级管理员 | 管理所有租户 |
| `ops` | 运维人员 | 系统维护 |
| `support` | 客服支持 | 查看权限 |
| `auditor` | 审计员 | 只读所有日志 |

⚠️ **注意：没有 `admin` 这个值！请使用 `super_admin`**

## 修复方法

### 方法 1: 使用 Python 修复脚本 (推荐)

1. **检查当前状态**：
   ```bash
   python fix_platform_role_enum.py
   ```

2. **执行修复**：
   ```bash
   python fix_platform_role_enum.py --fix
   ```

   该脚本会：
   - 检查现有枚举类型
   - 如果类型不正确，会重建枚举类型
   - 更新表结构
   - 显示修复结果和使用示例

### 方法 2: 使用 SQL 脚本

1. **连接到数据库**：
   ```bash
   psql -U docsagent -d docsagent
   ```

2. **执行修复脚本**：
   ```bash
   \i backend/migrations/003_fix_platform_role_enum.sql
   ```

### 方法 3: 手动 SQL 命令

```sql
-- 1. 检查现有枚举类型
SELECT enumlabel FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'platformrole')
ORDER BY enumsortorder;

-- 2. 如果需要重建枚举类型
BEGIN;

-- 临时修改列类型
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

COMMIT;
```

## 正确的插入示例

修复后，使用以下命令插入数据：

```sql
-- 插入超级管理员 (注意是 super_admin，不是 admin)
INSERT INTO platform_admins (user_id, role)
VALUES (1, 'super_admin');

-- 插入运维人员
INSERT INTO platform_admins (user_id, role)
VALUES (2, 'ops');

-- 插入客服支持
INSERT INTO platform_admins (user_id, role)
VALUES (3, 'support');

-- 插入审计员
INSERT INTO platform_admins (user_id, role)
VALUES (4, 'auditor');
```

## 使用 Python 代码插入

```python
from backend.models.tenant_permission_models import PlatformAdmin, PlatformRole
from api.db import get_db

# 创建超级管理员
admin = PlatformAdmin(
    user_id=1,
    role=PlatformRole.SUPER_ADMIN  # 使用枚举类型
)

db = next(get_db())
db.add(admin)
db.commit()
```

## 验证修复

执行以下 SQL 验证修复是否成功：

```sql
-- 查看枚举类型定义
\dT+ platformrole

-- 查看表结构
\d platform_admins

-- 查看现有管理员
SELECT user_id, role FROM platform_admins;
```

## 常见错误

### ❌ 错误示例

```sql
-- 错误：使用了不存在的 'admin' 值
INSERT INTO platform_admins (user_id, role) VALUES (1, 'admin');
-- ERROR: invalid input value for enum platformrole: 'admin'

-- 错误：大小写不对
INSERT INTO platform_admins (user_id, role) VALUES (1, 'SUPER_ADMIN');
-- ERROR: invalid input value for enum platformrole: 'SUPER_ADMIN'

-- 错误：使用了大写
INSERT INTO platform_admins (user_id, role) VALUES (1, 'Super_Admin');
-- ERROR: invalid input value for enum platformrole: 'Super_Admin'
```

### ✅ 正确示例

```sql
-- 正确：使用小写，下划线分隔
INSERT INTO platform_admins (user_id, role) VALUES (1, 'super_admin');

-- 正确：使用其他有效值
INSERT INTO platform_admins (user_id, role) VALUES (2, 'ops');
INSERT INTO platform_admins (user_id, role) VALUES (3, 'support');
INSERT INTO platform_admins (user_id, role) VALUES (4, 'auditor');
```

## 相关文件

- `backend/models/tenant_permission_models.py` - Python 模型定义
- `backend/migrations/002_add_multi_tenant.sql` - 原始迁移脚本（已更新）
- `backend/migrations/003_fix_platform_role_enum.sql` - 修复脚本
- `fix_platform_role_enum.py` - Python 修复工具

## 技术细节

### 为什么会出现这个问题？

1. **初始迁移问题**：原始的 `002_add_multi_tenant.sql` 使用了 `CHECK` 约束而不是真正的 `ENUM` 类型
2. **SQLAlchemy 行为**：SQLAlchemy 的 `Enum()` 列类型会在 PostgreSQL 中创建 `ENUM` 类型
3. **类型不一致**：如果数据库是通过 SQLAlchemy 创建的，但 `ENUM` 类型创建失败或值不正确，就会出现此错误

### 修复后的改进

- ✅ 迁移脚本现在正确创建 `platformrole` 枚举类型
- ✅ 与 SQLAlchemy 模型定义完全一致
- ✅ 提供了修复工具和详细文档
- ✅ 添加了更多的注释和说明

## 需要帮助？

如果修复后仍有问题，请检查：

1. 数据库连接是否正常
2. 是否有足够的权限执行 DDL 操作
3. 是否有其他应用程序正在使用该表
4. PostgreSQL 版本是否支持 ENUM 类型（9.1+）

可以运行以下命令获取更多诊断信息：

```bash
python fix_platform_role_enum.py  # 不带 --fix 参数，只检查状态
```
