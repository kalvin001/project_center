from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# 创建日志的基础模型
class LogBase(BaseModel):
    entity_type: Optional[str] = Field(None, description="实体类型：machine, project, user, system等")
    entity_id: Optional[int] = Field(None, description="实体ID")
    category: str = Field(..., description="日志分类：system, operation, status, security, error")
    operation: str = Field(..., description="操作类型：create, update, delete, deploy, start, stop, login等")
    title: str = Field(..., description="日志标题")
    content: Optional[str] = Field(None, description="详细内容")
    status: Optional[str] = Field(None, description="状态：success, failed, warning, info")
    data: Optional[Dict[str, Any]] = Field(None, description="额外数据")
    user_ip: Optional[str] = Field(None, description="操作者IP地址")

# 创建日志请求模型
class LogCreate(LogBase):
    user_id: Optional[int] = Field(None, description="操作用户ID，为空表示系统操作")

# 日志过滤请求模型
class LogFilter(BaseModel):
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    category: Optional[str] = None
    operation: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0

# 日志详情响应模型
class LogInDB(LogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

# 日志列表响应模型
class Log(LogInDB):
    username: Optional[str] = None  # 添加用户名，方便前端展示 