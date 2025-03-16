import logging
from fastapi import FastAPI, APIRouter, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.api import auth, projects, files, machines, logs, deployments
from app.core.config import settings
from app.db.database import init_db, async_session_factory
from app.core.auth import add_test_user

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序启动和关闭事件
    """
    # 启动时初始化数据库
    logger.info("初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成")
    
    # 在启动时添加测试用户
    logger.info("创建测试用户...")
    async with async_session_factory() as db:
        await add_test_user(db)
    logger.info("测试用户创建完成")
    
    yield
    
    # 应用程序关闭时执行清理操作
    logger.info("应用程序关闭，执行清理操作")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    lifespan=lifespan,
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 创建主路由
api_router = APIRouter(prefix=settings.API_PREFIX)

# 添加子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(projects.router, prefix="/projects", tags=["项目"])
api_router.include_router(files.router, prefix="/files", tags=["文件系统"])
api_router.include_router(machines.router, prefix="/machines", tags=["机器管理"])
api_router.include_router(logs.router, prefix="/logs", tags=["日志管理"])
api_router.include_router(deployments.router, prefix="/deployments", tags=["部署管理"])

# 将主路由添加到应用
app.include_router(api_router)

# 配置静态文件服务
static_dir = os.path.join(os.getcwd(), "static")
os.makedirs(static_dir, exist_ok=True)  # 确保目录存在
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """健康检查端点"""
    return {"message": f"欢迎使用{settings.APP_NAME}!", "status": "online"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "api_version": "0.1.0"}


@app.on_event("startup")
async def startup_event():
    """应用程序启动时执行"""
    # 创建测试用户
    async with async_session_factory() as db:
        await add_test_user(db) 