"""
DocsAgent 主程序入口
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from api.config import settings
from api.logging_config import setup_logging
from api.db import get_db, init_db
from api.auth import UserCreate, UserLogin, Token, authenticate_user, create_access_token, get_password_hash, get_current_active_user
from models.user_models import User
from loguru import logger


# 初始化日志
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("✅ 数据库初始化完成")

    yield

    # 关闭时清理
    logger.info("👋 关闭应用")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="文档理解和问答系统",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 基础路由 ====================
@app.get("/")
async def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ==================== 认证路由 ====================
@app.post("/api/auth/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户是否存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        return {"error": "用户名已存在"}

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        return {"error": "邮箱已被使用"}

    # 创建新用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"新用户注册: {new_user.username}")
    return {"message": "注册成功", "user_id": new_user.id}


@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        return {"error": "用户名或密码错误"}

    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"用户登录: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user.to_dict()


# ==================== 导入其他路由 ====================
from routes import upload, search

app.include_router(upload.router, prefix="/api", tags=["文档上传"])
app.include_router(search.router, prefix="/api", tags=["文档检索"])

# TODO: 后续添加更多路由
# from routes import qa, docs, acl, metrics
# app.include_router(qa.router, prefix="/api", tags=["问答"])
# app.include_router(docs.router, prefix="/api", tags=["文档管理"])
# app.include_router(acl.router, prefix="/api", tags=["权限管理"])
# app.include_router(metrics.router, prefix="/api", tags=["日志统计"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
