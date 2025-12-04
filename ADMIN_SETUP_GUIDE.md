# 🔐 Admin和运维账号权限设置指南

## 📖 问题说明

你遇到的问题是：系统有**两套权限体系**没有整合

### 旧系统（User.role）
```python
User.role = ADMIN | USER | GUEST  # 老的设计，已被新系统取代
```

### 新系统（多租户权限）
```python
# 三层权限体系：
1. PlatformAdmin（平台管理员）- 跨租户管理
2. TenantUser + TenantRole（租户内权限）- 业务功能
3. ResourcePermission（资源级权限）- 细粒度控制
```

### 当前问题
- ❌ **admin账号**：只有 `User.role=ADMIN`，**没有**多租户权限
- ❌ **运维账号**：只有 `PlatformAdmin.role=OPS`，**没有**租户权限，无法使用业务功能

---

## ✅ 解决方案：双重权限设计

### 设计原则
**超级管理员和运维人员应该拥有两种权限：**

1. **平台级权限**（PlatformAdmin）
   - 用于管理租户、系统配置
   - 跨租户访问数据

2. **租户级权限**（TenantUser + TenantRole）
   - 用于使用业务功能（上传文档、问答等）
   - 在特定租户内工作

---

## 🔧 修复步骤

### 方法1：使用修复脚本（推荐）

#### 1. 检查当前权限
```bash
# 在Docker容器中运行
docker-compose exec backend python /app/fix_admin_permissions.py --check --username admin

# 或在本地运行（如果已安装依赖）
cd /home/user/DocsAgent
python fix_admin_permissions.py --check --username admin
```

#### 2. 修复admin用户
```bash
# 这会：
# - 将admin设置为 PlatformAdmin.SUPER_ADMIN
# - 将admin加入默认租户并设置为 tenant_admin
docker-compose exec backend python /app/fix_admin_permissions.py --fix --username admin
```

#### 3. 创建运维账号（可选）
```bash
# 创建ops用户，拥有平台运维权限 + 租户普通成员权限
docker-compose exec backend python /app/fix_admin_permissions.py --create-ops

# 自定义运维账号
docker-compose exec backend python /app/fix_admin_permissions.py --create-ops \
  --ops-username ops2 \
  --ops-email ops2@company.com \
  --ops-password mypassword123
```

---

### 方法2：手动SQL修复

如果脚本不可用，可以手动执行SQL：

```bash
# 连接数据库
docker-compose exec postgres psql -U docsagent -d docsagent
```

```sql
-- 1. 查看admin用户信息
SELECT id, username, email, role FROM users WHERE username = 'admin';
-- 假设admin的user_id是1

-- 2. 将admin设置为平台超级管理员
INSERT INTO platform_admins (user_id, role, created_at, updated_at)
VALUES (1, 'super_admin', NOW(), NOW())
ON CONFLICT (user_id) DO UPDATE SET role = 'super_admin';

-- 3. 查找默认租户的tenant_admin角色
SELECT id, name FROM tenant_roles
WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
  AND name = 'tenant_admin';
-- 假设role_id是 'xxx-xxx-xxx'

-- 4. 将admin加入默认租户并设置为租户管理员
INSERT INTO tenant_users (id, tenant_id, user_id, role_id, status, joined_at, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  '00000000-0000-0000-0000-000000000001',
  1,
  'xxx-xxx-xxx',  -- 替换为上面查询到的role_id
  'active',
  NOW(),
  NOW(),
  NOW()
)
ON CONFLICT (tenant_id, user_id) DO UPDATE
SET role_id = 'xxx-xxx-xxx', status = 'active';

-- 5. 验证
SELECT
  u.username,
  pa.role as platform_role,
  tu.status as tenant_status,
  tr.name as tenant_role
FROM users u
LEFT JOIN platform_admins pa ON u.id = pa.user_id
LEFT JOIN tenant_users tu ON u.id = tu.user_id
LEFT JOIN tenant_roles tr ON tu.role_id = tr.id
WHERE u.username = 'admin';
```

---

## 📋 权限说明

### 超级管理员（SUPER_ADMIN）
修复后，admin账号拥有：

#### ✅ 平台级权限
- 管理所有租户
- 创建/删除/修改租户
- 查看所有租户数据
- 系统配置管理

#### ✅ 租户级权限（在默认租户）
- 上传文档
- 问答功能
- 创建文件夹
- 管理租户用户
- 配置租户权限

### 运维人员（OPS）
创建的ops账号拥有：

#### ✅ 平台级权限
- 系统维护
- 查看系统状态
- 有限的租户管理

#### ✅ 租户级权限（在默认租户，普通成员）
- 上传文档
- 问答功能
- 创建文件夹
- **不能**管理租户用户

---

