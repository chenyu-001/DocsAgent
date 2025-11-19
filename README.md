# 📚 DocsAgent - 文档理解小机器人

一个基于 RAG（检索增强生成）的智能文档理解系统，能够理解并回答关于上传文档的问题。

## ✨ 核心功能

- 📄 **多格式支持**：PDF、Word、PowerPoint、Excel、TXT、Markdown
- 🔍 **智能检索**：基于向量相似度的语义检索
- 🤖 **AI 问答**：使用 Qwen 等 LLM 理解文档内容并回答问题
- 🔐 **权限管理**：用户认证和文档访问控制
- 📊 **日志追踪**：完整的操作和查询日志

## 🛠️ 技术栈

**后端**:
- FastAPI - 高性能 Web 框架
- PostgreSQL - 元数据存储
- Qdrant - 向量数据库
- BGE - 中文嵌入模型 (BAAI/bge-large-zh-v1.5)
- Qwen - 大语言模型（通义千问）

**文档解析**:
- PyMuPDF - PDF 解析
- python-docx - Word 文档
- python-pptx - PowerPoint
- openpyxl - Excel

## 🚀 快速开始

### 1. 前置要求

- Docker & Docker Compose
- (可选) 阿里云 API Key 用于 Qwen 模型

### 2. 配置环境变量

编辑 `.env` 文件，配置你的 API Key：

```bash
# 通义千问 API Key（必须）
LLM_API_KEY=sk-your-qwen-api-key-here

# 数据库密码（建议修改）
POSTGRES_PASSWORD=your-strong-password

# JWT 密钥（生产环境必须修改）
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### 3. 启动服务

```bash
# 启动所有服务（PostgreSQL + Qdrant + Backend）
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

### 4. 访问应用

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **Qdrant 管理界面**: http://localhost:6333/dashboard

## 📖 使用示例

### 1. 用户注册

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "测试用户"
  }'
```

### 2. 用户登录

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# 返回示例：
# {"access_token":"eyJ...", "token_type":"bearer"}
```

### 3. 上传文档

```bash
TOKEN="your-access-token-here"

curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/document.pdf"
```

### 4. 检索文档

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "这个文档的主要内容是什么？",
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
│   │   ├── auth.py            # 认证系统
│   │   └── db.py              # 数据库连接
│   ├── models/                 # 数据模型
│   │   ├── user_models.py     # 用户模型
│   │   ├── document_models.py # 文档模型
│   │   └── chunk_models.py    # 文本块模型
│   ├── services/               # 业务逻辑
│   │   ├── parser/            # 文档解析器
│   │   ├── embedder/          # 向量嵌入
│   │   ├── chunker.py         # 文本切片
│   │   └── retriever.py       # 检索服务
│   ├── routes/                 # API 路由
│   │   ├── upload.py          # 文档上传
│   │   └── search.py          # 文档检索
│   └── utils/                  # 工具函数
├── docker-compose.yml          # Docker 编排
├── .env                        # 环境变量
└── README.md                   # 项目文档
```

## 🔧 开发模式

### 本地开发（不使用 Docker）

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**注意**: 本地开发仍需要 PostgreSQL 和 Qdrant 服务，可使用 Docker 单独启动：

```bash
docker-compose up -d postgres qdrant
```

## ⚙️ 配置说明

### 嵌入模型

默认使用 **BGE-large-zh-v1.5** 中文嵌入模型，首次启动会自动下载（约 1.3GB）。

如需切换模型，修改 `.env`:

```bash
# 使用其他 BGE 模型
EMBEDDING_MODEL_NAME=BAAI/bge-base-zh-v1.5

# 或使用 OpenAI embeddings
EMBEDDING_MODEL_TYPE=openai
OPENAI_API_KEY=sk-your-openai-key
```

### LLM 模型

支持多种 LLM：

```bash
# Qwen（默认）
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

## 🐛 常见问题

### 1. 模型下载慢

BGE 模型会从 Hugging Face 下载。国内用户可设置镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### 2. 内存不足

BGE-large 模型需要约 2GB 内存。如果内存有限，可使用更小的模型：

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5  # 约 100MB
```

### 3. GPU 加速

如果有 GPU，可启用 CUDA 加速：

```bash
EMBEDDING_DEVICE=cuda
```

## 📝 TODO

- [ ] 实现 QA（问答）接口
- [ ] 添加文档管理界面
- [ ] 支持更多文件格式（图片 OCR）
- [ ] 实现重排序（Reranker）
- [ ] 添加权限控制（ACL）
- [ ] 构建前端界面

## 📄 许可证

MIT License

## 🙋 获取 Qwen API Key

1. 访问 [阿里云-模型服务灵积](https://dashscope.console.aliyun.com/)
2. 开通"通义千问"服务
3. 创建 API Key
4. 将 API Key 填入 `.env` 文件的 `LLM_API_KEY`

## 💡 贡献

欢迎提交 Issue 和 Pull Request！

---

**注意**: 这是一个初始版本，部分功能还在完善中。如有问题请提 Issue。
