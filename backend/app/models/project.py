from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Project(Base):
    """项目模型"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repository_url = Column(String, nullable=False)
    repository_type = Column(String, nullable=False, default="git")
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # 项目类型 (frontend, backend, fullstack, etc.)
    project_type = Column(String, nullable=False, default="fullstack")
    
    # 项目技术栈
    tech_stack = Column(JSON, nullable=True)
    
    # 项目存储路径
    storage_path = Column(String, nullable=False)
    
    # 关系
    owner = relationship("User", backref="projects")
    deployments = relationship("Deployment", back_populates="project", cascade="all, delete-orphan")


class Deployment(Base):
    """部署模型"""
    __tablename__ = "deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    environment = Column(String, nullable=False, default="development")  # development, staging, production
    server_host = Column(String, nullable=False)
    server_port = Column(Integer, nullable=True)
    deploy_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, success, failed
    log = Column(Text, nullable=True)
    deployed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    project = relationship("Project", back_populates="deployments") 