## 🎯 使用示例

### 1. admin登录后

```bash
# 获取token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

export TOKEN="your_token_here"
```

#### 平台管理功能
```bash
# 列出所有租户
curl -X GET "http://localhost:8000/api/tenants/" \
  -H "Authorization: Bearer $TOKEN"

# 创建新租户
curl -X POST "http://localhost:8000/api/tenants/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新公司",
    "slug": "new-company",
    "deploy_mode": "cloud"
  }'
```

#### 业务功能（需要指定租户）
```bash
# 上传文档（在默认租户）
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -F "file=@document.pdf"

# 问答
curl -X POST "http://localhost:8000/api/qa/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是AI？"}'
```

### 2. ops运维账号登录后

```bash
# 登录
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "ops", "password": "ops123"}'

export OPS_TOKEN="ops_token_here"

# 可以使用业务功能
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer $OPS_TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -F "file=@test.pdf"

# 可以查看租户（但不能修改）
curl -X GET "http://localhost:8000/api/tenants/" \
  -H "Authorization: Bearer $OPS_TOKEN"
```

---

## 🔍 验证修复

### 检查admin权限
```bash
docker-compose exec backend python /app/fix_admin_permissions.py --check --username admin
```

应该看到：
```
✅ 是平台管理员
   角色: super_admin

✅ 租户归属:
   - 租户: Default Tenant (00000000-0000-0000-0000-000000000001)
     角色: 租户管理员 (tenant_admin)
     状态: active
```

### 前端测试
1. 用 `admin` / `admin123` 登录
2. 应该能看到：
   - **平台管理菜单**（管理租户）
   - **业务功能菜单**（上传文档、问答）
3. 两个功能都应该能正常使用

---

## 💡 设计建议

### 角色设计清单

| 角色类型 | PlatformAdmin | TenantUser | 用途 |
|---------|--------------|-----------|------|
| **超级管理员** | SUPER_ADMIN | tenant_admin (在默认租户) | 管理系统 + 使用功能 |
| **运维人员** | OPS | member (在默认租户) | 系统维护 + 测试功能 |
| **客服** | SUPPORT | guest (在任意租户) | 查看数据 + 协助用户 |
| **审计员** | AUDITOR | 无 | 只查看日志 |
| **租户管理员** | 无 | tenant_admin (在自己租户) | 管理企业内部 |
| **普通用户** | 无 | member/guest (在租户) | 使用业务功能 |

### 最佳实践
1. ✅ **超级管理员和运维都应该有租户权限**，这样他们可以测试和使用业务功能
2. ✅ **平台管理员默认有所有权限**（在 `permission_checker.py:66` 已实现）
3. ✅ **租户管理员只能管理自己的租户**
4. ✅ **审计员只能查看，不能修改**
5. ⚠️ **生产环境建议分离账号**：一个用于管理，一个用于日常使用

---

## 🐛 故障排除

### 问题1：admin登录后还是看不到管理功能
**原因**：前端可能没有检测到平台管理员权限

**解决**：
1. 检查前端代码是否读取了 `platform_admin` 信息
2. 确认API返回的用户信息包含平台角色

### 问题2：admin不能上传文档
**原因**：没有租户上下文

**解决**：
1. 确保请求头包含 `X-Tenant-ID`
2. 确认admin在该租户中

### 问题3：运维账号403错误
**原因**：权限检查失败

**解决**：
```bash
# 检查权限
docker-compose exec backend python /app/fix_admin_permissions.py --check --username ops

# 如果没有租户权限，修复：
docker-compose exec postgres psql -U docsagent -d docsagent -c \
  "INSERT INTO tenant_users (id, tenant_id, user_id, role_id, status, joined_at, created_at, updated_at)
   SELECT gen_random_uuid(), '00000000-0000-0000-0000-000000000001', u.id,
          (SELECT id FROM tenant_roles WHERE name='member' AND tenant_id='00000000-0000-0000-0000-000000000001' LIMIT 1),
          'active', NOW(), NOW(), NOW()
   FROM users u WHERE u.username='ops'
   ON CONFLICT DO NOTHING;"
```

---

## 📞 下一步

1. **运行修复脚本**：
   ```bash
   docker-compose exec backend python /app/fix_admin_permissions.py --fix
   ```

2. **测试登录**：
   - 用户名：`admin`
   - 密码：`admin123`

3. **验证功能**：
   - 能管理租户（平台功能）
   - 能上传文档和问答（业务功能）

4. **创建运维账号**（可选）：
   ```bash
   docker-compose exec backend python /app/fix_admin_permissions.py --create-ops
   ```

---

**🎉 完成以上步骤后，你的admin账号就能同时拥有管理权限和业务功能权限了！**

有任何问题随时问我。
