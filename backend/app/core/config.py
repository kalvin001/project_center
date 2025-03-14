from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用程序设置"""
    # 基础配置
    APP_NAME: str = "项目管理中心"
    API_PREFIX: str = "/api"
    DEBUG: bool = True
    
    # 项目根目录
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROJECTS_DIR: Path = Path("D:/data/code/project_center")
    
    # 数据库配置
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/project_center.db"
    
    # 安全配置
    SECRET_KEY: str = "your_secret_key_here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1天
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8011
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8012",
        "http://127.0.0.1:8012",
        "http://localhost:5173",  # Vite的默认端口
        "http://127.0.0.1:5173",
        "*"  # 允许所有源（开发环境中）
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# 确保项目目录存在
os.makedirs(settings.PROJECTS_DIR, exist_ok=True) 