# Docker 环境下的多租户架构部署指南

## 🚀 快速开始

### 方法1: 使用Shell脚本 (推荐)

在你的本地环境(PowerShell/CMD)中运行：

```bash
# 进入backend容器
docker-compose exec backend bash

# 在容器内执行迁移脚本
cd /app
bash run_migration.sh

# 退出容器
exit
```

### 方法2: 直接执行SQL (如果容器没有bash)

```bash
# 方式A: 使用docker exec直接执行SQL
docker exec -i docsagent-postgres psql -U docsagent -d docsagent < backend/migrations/002_add_multi_tenant.sql

# 方式B: 使用docker-compose exec
docker-compose exec -T postgres psql -U docsagent -d docsagent < backend/migrations/002_add_multi_tenant.sql
```

### 方法3: 使用Python脚本 (如果容器内有Python环境)

```bash
# 进入backend容器
docker-compose exec backend bash

# 运行Python初始化脚本
cd /app
python init_db.py

# 可选: 创建测试租户
python init_db.py --create-test-tenant
```

---

## 📋 详细步骤

### 1. 确保Docker服务已启动

```bash
# 检查容器状态
docker-compose ps

# 应该看到以下服务运行中:
# - docsagent-postgres (healthy)
# - docsagent-qdrant (running)
# - docsagent-backend (running)
# - docsagent-frontend (running)
```

如果服务未启动:

```bash
# 启动所有服务
docker-compose up -d

# 等待数据库健康检查通过
docker-compose ps postgres
```

### 2. 运行数据库迁移

#### 选项A: 使用Shell脚本

```powershell
# Windows PowerShell
docker-compose exec backend bash /app/run_migration.sh
```

```bash
# Linux/Mac
docker-compose exec backend bash /app/run_migration.sh
```

#### 选项B: 手动执行SQL

```bash
# 将SQL文件复制到容器
docker cp backend/migrations/002_add_multi_tenant.sql docsagent-postgres:/tmp/

# 在postgres容器内执行
docker-compose exec postgres psql -U docsagent -d docsagent -f /tmp/002_add_multi_tenant.sql
```

### 3. 验证迁移

```bash
# 进入postgres容器
docker-compose exec postgres psql -U docsagent -d docsagent

# 在psql中执行:
\dt  # 查看所有表

# 检查租户表
SELECT id, name, slug, status FROM tenants;

# 检查角色表
SELECT id, name, display_name, permissions FROM tenant_roles LIMIT 10;

# 退出
\q
```

预期输出应包含:
- ✅ `tenants` 表
- ✅ `tenant_users` 表
- ✅ `tenant_roles` 表
- ✅ `resource_permissions` 表
- ✅ `audit_logs` 表
- ✅ 默认租户 (ID: 00000000-0000-0000-0000-000000000001)

---

## 🔧 故障排除

### 问题1: "docker-compose: command not found"

**解决方案**: 使用新版Docker Compose命令

```bash
# 旧版本
docker-compose exec backend bash

# 新版本 (Docker Compose V2)
docker compose exec backend bash
```

### 问题2: "backend服务未运行"

```bash
# 检查日志
docker-compose logs backend

# 重启服务
docker-compose restart backend
```

### 问题3: "psql: FATAL: password authentication failed"

检查`.env`文件中的数据库密码是否正确:

```bash
# 查看环境变量
docker-compose exec backend env | grep POSTGRES
```

### 问题4: "relation 'tenants' already exists"

迁移已执行过，可以跳过或使用`--drop`重置:

```bash
# 警告: 这会删除所有数据!
docker-compose exec backend python init_db.py --drop
```

### 问题5: Windows路径问题

在Windows PowerShell中，如果遇到路径问题:

```powershell
# 使用正斜杠
docker-compose exec backend bash /app/run_migration.sh

# 或使用反斜杠转义
docker-compose exec backend bash /app/run_migration.sh
```

---

## 📊 验证部署

### 1. 检查API

```bash
# 健康检查
curl http://localhost:8000/health

# 获取租户信息
curl -X GET "http://localhost:8000/api/tenants/current/info" \
  -H "X-Tenant-ID: 00000000-0000-0000-0000-000000000001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. 查看日志

```bash
# 后端日志
docker-compose logs -f backend

# 数据库日志
docker-compose logs -f postgres
```

### 3. 进入容器调试

```bash
# 进入backend容器
docker-compose exec backend bash

# 进入postgres容器
docker-compose exec postgres bash

# 进入qdrant容器
docker-compose exec qdrant sh
```

---

## 🎯 创建测试租户

```bash
# 方法1: 使用Python脚本
docker-compose exec backend python init_db.py --create-test-tenant

# 方法2: 使用API
curl -X POST "http://localhost:8000/api/tenants/" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "slug": "test-company",
    "description": "测试租户",
    "deploy_mode": "cloud"
  }'
```

---

## 🐳 Docker Compose 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart backend

# 查看日志
docker-compose logs -f backend

# 查看容器状态
docker-compose ps

# 进入容器
docker-compose exec backend bash

# 重建容器
docker-compose up -d --build backend

# 删除所有数据(谨慎!)
docker-compose down -v
```

---

## 📁 文件位置(容器内)

在backend容器内:
- 工作目录: `/app`
- 迁移脚本: `/app/migrations/002_add_multi_tenant.sql`
- Shell脚本: `/app/run_migration.sh`
- Python脚本: `/app/init_db.py`
- 日志: `/app/logs/`
- 存储: `/app/storage/`

---

## 🔄 更新代码后重启

```bash
# 代码已挂载到容器,只需重启
docker-compose restart backend

# 如果修改了Dockerfile或requirements.txt
docker-compose up -d --build backend
```

---

## 💡 开发技巧

### 实时日志

```bash
# 监控backend日志
docker-compose logs -f backend

# 同时监控多个服务
docker-compose logs -f backend postgres
```

### 数据库管理

```bash
# 进入psql交互式shell
docker-compose exec postgres psql -U docsagent -d docsagent

# 执行单条SQL
docker-compose exec postgres psql -U docsagent -d docsagent -c "SELECT * FROM tenants;"

# 导出数据
docker-compose exec postgres pg_dump -U docsagent docsagent > backup.sql

# 导入数据
docker-compose exec -T postgres psql -U docsagent -d docsagent < backup.sql
```

### 清理环境

```bash
# 停止并删除容器(保留数据)
docker-compose down

# 停止并删除所有(包括数据卷)
docker-compose down -v

# 重新开始
docker-compose up -d
```

---

## ✅ 部署检查清单

- [ ] Docker和Docker Compose已安装
- [ ] `.env`文件已配置
- [ ] 数据库容器运行正常(`docker-compose ps`)
- [ ] 执行数据库迁移(本文档方法1/2/3)
- [ ] 验证表已创建(`\dt`in psql)
- [ ] 验证默认租户存在
- [ ] API健康检查通过(`/health`)
- [ ] 可以登录并获取token
- [ ] 可以访问租户API

---

## 📞 需要帮助?

1. 查看日志: `docker-compose logs -f backend`
2. 检查数据库: `docker-compose exec postgres psql -U docsagent -d docsagent`
3. 查看完整文档: `MULTI_TENANT_GUIDE.md`
4. GitHub Issues: 提交问题并附上日志

---

**提示**: 如果你使用的是Docker Desktop,可以在图形界面中直接查看容器日志和执行命令!
