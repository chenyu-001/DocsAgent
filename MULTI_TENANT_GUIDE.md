# 🏢 DocsAgent 多租户架构指南

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [架构设计](#架构设计)
- [数据库迁移](#数据库迁移)
- [权限系统](#权限系统)
- [API使用](#api使用)
- [部署模式](#部署模式)
- [最佳实践](#最佳实践)

---

## 概述

DocsAgent 多租户架构支持:

✅ **三层权限体系**: 平台 → 租户 → 资源
✅ **灵活的角色系统**: 基于位运算的权限控制
✅ **三种部署模式**: Cloud / Hybrid / Local
✅ **完整审计日志**: 所有敏感操作记录
✅ **数据隔离**: Schema隔离或独立数据库
✅ **向量库支持**: Qdrant / Milvus 命名空间隔离

---

## 快速开始

### 1. 数据库迁移

```bash
# 进入backend目录
cd backend

# 初始化数据库(会创建所有表和默认租户)
python init_db.py

# 如果需要重置数据库(⚠️ 会删除所有数据!)
python init_db.py --drop

# 创建测试租户
python init_db.py --create-test-tenant
```

### 2. 启动服务

```bash
# 启动后端
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 或使用Docker
docker-compose up -d
```

### 3. 测试API

```bash
# 登录获取token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# 获取当前租户信息
curl -X GET "http://localhost:8000/api/tenants/current/info" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001"
```

---

## 架构设计

### 系统层级

```
┌─────────────────────────────────────────┐
│         平台管理员 (Super Admin)          │  ← 管理所有租户
├─────────────────────────────────────────┤
│              租户层 (Tenant)             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ 企业 A  │  │ 企业 B  │  │ 企业 C  │  │  ← 数据隔离
│  └────┬────┘  └────┬────┘  └────┬────┘  │
│       │            │            │       │
│  ┌────▼────────────▼────────────▼────┐  │
│  │     租户内部 (部门/用户/角色)      │  │  ← 权限管理
│  └───────────────────────────────────┘  │
│       │                                 │
│  ┌────▼────────────────────────────┐    │
│  │   资源层 (文档/文件夹/工作空间)  │    │  ← 细粒度权限
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### 核心模型

#### 1. 租户模型 (Tenant)

```python
# 租户表字段
- id: UUID (主键)
- name: 租户名称
- slug: URL标识
- deploy_mode: 部署模式(cloud/hybrid/local)
- storage_quota_bytes: 存储配额
- user_quota: 用户数上限
- document_quota: 文档数上限
- status: 租户状态(active/suspended/trial)
```

#### 2. 权限模型 (Permission)

使用位运算的权限系统:

```python
Permission.NONE = 0       # 无权限
Permission.READ = 1       # 读取 (1 << 0)
Permission.WRITE = 2      # 写入 (1 << 1)
Permission.DELETE = 4     # 删除 (1 << 2)
Permission.SHARE = 8      # 分享 (1 << 3)
Permission.ADMIN = 16     # 管理 (1 << 4)
Permission.DOWNLOAD = 32  # 下载 (1 << 5)
Permission.COMMENT = 64   # 评论 (1 << 6)
Permission.EXPORT = 128   # 导出 (1 << 7)

# 预设组合
Permission.READER = READ | DOWNLOAD  # 33
Permission.EDITOR = READ | WRITE | DOWNLOAD | COMMENT  # 67
Permission.OWNER = 255  # 所有权限
```

#### 3. 角色模型 (TenantRole)

每个租户可以定义自己的角色:

- **tenant_admin**: 租户管理员(所有权限)
- **member**: 普通成员(编辑权限)
- **guest**: 访客(只读权限)
- **自定义角色**: 支持创建自定义角色

---

## 数据库迁移

### 迁移文件

所有迁移脚本位于 `backend/migrations/` 目录:

- `001_add_folders.sql` - 文件夹功能
- `002_add_multi_tenant.sql` - 多租户架构 ⭐

### 迁移内容

`002_add_multi_tenant.sql` 包含:

1. **租户核心表**
   - `tenants` - 租户表
   - `tenant_features` - 功能开关
   - `departments` - 部门表

2. **权限体系**
   - `tenant_roles` - 租户角色
   - `tenant_users` - 租户用户关联
   - `resource_permissions` - 资源权限
   - `platform_admins` - 平台管理员

3. **审计日志**
   - `audit_logs` - 审计日志
   - `login_history` - 登录历史

4. **触发器**
   - 自动更新 `updated_at`
   - 自动更新租户统计信息

5. **默认数据**
   - 创建默认租户(ID: `00000000-0000-0000-0000-000000000001`)
   - 迁移现有用户到默认租户
   - 创建系统角色

---

## 权限系统

### 权限检查流程

```python
from services.permission_checker import PermissionChecker, PermissionContext
from models.tenant_permission_models import Permission, ResourceType

# 创建权限上下文
ctx = PermissionContext(
    user_id=1,
    tenant_id="tenant-uuid",
    resource_type=ResourceType.DOCUMENT,
    resource_id="doc-123",
    required_permission=Permission.READ
)

# 检查权限
checker = PermissionChecker(db)
has_permission = checker.check(ctx)  # 抛出403如果无权限
```

### 权限继承

权限检查顺序:

1. **平台管理员** → 直接放行
2. **租户管理员** → 直接放行
3. **用户直接授权** → 检查resource_permissions表
4. **角色授权** → 通过用户的角色检查
5. **部门授权** → 通过用户的部门检查
6. **父资源权限** → 递归向上查找
7. **角色默认权限** → 使用角色的默认权限

### 授权管理

```python
from services.permission_checker import PermissionManager

perm_manager = PermissionManager(db)

# 授予权限
perm_manager.grant_permission(
    tenant_id="tenant-uuid",
    resource_type=ResourceType.DOCUMENT,
    resource_id="doc-123",
    grantee_type=GranteeType.USER,
    grantee_id="user-456",
    permission=Permission.EDITOR,
    granted_by=admin_user_id
)

# 撤销权限
perm_manager.revoke_permission(
    tenant_id="tenant-uuid",
    resource_type=ResourceType.DOCUMENT,
    resource_id="doc-123",
    grantee_type=GranteeType.USER,
    grantee_id="user-456"
)
```

---

## API使用

### 租户识别

系统支持多种方式识别租户:

#### 1. Header方式 (推荐)

```bash
curl -X GET "http://localhost:8000/api/tenants/current/info" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 2. 子域名方式

```bash
# 访问: http://test-company.localhost:8000
# 自动识别租户slug为 "test-company"
```

#### 3. 查询参数方式

```bash
curl -X GET "http://localhost:8000/api/documents?tenant_id=tenant-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 平台管理API

#### 创建租户 (需要平台管理员权限)

```bash
curl -X POST "http://localhost:8000/api/tenants/" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "slug": "acme",
    "description": "Acme公司的文档系统",
    "deploy_mode": "cloud",
    "storage_quota_bytes": 107374182400,
    "user_quota": 100,
    "document_quota": 10000,
    "contact_email": "admin@acme.com"
  }'
```

#### 列出所有租户

```bash
curl -X GET "http://localhost:8000/api/tenants/" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

#### 更新租户

```bash
curl -X PATCH "http://localhost:8000/api/tenants/tenant-uuid" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "storage_quota_bytes": 214748364800
  }'
```

### 租户管理API

#### 获取当前租户信息

```bash
curl -X GET "http://localhost:8000/api/tenants/current/info" \
  -H "X-Tenant-ID: tenant-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 邀请用户加入租户 (需要租户管理员权限)

```bash
curl -X POST "http://localhost:8000/api/tenants/current/users/invite" \
  -H "X-Tenant-ID: tenant-uuid" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "role_name": "member",
    "department_id": "dept-uuid"
  }'
```

#### 列出租户用户

```bash
curl -X GET "http://localhost:8000/api/tenants/current/users" \
  -H "X-Tenant-ID: tenant-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 创建自定义角色

```bash
curl -X POST "http://localhost:8000/api/tenants/current/roles" \
  -H "X-Tenant-ID: tenant-uuid" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "reviewer",
    "display_name": "审核员",
    "description": "可以查看和评论文档",
    "permissions": 97
  }'
```

### 权限管理API

#### 授予权限

```bash
curl -X POST "http://localhost:8000/api/tenants/current/permissions/grant" \
  -H "X-Tenant-ID: tenant-uuid" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "document",
    "resource_id": "123",
    "grantee_type": "user",
    "grantee_id": "456",
    "permission": 67,
    "expires_at": "2025-12-31T23:59:59"
  }'
```

#### 查看资源权限

```bash
curl -X GET "http://localhost:8000/api/tenants/current/permissions/document/123" \
  -H "X-Tenant-ID: tenant-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 部署模式

### Cloud模式

**特点**: 共享基础设施,Schema隔离

```python
# 租户配置
{
    "deploy_mode": "cloud",
    "db_schema": "tenant_xxx",  # 自动生成
    "vector_namespace": "tenant-uuid"
}
```

**优势**:
- ✅ 轻量级,易管理
- ✅ 成本低
- ✅ 快速扩展

**适用场景**: 中小型客户,SaaS服务

### Hybrid模式

**特点**: 元数据云端,业务数据本地

```python
# 租户配置
{
    "deploy_mode": "hybrid",
    "db_connection": "postgresql://local-db:5432/tenant_db",
    "vector_db_config": {
        "type": "qdrant",
        "host": "customer-qdrant.local",
        "port": 6333
    }
}
```

**优势**:
- ✅ 数据本地化(合规要求)
- ✅ 统一管理
- ✅ 灵活配置

**适用场景**: 对数据安全有要求的企业

### Local模式

**特点**: 完全本地部署

```python
# 租户配置
{
    "deploy_mode": "local",
    "db_connection": "postgresql://local:5432/docsagent",
    "vector_db_config": {...},
    "storage_config": {
        "type": "local",
        "base_path": "/data/uploads"
    },
    "license_key": "eyJ..."  # License验证
}
```

**优势**:
- ✅ 完全控制
- ✅ 数据不出本地
- ✅ 高性能

**适用场景**: 大型企业,政府机构

---

## 最佳实践

### 1. 租户命名

```python
# ✅ 好的slug
"acme-corp"
"tech-company"
"user-123"

# ❌ 避免的slug
"Acme Corp"  # 不要有空格
"公司名"      # 不要用非ASCII字符
"admin"      # 避免保留关键字
```

### 2. 权限设计

```python
# 最小权限原则
# 新用户默认只给 READER 权限
default_permission = Permission.READER

# 按需授权
# 只在用户需要时才授予更高权限
if user.is_team_lead:
    permission = Permission.EDITOR | Permission.SHARE

# 临时授权
# 使用expires_at实现临时权限
grant_permission(..., expires_at="2025-12-31")
```

### 3. 审计日志

```python
# 关键操作必须记录审计日志
from services.audit_service import AuditService, audit_decorator

@audit_decorator(AuditAction.DOC_DELETE, level=AuditLevel.CRITICAL)
async def delete_document(doc_id: int, current_user: User, db: Session):
    # 删除逻辑
    pass
```

### 4. 配额管理

```python
# 操作前检查配额
if tenant.is_quota_exceeded("storage"):
    raise HTTPException(403, "Storage quota exceeded")

# 定期清理
# 使用cron job定期检查过期租户和配额
```

### 5. 数据隔离

```python
# 所有查询必须加上tenant_id过滤
documents = db.query(Document).filter(
    Document.tenant_id == current_tenant.id  # ⭐ 重要!
).all()

# 使用中间件自动设置租户上下文
# 参考 services/tenant_context.py
```

---

## 故障排除

### 问题1: 迁移失败

```bash
# 检查数据库连接
psql -U user -d docsagent

# 查看错误日志
tail -f logs/backend.log

# 重新运行迁移
python init_db.py --drop
```

### 问题2: 权限检查失败

```python
# 启用调试日志
import logging
logging.getLogger("services.permission_checker").setLevel(logging.DEBUG)

# 检查租户用户关联
db.query(TenantUser).filter(
    TenantUser.user_id == user_id,
    TenantUser.tenant_id == tenant_id
).first()
```

### 问题3: 租户未找到

```bash
# 检查租户ID或slug
curl -X GET "http://localhost:8000/api/tenants/" -H "Authorization: Bearer ADMIN_TOKEN"

# 检查Header
X-Tenant-ID: 正确的UUID或slug
```

---

## 下一步

1. **集成前端**: 更新前端以支持多租户
2. **License系统**: 实现本地部署的License验证
3. **监控告警**: 添加租户资源监控
4. **数据同步**: 实现Hybrid模式的数据同步
5. **API文档**: 生成完整的OpenAPI文档

---

## 参考文档

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Qdrant文档](https://qdrant.tech/documentation/)

---

**🎉 恭喜!** 你已经成功部署了DocsAgent多租户架构!

如有问题,请查看日志或提交Issue。
