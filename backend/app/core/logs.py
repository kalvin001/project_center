from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from fastapi import Request

from app.models.log import Log
from app.models.user import User
from app.schemas.log import LogCreate, LogFilter


async def create_log(
    db: AsyncSession,
    *,
    category: str,
    operation: str,
    title: str,
    content: Optional[str] = None,
    status: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    user_ip: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> Log:
    """创建日志记录"""
    log_in = LogCreate(
        category=category,
        operation=operation,
        title=title,
        content=content,
        status=status,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        user_ip=user_ip,
        data=data
    )
    db_log = Log(**log_in.dict(exclude_unset=True))
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def create_system_log(
    db: AsyncSession,
    *,
    title: str,
    operation: str,
    content: Optional[str] = None,
    status: str = "info",
    request: Optional[Request] = None
) -> Log:
    """创建系统日志"""
    user_ip = None
    if request:
        user_ip = request.client.host if request.client else None
    
    return await create_log(
        db=db,
        category="system",
        operation=operation,
        title=title,
        content=content,
        status=status,
        user_ip=user_ip
    )


async def create_user_operation_log(
    db: AsyncSession,
    *,
    user_id: int,
    title: str,
    operation: str,
    content: Optional[str] = None,
    status: str = "success",
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    request: Optional[Request] = None,
    data: Optional[Dict[str, Any]] = None
) -> Log:
    """创建用户操作日志"""
    user_ip = None
    if request:
        user_ip = request.client.host if request.client else None
    
    return await create_log(
        db=db,
        category="operation",
        operation=operation,
        title=title,
        content=content,
        status=status,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        user_ip=user_ip,
        data=data
    )


async def create_machine_log(
    db: AsyncSession,
    *,
    machine_id: int,
    operation: str, 
    title: str,
    content: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
    data: Optional[Dict[str, Any]] = None
) -> Log:
    """创建机器操作日志（兼容旧的MachineLog）"""
    user_ip = None
    if request:
        user_ip = request.client.host if request.client else None
    
    return await create_log(
        db=db,
        category="operation",
        operation=operation,
        title=title,
        content=content,
        status=status,
        entity_type="machine", 
        entity_id=machine_id,
        user_id=user_id,
        user_ip=user_ip,
        data=data
    )


async def get_logs(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    filter_params: Optional[LogFilter] = None
) -> List[Dict]:
    """获取日志列表"""
    # 构建查询
    query = select(Log, User.username).outerjoin(User, Log.user_id == User.id)
    
    # 应用过滤条件
    if filter_params:
        conditions = []
        
        if filter_params.entity_type:
            conditions.append(Log.entity_type == filter_params.entity_type)
        
        if filter_params.entity_id:
            conditions.append(Log.entity_id == filter_params.entity_id)
            
        if filter_params.category:
            conditions.append(Log.category == filter_params.category)
            
        if filter_params.operation:
            conditions.append(Log.operation == filter_params.operation)
            
        if filter_params.status:
            conditions.append(Log.status == filter_params.status)
            
        if filter_params.user_id:
            conditions.append(Log.user_id == filter_params.user_id)
            
        if filter_params.start_date:
            conditions.append(Log.created_at >= filter_params.start_date)
            
        if filter_params.end_date:
            conditions.append(Log.created_at <= filter_params.end_date)
            
        if conditions:
            query = query.where(and_(*conditions))
    
    # 按时间倒序排序
    query = query.order_by(Log.created_at.desc())
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    # 执行查询
    result = await db.execute(query)
    rows = result.all()
    
    # 格式化结果
    logs_with_username = []
    for log, username in rows:
        log_dict = {
            "id": log.id,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "category": log.category,
            "operation": log.operation,
            "title": log.title,
            "content": log.content,
            "status": log.status,
            "data": log.data,
            "user_id": log.user_id,
            "username": username,
            "user_ip": log.user_ip,
            "created_at": log.created_at
        }
        logs_with_username.append(log_dict)
    
    return logs_with_username


async def get_log(db: AsyncSession, log_id: int) -> Optional[Log]:
    """根据ID获取日志详情"""
    result = await db.execute(select(Log).where(Log.id == log_id))
    return result.scalars().first()


async def get_logs_count(
    db: AsyncSession,
    *,
    filter_params: Optional[LogFilter] = None
) -> int:
    """获取日志总数"""
    # 构建查询
    query = select(Log)
    
    # 应用过滤条件
    if filter_params:
        conditions = []
        
        if filter_params.entity_type:
            conditions.append(Log.entity_type == filter_params.entity_type)
        
        if filter_params.entity_id:
            conditions.append(Log.entity_id == filter_params.entity_id)
            
        if filter_params.category:
            conditions.append(Log.category == filter_params.category)
            
        if filter_params.operation:
            conditions.append(Log.operation == filter_params.operation)
            
        if filter_params.status:
            conditions.append(Log.status == filter_params.status)
            
        if filter_params.user_id:
            conditions.append(Log.user_id == filter_params.user_id)
            
        if filter_params.start_date:
            conditions.append(Log.created_at >= filter_params.start_date)
            
        if filter_params.end_date:
            conditions.append(Log.created_at <= filter_params.end_date)
            
        if conditions:
            query = query.where(and_(*conditions))
    
    # 执行查询
    result = await db.execute(query)
    return len(result.all()) 