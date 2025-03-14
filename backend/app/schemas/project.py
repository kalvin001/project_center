from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List, Union
from datetime import datetime


class ProjectBase(BaseModel):
    """项目基本信息"""
    name: str
    description: Optional[str] = None
    project_type: str = "fullstack"
    repository_url: str
    repository_type: str = "git"
    tech_stack: Optional[Dict[str, Any]] = None


# 添加统计信息模型
class ProjectStats(BaseModel):
    """项目统计信息"""
    file_count: int = 0
    total_size_bytes: int = 0
    code_lines: int = 0
    total_size_human: str = "0 B"
    ignore_file_exists: bool = False


class ProjectCreate(ProjectBase):
    """创建项目需要的数据"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目需要的数据"""
    name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None
    repository_type: Optional[str] = None
    project_type: Optional[str] = None
    tech_stack: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProjectInDB(ProjectBase):
    """数据库中的项目数据"""
    id: int
    owner_id: int
    storage_path: str
    created_at: datetime
    last_updated: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ProjectResponse(ProjectInDB):
    """返回给客户端的项目数据"""
    pass


# 添加统计信息的响应模型
class ProjectResponseWithStats(ProjectResponse):
    """包含统计信息的项目数据"""
    stats: Optional[ProjectStats] = None


class DeploymentBase(BaseModel):
    """部署基本信息"""
    project_id: int
    environment: str
    server_host: str
    server_port: Optional[int] = None
    deploy_path: str


class DeploymentCreate(BaseModel):
    """创建部署需要的数据"""
    environment: str
    server_host: str
    server_port: Optional[int] = None
    deploy_path: str


class DeploymentUpdate(BaseModel):
    """更新部署需要的数据"""
    environment: Optional[str] = None
    server_host: Optional[str] = None
    server_port: Optional[int] = None
    deploy_path: Optional[str] = None
    status: Optional[str] = None
    log: Optional[str] = None


class DeploymentInDB(DeploymentBase):
    """数据库中的部署数据"""
    id: int
    status: str
    log: Optional[str] = None
    deployed_at: datetime

    class Config:
        from_attributes = True


class DeploymentResponse(DeploymentInDB):
    """返回给客户端的部署数据"""
    pass


class ProjectWithDeployments(ProjectResponseWithStats):
    """包含部署信息和统计信息的项目数据"""
    deployments: List[DeploymentResponse] = [] 