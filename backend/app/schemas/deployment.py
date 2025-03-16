from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from .project import ProjectResponse
from .machine import Machine

class DeploymentBase(BaseModel):
    """部署基础模型"""
    project_id: int
    machine_id: int
    environment: str = "development"

class DeploymentCreate(DeploymentBase):
    """创建部署请求"""
    deploy_path: Optional[str] = None

class DeploymentUpdate(BaseModel):
    """更新部署状态"""
    status: str
    deploy_path: Optional[str] = None
    log: Optional[str] = None
    deployed_at: Optional[datetime] = None

class DeployInfo(BaseModel):
    """部署信息"""
    deploy_path: str
    environment: str = "development"

class DeploymentResponse(DeploymentBase):
    """部署响应模型"""
    id: int
    status: str
    deploy_path: Optional[str] = None
    log: Optional[str] = None
    deployed_at: Optional[datetime] = None
    created_at: datetime
    project: Optional[ProjectResponse] = None
    machine: Optional[Machine] = None

    class Config:
        from_attributes = True

class ProjectMachineLink(BaseModel):
    """项目-机器关联"""
    project_id: int
    machine_id: int 