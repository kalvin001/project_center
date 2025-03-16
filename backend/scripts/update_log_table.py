import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.sql import select, insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base_class import Base
from app.models.machine import Machine
from app.models.machine_log import MachineLog

# 新的Log模型定义
class Log(Base):
    """通用日志模型，记录系统中的所有操作和状态变化"""
    
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联对象
    entity_type = Column(String(50), nullable=True)  
    entity_id = Column(Integer, nullable=True)       
    
    # 日志分类和操作类型
    category = Column(String(50), nullable=False)    
    operation = Column(String(50), nullable=False)   
    
    # 日志内容
    title = Column(String(255), nullable=False)     
    content = Column(Text, nullable=True)           
    status = Column(String(50), nullable=True)      
    
    # 详细数据
    data = Column(JSON, nullable=True)
    
    # 操作者信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_ip = Column(String(50), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), nullable=False)


def main():
    # 连接数据库
    print("连接数据库...")
    engine = create_engine(settings.DATABASE_URL)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # 创建会话
    session = Session(engine)
    
    # 检查是否存在旧表
    if "machine_logs" in metadata.tables:
        print("找到旧的machine_logs表，准备迁移数据...")
        
        # 获取所有旧数据
        old_logs = session.query(MachineLog).all()
        print(f"找到 {len(old_logs)} 条旧日志记录")
        
        # 创建新表（如果不存在）
        Base.metadata.create_all(bind=engine, tables=[Log.__table__])
        
        # 迁移数据
        for old_log in old_logs:
            # 创建新日志记录
            new_log = Log(
                entity_type="machine",
                entity_id=old_log.machine_id,
                category="operation",  # 假设所有旧日志都是操作日志
                operation=old_log.log_type,
                title=f"机器操作: {old_log.log_type}",
                content=old_log.content,
                status=old_log.status,
                data=None,  # 旧日志没有详细数据
                user_id=None,  # 旧日志没有用户信息
                user_ip=None,
                created_at=old_log.created_at
            )
            session.add(new_log)
        
        # 提交更改
        session.commit()
        print("数据迁移完成")
        
        # 删除旧表（谨慎操作！确保数据已备份）
        print("即将删除旧表，请确认数据已正确迁移...")
        input("按回车键继续...")
        old_table = metadata.tables["machine_logs"]
        old_table.drop(engine)
        print("旧表已删除")
    else:
        print("未找到machine_logs表，创建新的logs表...")
        Base.metadata.create_all(bind=engine, tables=[Log.__table__])
        print("新表创建完成")
    
    print("更新完成！")


if __name__ == "__main__":
    main() 