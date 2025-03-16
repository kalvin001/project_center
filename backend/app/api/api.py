from fastapi import APIRouter

from app.api import auth, machines, projects, files, logs

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(machines.router, prefix="/machines", tags=["机器管理"])
api_router.include_router(projects.router, prefix="/projects", tags=["项目管理"])
api_router.include_router(files.router, prefix="/files", tags=["文件管理"])
api_router.include_router(logs.router, prefix="/logs", tags=["日志管理"]) 