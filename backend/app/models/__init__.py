"""
数据库模型模块
"""

# 导入所有模型，确保SQLAlchemy可以找到它们
from app.models.user import User
from app.models.project import Project, Deployment 