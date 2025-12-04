# 📚 DocsAgent - 智能文档理解系统

一个基于 RAG（检索增强生成）的智能文档理解系统，支持多格式文档上传、语义检索和 AI 问答。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 核心功能

- 📄 **多格式支持**：PDF、Word、PowerPoint、Excel、TXT、Markdown
- 🔍 **智能检索**：基于向量相似度的语义检索
- 🤖 **AI 问答**：使用 LLM 理解文档内容并智能回答
- 👥 **多租户架构**：支持企业级多租户隔离
- 🔐 **权限管理**：完整的用户认证和细粒度权限控制
- 📊 **审计日志**：完整的操作追踪和审计

## 🛠️ 技术栈

**后端**:
- FastAPI - 高性能 Web 框架
- PostgreSQL - 关系数据库
- Qdrant - 向量数据库
- BGE - 中文嵌入模型 (BAAI/bge-large-zh-v1.5)
- Qwen/OpenAI/Claude - 大语言模型

**前端**:
- React 18 + TypeScript
- Vite + Tailwind CSS
- React Router + Axios

## 🚀 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 1. 克隆项目

```bash
git clone https://github.com/chenyu-001/DocsAgent.git
cd DocsAgent
```

### 2. 配置环境变量

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少配置以下必要参数：

```bash
# 通义千问 API Key（必须配置才能使用问答功能）
LLM_API_KEY=sk-your-qwen-api-key-here

# 数据库密码（建议修改）
POSTGRES_PASSWORD=your-strong-password

# JWT 密钥（生产环境必须修改）
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

> 💡 **获取 Qwen API Key**：访问 [阿里云-模型服务灵积](https://dashscope.console.aliyun.com/)，开通"通义千问"服务后创建 API Key

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 4. 访问应用

- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📖 使用指南

### Web 界面使用

1. 访问 http://localhost:3000
2. 点击"注册"创建账号（或使用默认账号：`admin` / `admin123`）
3. 登录后进入主界面
4. 上传文档（支持拖拽）
5. 等待文档处理完成
6. 在搜索框输入问题，查看智能回答

### API 使用

详细的 API 文档请访问：http://localhost:8000/docs

#### 快速示例

```bash
# 1. 用户登录
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  | jq -r '.access_token')

# 2. 上传文档
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# 3. 智能问答
curl -X POST "http://localhost:8000/api/qa" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "这个文档的主要内容是什么？",
    "top_k": 5
  }'
```

## 📁 项目结构

```
DocsAgent/
├── backend/                    # 后端服务
│   ├── api/                    # API 层
│   │   ├── main.py            # FastAPI 应用入口
│   │   ├── config.py          # 配置管理
│   │   └── auth.py            # 认证系统
│   ├── models/                 # 数据模型
│   ├── services/               # 业务逻辑
│   │   ├── parser/            # 文档解析
│   │   ├── embedder/          # 向量嵌入
│   │   └── retriever.py       # 检索服务
│   ├── routes/                 # API 路由
│   └── migrations/             # 数据库迁移
├── web/                        # 前端应用
│   ├── src/
│   │   ├── api/               # API 客户端
│   │   ├── components/        # React 组件
│   │   └── pages/             # 页面
├── docker-compose.yml          # Docker 编排
├── .env.example               # 环境变量模板
└── README.md                  # 项目文档
```

## ⚙️ 配置说明

### LLM 模型配置

支持多种大语言模型：

```bash
# 通义千问（默认）
LLM_TYPE=qwen
LLM_API_KEY=sk-your-qwen-key
LLM_MODEL_NAME=qwen-plus

# OpenAI
LLM_TYPE=openai
LLM_API_KEY=sk-your-openai-key
LLM_MODEL_NAME=gpt-4o-mini

# Claude
LLM_TYPE=claude
LLM_API_KEY=sk-ant-your-claude-key
LLM_MODEL_NAME=claude-3-5-sonnet-20241022
```

### 嵌入模型配置

默认使用 BGE-large-zh-v1.5 中文嵌入模型（首次启动会自动下载，约 1.3GB）：

```bash
# 使用其他 BGE 模型
EMBEDDING_MODEL_NAME=BAAI/bge-base-zh-v1.5  # 更小的模型

# 使用 CUDA 加速（需要 GPU）
EMBEDDING_DEVICE=cuda
```

## 🔧 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend

# 进入容器
docker-compose exec backend bash

# 数据库管理
docker-compose exec postgres psql -U docsagent -d docsagent

# 重建容器（更新代码后）
docker-compose up -d --build backend
```

## 🐛 常见问题

### 智能问答功能报错

**问题**：提示"生成回答时出现问题，请稍后重试"

**原因**：
- LLM API Key 未配置或无效
- API 额度不足
- 网络连接问题

**解决**：
1. 检查 `.env` 文件中的 `LLM_API_KEY` 是否正确配置
2. 确认 API 账户有足够的调用额度
3. 测试网络连接：`curl https://dashscope.aliyuncs.com`

> 💡 **提示**：检索功能不需要 LLM API，即使没有配置 API Key 也能正常使用文档搜索。

### 模型下载慢

**问题**：BGE 模型下载速度慢

**解决**：设置 Hugging Face 镜像

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### 内存不足

**问题**：容器 OOM 错误

**解决**：使用更小的嵌入模型

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5  # 约 100MB
```

## 🗺️ 路线图

- [x] 基础文档上传和检索
- [x] 智能问答功能
- [x] 多租户架构
- [x] 细粒度权限控制
- [ ] 图片 OCR 支持
- [ ] 检索重排序（Reranker）
- [ ] 暗色模式
- [ ] 搜索历史记录
- [ ] 知识图谱可视化

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

- 📧 Email: [your-email@example.com]
- 🐛 Issues: [GitHub Issues](https://github.com/chenyu-001/DocsAgent/issues)
- 📖 文档: [Wiki](https://github.com/chenyu-001/DocsAgent/wiki)

---

**⭐ 如果这个项目对你有帮助，欢迎给个 Star！**
