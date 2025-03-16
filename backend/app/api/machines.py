from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.machines import MachineManager
from app.db.database import get_db
from app.schemas.machine import (
    Machine, MachineCreate, MachineUpdate, MachineStatus, 
    MachineLog, DeployRequest, LogRequest, OperationResponse,
    MachineMetrics
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Machine])
async def list_machines(
    skip: int = Query(0, description="跳过的记录数"),
    limit: int = Query(100, description="返回的最大记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取机器列表"""
    machines = await MachineManager.get_machines(db, skip=skip, limit=limit)
    return machines

@router.post("/", response_model=Machine)
async def create_machine(
    machine: MachineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新机器"""
    # 检查同名机器是否已存在
    existing_machine = await MachineManager.get_machine_by_name(db, machine.name)
    if existing_machine:
        raise HTTPException(status_code=400, detail="同名机器已存在")
    
    return await MachineManager.create_machine(db, machine)

@router.get("/{machine_id}", response_model=Machine)
async def get_machine(
    machine_id: int = Path(..., description="机器ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取机器详情"""
    machine = await MachineManager.get_machine(db, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="机器不存在")
    return machine

@router.put("/{machine_id}", response_model=Machine)
async def update_machine(
    machine_data: MachineUpdate,
    machine_id: int = Path(..., description="机器ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新机器信息"""
    updated_machine = await MachineManager.update_machine(db, machine_id, machine_data)
    if not updated_machine:
        raise HTTPException(status_code=404, detail="机器不存在")
    return updated_machine

@router.delete("/{machine_id}", response_model=OperationResponse)
async def delete_machine(
    machine_id: int = Path(..., description="机器ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除机器"""
    success = await MachineManager.delete_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=404, detail="机器不存在")
    return {"success": True, "message": "机器已删除"}

@router.post("/{machine_id}/check", response_model=MachineStatus)
async def check_machine_status(
    check_data: dict = None,
    machine_id: int = Path(..., description="机器ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查机器状态"""
    logger = logging.getLogger(__name__)
    
    # 获取机器信息并记录日志
    db_machine = await MachineManager.get_machine(db, machine_id)
    if db_machine:
        logger.info(f"检查机器状态: {db_machine.name}, 使用SSH密钥: {bool(db_machine.key_file)}")
    
    success, status, error = await MachineManager.check_machine_status(db, machine_id)
    if not success:
        logger.error(f"检查状态失败: {error}")
        raise HTTPException(status_code=400, detail=error)
    return status

@router.post("/{machine_id}/deploy", response_model=OperationResponse)
async def deploy_project(
    deploy_data: DeployRequest,
    machine_id: int = Path(..., description="机器ID"),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """部署项目到机器"""
    if background_tasks:
        # 后台任务部署
        background_tasks.add_task(
            MachineManager.deploy_project, 
            db,
            machine_id
        )
        return {"success": True, "message": "部署任务已开始，请稍后查看状态"}
    else:
        # 同步部署
        success, message = await MachineManager.deploy_project(db, machine_id)
        return {"success": success, "message": message}

@router.post("/{machine_id}/start", response_model=OperationResponse)
async def start_project(
    start_data: dict = None,
    machine_id: int = Path(..., description="机器ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动远程项目"""
    success, message = await MachineManager.start_project(db, machine_id)
    return {"success": success, "message": message}

@router.post("/{machine_id}/stop", response_model=OperationResponse)
async def stop_project(
    stop_data: dict = None,
    machine_id: int = Path(..., description="机器ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """停止远程项目"""
    success, message = await MachineManager.stop_project(db, machine_id)
    return {"success": success, "message": message}

@router.post("/{machine_id}/logs", response_model=OperationResponse)
async def get_logs(
    log_request: LogRequest,
    machine_id: int = Path(..., description="机器ID"),
    lines: int = Query(100, description="返回的日志行数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取远程日志"""
    success, logs, error = await MachineManager.get_logs(
        db, 
        machine_id, 
        log_request.log_type,
        lines=lines
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"success": True, "message": logs}

@router.get("/{machine_id}/metrics", response_model=MachineMetrics)
async def get_machine_metrics(
    machine_id: int = Path(..., description="机器ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取机器监控指标"""
    # 检查机器是否存在
    machine = await MachineManager.get_machine(db, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="机器不存在")
    
    # 获取监控指标
    success, metrics, error = await MachineManager.get_machine_metrics(db, machine_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return metrics 