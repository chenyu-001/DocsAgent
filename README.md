DocsAgent/
│
├── backend/                         # ← 主后端 (FastAPI)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                  # 入口: 创建 FastAPI app
│   │   ├── config.py                # 环境配置/常量
│   │   ├── db.py                    # 数据库连接与模型初始化
│   │   ├── auth.py                  # 登录验证 / JWT / 权限依赖
│   │   ├── logging_config.py        # 日志设置（结构化+文件分日）
│   │   │
│   │   ├── routes/                  # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── upload.py            # 上传文件 + 解析任务
│   │   │   ├── search.py            # Hybrid 检索接口
│   │   │   ├── qa.py                # 问答接口（RAG，可后补）
│   │   │   ├── docs.py              # 文档管理/元信息
│   │   │   ├── acl.py               # 权限配置接口
│   │   │   └── metrics.py           # 查询日志/统计
│   │   │
│   │   ├── services/                # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── parser/              # 文档解析模块
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pdf_parser.py
│   │   │   │   ├── docx_parser.py
│   │   │   │   ├── pptx_parser.py
│   │   │   │   └── text_parser.py
│   │   │   ├── chunker.py           # 文本切片逻辑
│   │   │   ├── embedder/            # 向量嵌入模块
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py          # 抽象类定义
│   │   │   │   ├── openai_embedder.py
│   │   │   │   └── local_bge_embedder.py
│   │   │   ├── retriever.py         # Hybrid 检索 + 权限过滤
│   │   │   ├── reranker/            # 语义重排
│   │   │   │   ├── __init__.py
│   │   │   │   └── local_reranker.py
│   │   │   ├── auth_service.py
│   │   │   ├── storage_service.py   # 文件存储/预览路径管理
│   │   │   └── log_service.py
│   │   │
│   │   ├── models/                  # 数据模型定义
│   │   │   ├── __init__.py
│   │   │   ├── user_models.py
│   │   │   ├── document_models.py
│   │   │   ├── acl_models.py
│   │   │   ├── chunk_models.py
│   │   │   └── log_models.py
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── hash.py              # 文件哈希/命名工具
│   │       ├── text_clean.py        # 文本清洗/正则过滤
│   │       └── timing.py            # 性能计时装饰器
│   │
│   ├── requirements.txt             # Python 依赖
│   └── Dockerfile                   # 构建后端镜像
│
│
├── web/                             # ← 前端 (React + Tailwind，可后期补)
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ResultCard.tsx
│   │   │   ├── LoginForm.tsx
│   │   │   └── ACLPanel.tsx
│   │   ├── pages/
│   │   │   ├── SearchPage.tsx
│   │   │   ├── DocumentPage.tsx
│   │   │   └── LoginPage.tsx
│   │   └── api/
│   │       ├── client.ts
│   │       └── types.ts
│   └── Dockerfile
│
│
├── storage/                         # ← 原始文件 & 解析缓存
│   ├── uploads/
│   ├── parsed/
│   └── previews/
│
├── logs/                            # ← 日志系统
│   ├── 202511/
│   └── ...
│
├── tests/
│   ├── test_upload.py
│   ├── test_search.py
│   ├── test_acl.py
│   └── test_retriever.py
│
├── docker-compose.yml
├── README.md
└── .env.example                     # 环境变量模板
