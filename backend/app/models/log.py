from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class Log(Base):
    """通用日志模型，记录系统中的所有操作和状态变化"""
    
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联对象（可能为空，表示系统级日志）
    entity_type = Column(String(50), nullable=True)  # 实体类型：machine, project, user, system等
    entity_id = Column(Integer, nullable=True)       # 实体ID
    
    # 日志分类和操作类型
    category = Column(String(50), nullable=False)    # 日志分类：system, operation, status, security, error
    operation = Column(String(50), nullable=False)   # 操作类型：create, update, delete, deploy, start, stop, login, etc.
    
    # 日志内容
    title = Column(String(255), nullable=False)      # 日志标题
    content = Column(Text, nullable=True)            # 详细内容
    status = Column(String(50), nullable=True)       # 状态：success, failed, warning, info
    
    # 详细数据（JSON格式，可存储额外信息）
    data = Column(JSON, nullable=True)
    
    # 操作者信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 可能为空，表示系统操作
    user = relationship("User", backref="logs")
    user_ip = Column(String(50), nullable=True)      # 操作者IP地址
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 