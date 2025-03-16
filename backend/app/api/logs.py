from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_active_user
from app.core.logs import get_logs, get_log, get_logs_count
from app.schemas.log import Log, LogFilter
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Dict])
async def read_logs(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    category: Optional[str] = None,
    operation: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Any:
    """
    获取日志列表，支持各种过滤条件
    """
    # 允许所有已登录用户访问日志
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="没有足够的权限")
    
    # 构建过滤参数
    filter_params = LogFilter(
        entity_type=entity_type,
        entity_id=entity_id,
        category=category,
        operation=operation,
        status=status,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    # 获取日志列表
    logs = await get_logs(db=db, skip=skip, limit=limit, filter_params=filter_params)
    
    return logs


@router.get("/count")
async def read_logs_count(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    category: Optional[str] = None,
    operation: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Any:
    """
    获取日志总数
    """
    # 允许所有已登录用户访问日志
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="没有足够的权限")
    
    # 构建过滤参数
    filter_params = LogFilter(
        entity_type=entity_type,
        entity_id=entity_id,
        category=category,
        operation=operation,
        status=status,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    # 获取日志总数
    count = await get_logs_count(db=db, filter_params=filter_params)
    
    return {"total": count}


@router.get("/{log_id}", response_model=Dict)
async def read_log(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    log_id: int,
) -> Any:
    """
    获取日志详情
    """
    # 允许所有已登录用户访问日志
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="没有足够的权限")
    
    # 获取日志详情
    log = await get_log(db=db, log_id=log_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"ID为{log_id}的日志不存在")
    
    # 获取用户名
    username = None
    if log.user_id:
        result = await db.execute(select(User).where(User.id == log.user_id))
        user = result.scalars().first()
        if user:
            username = user.username
    
    # 构建返回数据
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
    
    return log_dict 