# 🚀 部署指南

本文档提供 DocsAgent 的详细部署和配置说明。

## 📋 目录

- [系统要求](#系统要求)
- [Docker 部署（推荐）](#docker-部署推荐)
- [环境变量配置](#环境变量配置)
- [数据库初始化](#数据库初始化)
- [生产环境配置](#生产环境配置)
- [故障排除](#故障排除)

---

## 系统要求

### 硬件要求

**最低配置**：
- CPU: 2 核心
- 内存: 4GB RAM
- 磁盘: 10GB 可用空间

**推荐配置**：
- CPU: 4 核心以上
- 内存: 8GB RAM 以上
- 磁盘: 50GB 可用空间（用于存储文档和模型）

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- （可选）GPU 支持用于加速模型推理

---

## Docker 部署（推荐）

### 1. 克隆项目

```bash
git clone https://github.com/chenyu-001/DocsAgent.git
cd DocsAgent
```

### 2. 配置环境变量

复制并编辑环境变量文件：

```bash
cp .env.example .env
nano .env  # 或使用其他编辑器
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 等待服务启动（约 30-60 秒）
docker-compose ps

# 查看启动日志
docker-compose logs -f backend
```

### 4. 验证部署

```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 预期输出：
# {
#   "status": "healthy",
#   "database": "connected",
#   "vector_db": "connected"
# }
```

### 5. 访问应用

- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **Qdrant 管理界面**: http://localhost:6333/dashboard

---

## 环境变量配置

### 核心配置

#### 数据库配置

```bash
# PostgreSQL 配置
POSTGRES_USER=docsagent          # 数据库用户名
POSTGRES_PASSWORD=your_password  # 数据库密码（必须修改）
POSTGRES_DB=docsagent            # 数据库名称
POSTGRES_HOST=postgres           # 数据库主机（Docker 内部网络）
POSTGRES_PORT=5432               # 数据库端口
```

#### JWT 认证配置

```bash
# JWT 密钥（生产环境必须修改为随机字符串）
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### LLM 配置

#### 通义千问（默认）

```bash
LLM_TYPE=qwen
LLM_API_KEY=sk-your-qwen-api-key
LLM_MODEL_NAME=qwen-plus          # 或 qwen-turbo, qwen-max
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### OpenAI

```bash
LLM_TYPE=openai
LLM_API_KEY=sk-your-openai-key
LLM_MODEL_NAME=gpt-4o-mini        # 或 gpt-4, gpt-3.5-turbo
LLM_BASE_URL=https://api.openai.com/v1
```

#### Claude

```bash
LLM_TYPE=claude
LLM_API_KEY=sk-ant-your-claude-key
LLM_MODEL_NAME=claude-3-5-sonnet-20241022
LLM_BASE_URL=https://api.anthropic.com
```

### 嵌入模型配置

```bash
# BGE 中文嵌入模型（默认）
EMBEDDING_MODEL_TYPE=huggingface
EMBEDDING_MODEL_NAME=BAAI/bge-large-zh-v1.5  # 推荐
# EMBEDDING_MODEL_NAME=BAAI/bge-base-zh-v1.5  # 中等大小
# EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5 # 小型模型

# 模型设备
EMBEDDING_DEVICE=cpu              # 或 cuda（需要 GPU）

# Hugging Face 镜像（可选，国内用户推荐）
HF_ENDPOINT=https://hf-mirror.com
```

### 向量数据库配置

```bash
# Qdrant 配置
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=documents
```

### 文件上传配置

```bash
# 文件上传限制
MAX_UPLOAD_SIZE=52428800          # 50MB (bytes)
ALLOWED_EXTENSIONS=pdf,docx,pptx,xlsx,txt,md

# 文档存储路径
STORAGE_PATH=/app/storage
```

### 多租户配置

```bash
# 默认租户 ID
DEFAULT_TENANT_ID=00000000-0000-0000-0000-000000000001

# 租户隔离模式
# - namespace: 使用向量库命名空间隔离（推荐）
# - database: 独立数据库隔离（高安全性）
TENANT_ISOLATION_MODE=namespace
```

---

## 数据库初始化

### 自动初始化

首次启动时，系统会自动：
1. 创建所有数据库表
2. 创建默认租户
3. 创建系统角色
4. 创建默认管理员账号

**默认管理员账号**：
- 用户名：`admin`
- 密码：`admin123`
- ⚠️ **生产环境必须立即修改密码**

### 手动初始化

如果需要手动执行初始化：

```bash
# 进入 backend 容器
docker-compose exec backend bash

# 运行初始化脚本
cd /app
python init_db.py

# 创建测试租户（可选）
python init_db.py --create-test-tenant

# 重置数据库（⚠️ 会删除所有数据）
python init_db.py --drop
```

### 数据库迁移

执行数据库迁移脚本：

```bash
# 进入 backend 容器
docker-compose exec backend bash

# 执行迁移
cd /app
bash run_migration.sh
```

---

## 生产环境配置

### 安全建议

#### 1. 修改默认密码

```bash
# 数据库密码
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# JWT 密钥
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

#### 2. 使用 HTTPS

建议使用 Nginx 反向代理并配置 SSL：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. 设置文件权限

```bash
# 限制环境变量文件权限
chmod 600 .env

# 限制存储目录权限
chmod 700 storage/
```

#### 4. 配置防火墙

```bash
# 只开放必要端口
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH
ufw enable
```

### 性能优化

#### 1. 调整 Docker 资源限制

编辑 `docker-compose.yml`：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

#### 2. 启用 GPU 加速

如果有 NVIDIA GPU，可以启用 CUDA 加速：

```yaml
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

环境变量：
```bash
EMBEDDING_DEVICE=cuda
```

#### 3. 使用 Redis 缓存

添加 Redis 服务用于缓存：

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### 备份策略

#### 1. 数据库备份

```bash
# 自动备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backup
DATE=$(date +%Y%m%d_%H%M%S)

# 备份 PostgreSQL
docker-compose exec -T postgres pg_dump -U docsagent docsagent > \
  ${BACKUP_DIR}/postgres_${DATE}.sql

# 备份 Qdrant
docker cp docsagent-qdrant:/qdrant/storage ${BACKUP_DIR}/qdrant_${DATE}

# 保留最近 7 天的备份
find ${BACKUP_DIR} -mtime +7 -delete
EOF

chmod +x backup.sh

# 添加到 crontab（每天凌晨 2 点备份）
0 2 * * * /path/to/backup.sh
```

#### 2. 文档存储备份

```bash
# 备份文档存储
tar -czf storage_backup_$(date +%Y%m%d).tar.gz storage/
```

---

## 故障排除

### 容器无法启动

**问题**：`docker-compose up -d` 失败

**排查步骤**：

```bash
# 1. 查看详细日志
docker-compose logs backend
docker-compose logs postgres

# 2. 检查端口占用
netstat -tuln | grep -E '3000|8000|5432|6333'

# 3. 检查磁盘空间
df -h

# 4. 重建容器
docker-compose down -v
docker-compose up -d --build
```

### 数据库连接失败

**问题**：后端无法连接数据库

**解决方案**：

```bash
# 1. 检查数据库容器状态
docker-compose ps postgres

# 2. 测试数据库连接
docker-compose exec postgres psql -U docsagent -d docsagent -c "SELECT 1;"

# 3. 检查环境变量
docker-compose exec backend env | grep POSTGRES

# 4. 重启数据库
docker-compose restart postgres
docker-compose restart backend
```

### 模型下载失败

**问题**：BGE 模型下载超时或失败

**解决方案**：

```bash
# 1. 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com

# 2. 手动下载模型
mkdir -p models
cd models
git clone https://hf-mirror.com/BAAI/bge-large-zh-v1.5

# 3. 挂载到容器
# 在 docker-compose.yml 中添加：
volumes:
  - ./models:/app/models
```

### LLM API 调用失败

**问题**：智能问答功能报错

**排查步骤**：

```bash
# 1. 测试 API Key
curl -X POST "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-turbo","messages":[{"role":"user","content":"test"}]}'

# 2. 检查配置
docker-compose exec backend python -c "
from api.config import settings
print(f'LLM Type: {settings.LLM_TYPE}')
print(f'LLM Model: {settings.LLM_MODEL_NAME}')
print(f'API Key: {settings.LLM_API_KEY[:10]}...')
"

# 3. 查看详细错误日志
docker-compose logs -f backend | grep -i "llm\|error"
```

### 内存不足

**问题**：容器 OOM (Out of Memory)

**解决方案**：

```bash
# 1. 使用更小的模型
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5

# 2. 增加交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. 调整 Docker 内存限制
docker-compose up -d --scale backend=1 --memory=2g
```

### 文档上传失败

**问题**：文档上传时报错

**排查步骤**：

```bash
# 1. 检查文件大小限制
echo "MAX_UPLOAD_SIZE=104857600" >> .env  # 100MB

# 2. 检查存储路径权限
docker-compose exec backend ls -la /app/storage

# 3. 检查磁盘空间
docker-compose exec backend df -h /app/storage

# 4. 查看上传日志
docker-compose logs backend | grep -i "upload\|error"
```

---

## 监控和日志

### 日志查看

```bash
# 实时查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f postgres

# 查看最近 100 行
docker-compose logs --tail=100 backend

# 导出日志到文件
docker-compose logs backend > backend.log
```

### 健康检查

```bash
# 检查所有服务健康状态
curl http://localhost:8000/health

# 检查数据库连接
docker-compose exec postgres pg_isready -U docsagent

# 检查 Qdrant
curl http://localhost:6333/health
```

---

## 更新和维护

### 更新代码

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重建容器
docker-compose up -d --build

# 3. 执行数据库迁移（如果有）
docker-compose exec backend bash /app/run_migration.sh
```

### 清理和重置

```bash
# 停止所有服务
docker-compose down

# 删除所有数据（包括数据库）
docker-compose down -v

# 清理 Docker 资源
docker system prune -a
```

---

## 获取帮助

- 📖 查看 [README.md](./README.md) 了解基础使用
- 🐛 提交 [GitHub Issue](https://github.com/chenyu-001/DocsAgent/issues)
- 💬 查看 [Discussions](https://github.com/chenyu-001/DocsAgent/discussions)

---

**部署成功后，请务必修改默认密码并做好安全加固！**
