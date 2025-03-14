from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class Machine(Base):
    """远程服务器机器模型"""
    
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=22, nullable=False)
    username = Column(String(50), nullable=False)
    key_file = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # 最后一次状态检查
    last_check = Column(DateTime(timezone=True), nullable=True)
    is_online = Column(Boolean, default=False)
    backend_running = Column(Boolean, default=False)
    frontend_running = Column(Boolean, default=False)
    
    # 监控信息
    cpu_usage = Column(String(50), nullable=True)
    memory_usage = Column(String(50), nullable=True)
    disk_usage = Column(String(50), nullable=True)
    
    # 关联的日志记录
    logs = relationship("MachineLog", back_populates="machine", cascade="all, delete-orphan")
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 