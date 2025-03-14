from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class MachineLog(Base):
    """机器操作和状态日志模型"""
    
    __tablename__ = "machine_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    log_type = Column(String(50), nullable=False)  # deploy, status, start, stop
    content = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)  # success, failed
    
    # 关联的机器
    machine = relationship("Machine", back_populates="logs")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 