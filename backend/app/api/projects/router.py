"""
项目API路由模块

该模块整合项目API的所有子模块路由。
"""

from fastapi import APIRouter

from . import project_crud
from . import file_operations
from . import repository_sync
from . import deployment

# 创建项目路由 - 移除前缀，因为在api.py中已经有正确的路由前缀
router = APIRouter(tags=["projects"])

# 包含各个子模块的路由
router.include_router(project_crud.router)
router.include_router(file_operations.router)
router.include_router(repository_sync.router)
router.include_router(deployment.router) 