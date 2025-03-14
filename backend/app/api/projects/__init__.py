"""项目管理API模块

该模块包含项目管理的所有API端点，包括项目CRUD、文件管理、仓库同步和部署功能。
"""

from .router import router

__all__ = ["router"] 