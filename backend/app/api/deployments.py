from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging
import os
import subprocess
import shutil
from datetime import datetime
from sqlalchemy.orm import selectinload
import sys
import traceback
import asyncio
import base64
import magic

from app.api.deps import get_db
from app.models.project import Deployment, Project
from app.models.machine import Machine
from app.schemas.deployment import DeploymentCreate, DeploymentResponse, DeployInfo, DeploymentUpdate
from app.api.deps import get_current_user
from app.utils.ssh import SSHClient
from app.db.database import async_session_factory
from app.models.user import User
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# 1. 先定义固定路径路由
@router.get("/", response_model=List[DeploymentResponse])
async def get_all_deployments(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filter by deployment status")
):
    """获取所有部署记录"""
    query = select(Deployment).options(
        selectinload(Deployment.project),
        selectinload(Deployment.machine)
    )
    if status:
        query = query.filter(Deployment.status == status)
    query = query.order_by(Deployment.created_at.desc())
    result = await db.execute(query)
    deployments = result.scalars().all()
    return deployments

@router.post("/", response_model=DeploymentResponse)
async def create_deployment(
    deployment: DeploymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建项目与机器的关联并设置初始部署状态"""
    # 检查项目是否存在
    result = await db.execute(select(Project).filter(Project.id == deployment.project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查机器是否存在
    result = await db.execute(select(Machine).filter(Machine.id == deployment.machine_id))
    machine = result.scalars().first()
    if not machine:
        raise HTTPException(status_code=404, detail="目标机器不存在")
    
    # 检查是否已存在关联
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.project), selectinload(Deployment.machine))
        .filter(
            Deployment.project_id == deployment.project_id,
            Deployment.machine_id == deployment.machine_id
        )
    )
    existing = result.scalars().first()
    
    if existing:
        # 如果已存在关联，返回现有记录
        return existing
    
    # 创建新的关联部署记录
    new_deployment = Deployment(
        project_id=deployment.project_id,
        machine_id=deployment.machine_id,
        environment=deployment.environment,
        deploy_path=deployment.deploy_path,
        status="not_deployed",
        deployed_at=None  # 确保部署时间为空
    )
    
    db.add(new_deployment)
    await db.commit()
    await db.refresh(new_deployment)
    
    # 在返回前加载关联对象
    new_deployment.project = project
    new_deployment.machine = machine
    
    return new_deployment

# 2. 定义按具体前缀的路由，如 /by-project/ 和 /by-machine/
@router.get("/by-project/{project_id}", response_model=List[DeploymentResponse])
async def get_project_deployments(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取项目的所有部署记录"""
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.project), selectinload(Deployment.machine))
        .filter(Deployment.project_id == project_id)
    )
    deployments = result.scalars().all()
    return deployments

@router.get("/by-machine/{machine_id}", response_model=List[DeploymentResponse])
async def get_machine_deployments(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取机器上的所有部署记录"""
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.project), selectinload(Deployment.machine))
        .filter(Deployment.machine_id == machine_id)
    )
    deployments = result.scalars().all()
    return deployments

# 3. 定义所有带有id和子路径的特定操作路由
@router.post("/{deployment_id}/deploy", response_model=DeploymentResponse)
async def start_deployment(
    deployment_id: int,
    deploy_info: DeployInfo,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """部署应用"""
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.project), selectinload(Deployment.machine))
        .filter(Deployment.id == deployment_id)
    )
    deployment = result.scalars().first()
    if not deployment:
        raise HTTPException(status_code=404, detail="部署记录未找到")
    
    # 更新部署信息
    deployment.status = "pending"
    deployment.deploy_path = deploy_info.deploy_path
    deployment.environment = deploy_info.environment
    deployment.deployed_at = datetime.now()
    await db.commit()
    await db.refresh(deployment)
    
    # 在后台开始部署流程
    background_tasks.add_task(
        run_deployment,
        deployment_id=deployment.id,
        db=db
    )
    
    return deployment

@router.post("/{deployment_id}/redeploy", response_model=DeploymentResponse)
async def redeploy_project(
    deployment_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """重新部署应用"""
    logger.info(f"接收到重新部署请求，部署ID: {deployment_id}")
    
    try:
        result = await db.execute(
            select(Deployment)
            .options(selectinload(Deployment.project), selectinload(Deployment.machine))
            .filter(Deployment.id == deployment_id)
        )
        deployment = result.scalars().first()
        
        if not deployment:
            logger.error(f"部署记录未找到，部署ID: {deployment_id}")
            raise HTTPException(status_code=404, detail="部署记录未找到")
        
        logger.info(f"找到部署记录: {deployment.id}, 项目ID: {deployment.project_id}, 机器ID: {deployment.machine_id}, 路径: {deployment.deploy_path}")
        
        # 如果部署路径为空，设置一个默认的部署路径
        if not deployment.deploy_path:
            logger.info(f"部署路径为空，将设置默认路径")
            
            # 获取项目信息
            project_result = await db.execute(select(Project).filter(Project.id == deployment.project_id))
            project = project_result.scalars().first()
            
            if not project:
                logger.error(f"项目不存在，项目ID: {deployment.project_id}")
                raise HTTPException(status_code=404, detail="项目不存在")
            
            logger.info(f"找到项目: {project.name}")
            
            # 获取机器信息
            machine_result = await db.execute(select(Machine).filter(Machine.id == deployment.machine_id))
            machine = machine_result.scalars().first()
            
            if not machine:
                logger.error(f"机器不存在，机器ID: {deployment.machine_id}")
                raise HTTPException(status_code=404, detail="机器不存在")
            
            logger.info(f"找到机器: {machine.name}, 主机: {machine.host}")
            
            # 根据机器IP判断是否为Windows路径
            is_windows = False
            if machine.host.startswith('192.168.') or machine.host == 'localhost' or machine.host == '127.0.0.1':
                # 本地网络/本机可能是Windows
                is_windows = True
                logger.info("检测到本地/内网机器，使用Windows路径格式")
            
            # 设置默认的部署路径
            if is_windows:
                deployment.deploy_path = f"D:\\projects\\{project.name}"
            else:
                deployment.deploy_path = f"/root/projects/{project.name}"
            
            logger.info(f"设置默认部署路径: {deployment.deploy_path}")
        
        # 更新部署状态
        deployment.status = "pending"
        deployment.deployed_at = datetime.now()
        await db.commit()
        await db.refresh(deployment)
        
        logger.info(f"成功更新部署状态为pending，准备开始部署流程")
        
        # 在后台开始部署流程
        background_tasks.add_task(
            run_deployment,
            deployment_id=deployment.id,
            db=db
        )
        
        return deployment
    except Exception as e:
        logger.exception(f"重新部署过程中发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重新部署过程中发生错误: {str(e)}")

@router.get("/{deployment_id}/logs", response_model=dict)
async def get_deployment_logs(
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取部署日志"""
    result = await db.execute(select(Deployment).filter(Deployment.id == deployment_id))
    deployment = result.scalars().first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="部署记录未找到")
    
    return {"log": deployment.log or "暂无部署日志"}

@router.post("/{deployment_id}/start", response_model=DeploymentResponse)
async def start_application(
    deployment_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """启动应用"""
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.project), selectinload(Deployment.machine))
        .filter(Deployment.id == deployment_id)
    )
    deployment = result.scalars().first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="部署记录未找到")
    
    if deployment.status != "success":
        raise HTTPException(status_code=400, detail="只有成功部署的应用才能启动")
    
    # 后台任务启动应用
    background_tasks.add_task(start_application_task, deployment_id, db)
    
    # 更新状态为正在启动
    deployment.status = "starting"
    await db.commit()
    await db.refresh(deployment)
    
    return deployment

@router.post("/{deployment_id}/stop", response_model=DeploymentResponse)
async def stop_application(
    deployment_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """停止应用"""
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.project), selectinload(Deployment.machine))
        .filter(Deployment.id == deployment_id)
    )
    deployment = result.scalars().first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="部署记录未找到")
    
    if deployment.status != "success" and deployment.status != "running":
        raise HTTPException(status_code=400, detail="只有成功部署或正在运行的应用才能停止")
    
    # 后台任务停止应用
    background_tasks.add_task(stop_application_task, deployment_id, db)
    
    # 更新状态为正在停止
    deployment.status = "stopping"
    await db.commit()
    await db.refresh(deployment)
    
    return deployment

@router.post("/{deployment_id}/sync", response_model=DeploymentResponse)
async def sync_project(
    deployment_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """同步项目代码（拉取最新代码但不启动）"""
    logger.info(f"接收到同步项目请求，部署ID: {deployment_id}")
    
    try:
        # 添加更详细的日志
        logger.info(f"开始查询部署记录，ID: {deployment_id}")
        
        result = await db.execute(
            select(Deployment)
            .options(selectinload(Deployment.project), selectinload(Deployment.machine))
            .filter(Deployment.id == deployment_id)
        )
        deployment = result.scalars().first()
        
        if not deployment:
            error_msg = f"部署记录未找到，部署ID: {deployment_id}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        
        logger.info(f"部署记录已找到: 项目ID={deployment.project_id}, 机器ID={deployment.machine_id}, 状态={deployment.status}")
        
        # 加载相关联的项目和机器信息
        if not hasattr(deployment, 'project') or not deployment.project:
            logger.info(f"加载项目信息，项目ID: {deployment.project_id}")
            project_result = await db.execute(select(Project).filter(Project.id == deployment.project_id))
            project = project_result.scalars().first()
            if not project:
                error_msg = f"关联的项目未找到，项目ID: {deployment.project_id}"
                logger.error(error_msg)
                raise HTTPException(status_code=404, detail=error_msg)
            deployment.project = project
        
        # 加载机器信息
        if not hasattr(deployment, 'machine') or not deployment.machine:
            logger.info(f"加载机器信息，机器ID: {deployment.machine_id}")
            machine_result = await db.execute(select(Machine).filter(Machine.id == deployment.machine_id))
            machine = machine_result.scalars().first()
            if not machine:
                error_msg = f"关联的机器未找到，机器ID: {deployment.machine_id}"
                logger.error(error_msg)
                raise HTTPException(status_code=404, detail=error_msg)
            deployment.machine = machine
        
        # 当部署路径为空时，设置默认路径
        if not deployment.deploy_path:
            logger.info(f"部署路径为空，设置默认路径到root目录")
            
            # 根据机器类型判断默认路径
            is_windows = False
            if deployment.machine.host.startswith('192.168.') or deployment.machine.host == 'localhost' or deployment.machine.host == '127.0.0.1':
                is_windows = True
                logger.info("检测到本地/内网机器，可能是Windows环境")
            
            # 设置默认路径
            if is_windows:
                deployment.deploy_path = f"D:\\root\\projects\\{deployment.project.name}"
                logger.info(f"设置默认Windows路径: {deployment.deploy_path}")
            else:
                deployment.deploy_path = f"/root/projects/{deployment.project.name}"
                logger.info(f"设置默认Linux路径: {deployment.deploy_path}")
            
            # 保存更新后的部署路径
            await db.commit()
            logger.info(f"成功更新部署路径: {deployment.deploy_path}")
        
        logger.info(f"更新部署状态为'syncing'")
        # 更新状态为同步中
        deployment.status = "syncing"
        await db.commit()
        await db.refresh(deployment)
        
        logger.info(f"启动后台同步任务，部署ID: {deployment_id}")
        # 在后台执行同步操作
        background_tasks.add_task(
            sync_project_task,
            deployment_id=deployment.id,
            db=db
        )
        
        return deployment
    except HTTPException:
        # 重新抛出HTTP异常，保留原始状态码
        raise
    except Exception as e:
        error_msg = f"同步项目过程中发生错误: {str(e)}"
        logger.exception(error_msg)
        # 尝试更新部署状态为失败
        try:
            if 'deployment' in locals() and deployment:
                deployment.status = "sync_failed"
                deployment.log = (deployment.log or "") + f"\n\n[{datetime.now()}] 同步失败：\n{str(e)}"
                await db.commit()
        except Exception as db_error:
            logger.error(f"更新部署状态失败: {str(db_error)}")
        
        raise HTTPException(status_code=500, detail=error_msg)

# 4. 最后定义通用的id参数路由
@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取单个部署记录"""
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.project), selectinload(Deployment.machine))
        .filter(Deployment.id == deployment_id)
    )
    deployment = result.scalars().first()
    if not deployment:
        raise HTTPException(status_code=404, detail="部署记录未找到")
    return deployment

@router.delete("/{deployment_id}", response_model=dict)
async def delete_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除部署关联"""
    result = await db.execute(select(Deployment).filter(Deployment.id == deployment_id))
    deployment = result.scalars().first()
    if not deployment:
        raise HTTPException(status_code=404, detail="部署记录未找到")
    
    await db.delete(deployment)
    await db.commit()
    
    return {"message": "部署关联已删除"}

@router.get("/{deployment_id}/files", response_model=dict)
async def get_deployment_files(
    deployment_id: int,
    path: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取部署目录下的文件列表
    """
    try:
        # 获取部署信息
        deployment = await get_deployment_or_404(db, deployment_id, current_user)
        
        # 获取部署路径
        deploy_path = deployment.deploy_path
        if not deploy_path:
            # 使用默认路径
            if hasattr(settings, 'PROJECTS_DIR'):
                deploy_path = os.path.join(settings.PROJECTS_DIR, f"deployment_{deployment_id}")
                logger.info(f"使用默认部署路径: {deploy_path}")
            else:
                # 尝试获取项目根目录
                try:
                    base_dir = settings.BASE_DIR
                    deploy_path = os.path.join(base_dir, "deployments", f"deployment_{deployment_id}")
                    logger.info(f"使用备选部署路径: {deploy_path}")
                except:
                    # 如果无法获取项目根目录，使用当前目录
                    deploy_path = os.path.join(os.getcwd(), "deployments", f"deployment_{deployment_id}")
                    logger.info(f"使用当前工作目录作为部署路径: {deploy_path}")
        
        logger.info(f"获取部署(ID={deployment_id})文件列表，路径: {path}，完整路径: {deploy_path}")
        
        # 构建完整路径
        full_path = os.path.join(deploy_path, path)
        
        # 确保路径存在
        if not os.path.exists(full_path):
            logger.warning(f"路径不存在: {full_path}")
            
            # 如果是根路径不存在，自动创建
            if not path and not os.path.exists(deploy_path):
                logger.info(f"尝试创建根部署目录: {deploy_path}")
                try:
                    os.makedirs(deploy_path, exist_ok=True)
                    logger.info(f"成功创建部署目录: {deploy_path}")
                except Exception as e:
                    logger.error(f"创建部署目录失败: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"无法创建部署目录: {str(e)}")
                
                # 再次检查路径是否存在
                if os.path.exists(full_path):
                    logger.info(f"成功创建并访问部署目录: {full_path}")
                else:
                    raise HTTPException(status_code=404, detail=f"路径不存在: {path}")
            else:
                raise HTTPException(status_code=404, detail=f"路径不存在: {path}")
        
        # 确保路径是部署目录的子目录（防止目录遍历攻击）
        try:
            real_deployment_path = os.path.realpath(deploy_path)
            real_full_path = os.path.realpath(full_path)
            if not real_full_path.startswith(real_deployment_path):
                logger.warning(f"尝试访问部署目录外的路径: {real_full_path}")
                raise HTTPException(status_code=403, detail=f"路径越界访问")
        except Exception as e:
            logger.error(f"路径验证错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"路径验证错误: {str(e)}")
        
        # 如果不是目录，返回错误
        if not os.path.isdir(full_path):
            logger.warning(f"路径不是目录: {full_path}")
            raise HTTPException(status_code=400, detail=f"路径不是目录: {path}")
        
        try:
            # 获取目录内容
            directories = []
            files = []
            
            logger.info(f"扫描目录内容: {full_path}")
            with os.scandir(full_path) as entries:
                for entry in entries:
                    # 基本信息
                    entry_info = {
                        "name": entry.name,
                    }
                    
                    # 根据是否为目录添加不同字段
                    if entry.is_dir():
                        directories.append(entry_info)
                    else:
                        # 文件信息
                        stat_info = entry.stat()
                        entry_info.update({
                            "size": stat_info.st_size,
                            "last_modified": int(stat_info.st_mtime)
                        })
                        files.append(entry_info)
            
            # 对结果进行排序
            directories.sort(key=lambda x: x["name"])
            files.sort(key=lambda x: x["name"])
            
            result = {
                "directories": directories,
                "files": files,
                "path": path
            }
            
            logger.info(f"成功获取目录内容: {len(directories)}个目录, {len(files)}个文件")
            return result
        except Exception as e:
            logger.exception(f"获取文件列表出错: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取文件列表出错: {str(e)}")
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        # 记录其他异常并转换为HTTP 500错误
        logger.exception(f"处理文件列表请求时发生未处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/{deployment_id}/file", response_model=dict)
async def get_file_content(
    deployment_id: int,
    path: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取部署中的文件内容
    """
    try:
        # 获取部署信息
        deployment = await get_deployment_or_404(db, deployment_id, current_user)
        
        # 获取部署路径
        deploy_path = deployment.deploy_path
        if not deploy_path:
            # 使用默认路径
            if hasattr(settings, 'PROJECTS_DIR'):
                deploy_path = os.path.join(settings.PROJECTS_DIR, f"deployment_{deployment_id}")
                logger.info(f"使用默认部署路径: {deploy_path}")
            else:
                # 尝试获取项目根目录
                try:
                    base_dir = settings.BASE_DIR
                    deploy_path = os.path.join(base_dir, "deployments", f"deployment_{deployment_id}")
                    logger.info(f"使用备选部署路径: {deploy_path}")
                except:
                    # 如果无法获取项目根目录，使用当前目录
                    deploy_path = os.path.join(os.getcwd(), "deployments", f"deployment_{deployment_id}")
                    logger.info(f"使用当前工作目录作为部署路径: {deploy_path}")
                    
        logger.info(f"获取部署(ID={deployment_id})文件内容，路径: {path}")
                
        # 构建完整路径
        full_path = os.path.join(deploy_path, path)
        
        # 确保路径存在
        if not os.path.exists(full_path):
            logger.warning(f"文件路径不存在: {full_path}")
            raise HTTPException(status_code=404, detail=f"文件不存在: {path}")
        
        # 确保路径是部署目录的子目录（防止目录遍历攻击）
        try:
            real_deployment_path = os.path.realpath(deploy_path)
            real_full_path = os.path.realpath(full_path)
            if not real_full_path.startswith(real_deployment_path):
                logger.warning(f"尝试访问部署目录外的文件: {real_full_path}")
                raise HTTPException(status_code=403, detail=f"不允许访问部署目录外的文件")
        except Exception as e:
            logger.error(f"路径验证错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"路径验证错误: {str(e)}")
        
        # 如果是目录，返回错误
        if os.path.isdir(full_path):
            logger.warning(f"请求的路径是目录: {full_path}")
            raise HTTPException(status_code=400, detail=f"路径是目录，不是文件: {path}")
        
        # 获取文件大小
        file_size = os.path.getsize(full_path)
        
        # 如果文件过大，返回错误
        if file_size > 10 * 1024 * 1024:  # 10MB
            logger.warning(f"文件过大: {full_path}, 大小: {file_size / 1024 / 1024:.2f}MB")
            raise HTTPException(status_code=400, detail=f"文件过大，不能查看大于10MB的文件")
        
        # 检查文件类型
        is_binary = False
        try:
            # 首先尝试使用python-magic库
            try:
                import magic
                file_type = magic.from_file(full_path, mime=True)
                logger.info(f"检测到文件MIME类型: {file_type}")
                is_binary = not file_type.startswith(('text/', 'application/json', 'application/xml', 
                                                    'application/javascript', 'application/x-yaml'))
                if is_binary:
                    logger.info(f"通过MIME类型检测为二进制文件: {file_type}")
            except (ImportError, Exception) as e:
                logger.warning(f"python-magic库不可用或发生错误: {str(e)}，使用备用方法检测")
                # 备用方法：通过文件内容和扩展名检测
                with open(full_path, 'rb') as f:
                    chunk = f.read(4096)
                    # 检查是否包含空字节，这通常表示二进制文件
                    if b'\0' in chunk:
                        is_binary = True
                        logger.info("通过空字节检测为二进制文件")
                    # 检查常见二进制文件格式的魔术数字
                    if chunk.startswith((
                        b'\x89PNG',  # PNG
                        b'\xff\xd8\xff',  # JPEG
                        b'GIF',  # GIF
                        b'PK',  # ZIP
                        b'BM',  # BMP
                        b'\x7fELF',  # ELF
                        b'%PDF',  # PDF
                        b'\xd0\xcf\x11\xe0',  # MS Office
                    )):
                        is_binary = True
                        logger.info("通过魔术数字检测为二进制文件")
                
                # 也检查文件扩展名
                file_extension = os.path.splitext(full_path)[1].lower()
                binary_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', 
                                    '.exe', '.dll', '.so', '.pdf', '.zip', '.rar', 
                                    '.7z', '.tar', '.gz', '.bin', '.dat'}
                if file_extension in binary_extensions:
                    is_binary = True
                    logger.info(f"通过文件扩展名检测为二进制文件: {file_extension}")
        except Exception as e:
            logger.error(f"检测文件类型时出错: {str(e)}")
        
        # 如果是二进制文件，返回错误或仅返回基本信息
        if is_binary:
            logger.warning(f"请求的文件是二进制文件: {full_path}")
            return {
                "path": path,
                "size": file_size,
                "is_binary": True,
                "content": None,
                "message": "二进制文件不支持直接查看"
            }
        
        # 读取文件内容
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            logger.info(f"成功读取文件内容: {path}, 大小: {len(content)} 字符")
            return {
                "path": path,
                "content": content,
                "size": file_size,
                "is_binary": False
            }
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试使用其他编码
            try:
                with open(full_path, 'r', encoding='gbk') as f:
                    content = f.read()
                    
                logger.info(f"使用GBK编码成功读取文件内容: {path}")
                return {
                    "path": path,
                    "content": content,
                    "size": file_size,
                    "is_binary": False,
                    "encoding": "gbk"
                }
            except:
                logger.warning(f"无法解码文件内容，可能是二进制文件: {full_path}")
                return {
                    "path": path,
                    "size": file_size,
                    "is_binary": True,
                    "content": None,
                    "message": "无法解码文件内容，可能是二进制文件"
                }
        except Exception as e:
            logger.exception(f"获取文件内容出错: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取文件内容出错: {str(e)}")
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        # 记录其他异常并转换为HTTP 500错误
        logger.exception(f"处理文件内容请求时发生未处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

# 保留原有的辅助函数和后台任务函数
async def run_deployment(deployment_id: int, db: AsyncSession):
    """执行实际的部署流程"""
    # 获取部署信息
    result = await db.execute(select(Deployment).filter(Deployment.id == deployment_id))
    deployment = result.scalars().first()
    if not deployment:
        logger.error(f"部署ID {deployment_id} 不存在")
        return
    
    result = await db.execute(select(Project).filter(Project.id == deployment.project_id))
    project = result.scalars().first()
    
    result = await db.execute(select(Machine).filter(Machine.id == deployment.machine_id))
    machine = result.scalars().first()
    
    if not project or not machine:
        logger.error(f"项目或机器不存在，部署ID: {deployment_id}")
        await update_deployment_status(db, deployment, "failed", "项目或机器不存在")
        return
    
    if not deployment.deploy_path:
        logger.error(f"缺少部署路径，部署ID: {deployment_id}")
        await update_deployment_status(db, deployment, "failed", "缺少部署路径")
        return
    
    try:
        # 连接到远程服务器
        ssh = SSHClient(
            host=machine.host,
            port=machine.port,
            username=machine.username,
            password=machine.password,
            key_file=machine.key_file
        )
        
        # 部署日志
        log_messages = []
        log_messages.append(f"开始部署项目 {project.name} 到 {machine.name} ({machine.host})")
        
        # 确保目标路径存在
        await ssh.connect()
        await ssh.execute_command(f"mkdir -p {deployment.deploy_path}")
        log_messages.append(f"创建目标目录: {deployment.deploy_path}")
        
        # 克隆或拉取代码
        if project.repository_type == "git":
            # 检查目标目录是否已经是Git仓库
            exit_code, repo_check, _ = await ssh.execute_command(f"[ -d {deployment.deploy_path}/.git ] && echo 'EXISTS' || echo 'NOT_EXISTS'")
            
            if "EXISTS" in repo_check:
                # 已存在Git仓库，执行pull
                log_messages.append("检测到现有Git仓库，执行更新")
                exit_code, result, _ = await ssh.execute_command(f"cd {deployment.deploy_path} && git pull")
            else:
                # 不存在Git仓库，执行clone
                log_messages.append("未检测到现有Git仓库，执行克隆")
                exit_code, result, _ = await ssh.execute_command(f"git clone {project.repository_url} {deployment.deploy_path}")
                
            log_messages.append(f"Git操作结果: {result}")
        else:
            # 本地项目，使用sftp传输
            log_messages.append("本地项目，准备文件传输")
            # TODO: 实现本地项目文件传输逻辑
        
        # 部署后的项目初始化和启动
        if project.project_type == "frontend":
            log_messages.append("前端项目，执行构建")
            await ssh.execute_command(f"cd {deployment.deploy_path} && npm install")
            exit_code, build_result, _ = await ssh.execute_command(f"cd {deployment.deploy_path} && npm run build")
            log_messages.append(f"构建结果: {build_result}")
        elif project.project_type == "backend":
            log_messages.append("后端项目，执行依赖安装")
            await ssh.execute_command(f"cd {deployment.deploy_path} && pip install -r requirements.txt")
            # 可能需要启动服务
            # await ssh.execute_command(f"cd {deployment.deploy_path} && python app.py &")
        else:  # fullstack
            log_messages.append("全栈项目，执行前后端构建")
            if os.path.exists(f"{deployment.deploy_path}/frontend"):
                await ssh.execute_command(f"cd {deployment.deploy_path}/frontend && npm install")
                await ssh.execute_command(f"cd {deployment.deploy_path}/frontend && npm run build")
            if os.path.exists(f"{deployment.deploy_path}/backend"):
                await ssh.execute_command(f"cd {deployment.deploy_path}/backend && pip install -r requirements.txt")
        
        # 部署完成
        log_messages.append("部署完成")
        await ssh.close()
        await update_deployment_status(db, deployment, "success", "\n".join(log_messages))
        
    except Exception as e:
        logger.exception(f"部署失败: {str(e)}")
        await update_deployment_status(db, deployment, "failed", f"部署失败: {str(e)}")

async def update_deployment_status(db: AsyncSession, deployment: Deployment, status: str, log: str = None):
    """更新部署状态"""
    deployment.status = status
    deployment.log = log
    deployment.updated_at = datetime.now()
    await db.commit()

async def sync_project_task(deployment_id: int, db: AsyncSession):
    """后台任务：同步项目代码"""
    logger.info(f"开始后台同步任务，部署ID：{deployment_id}")
    
    # 使用新的会话以确保数据库连接可用
    try:
        async with async_session_factory() as session:
            # 开始事务
            async with session.begin():
                logger.info(f"查询部署信息，ID：{deployment_id}")
                result = await session.execute(
                    select(Deployment)
                    .options(selectinload(Deployment.project), selectinload(Deployment.machine))
                    .filter(Deployment.id == deployment_id)
                )
                deployment = result.scalars().first()
                
                if not deployment:
                    logger.error(f"同步项目任务：找不到部署ID {deployment_id}")
                    return
                
                logger.info(f"成功获取部署信息: 项目ID={deployment.project_id}, 机器ID={deployment.machine_id}")
                
                # 获取必要信息
                project = deployment.project
                machine = deployment.machine
                deploy_path = deployment.deploy_path
                
                if not project or not machine:
                    error_msg = f"项目或机器信息缺失，无法继续同步"
                    logger.error(error_msg)
                    deployment.status = "sync_failed"
                    deployment.log = (deployment.log or "") + f"\n\n[{datetime.now()}] 同步失败：\n{error_msg}"
                    await session.commit()
                    return
                
                log_messages = []
                log_messages.append(f"[{datetime.now()}] 开始同步项目: {project.name}")
                
                try:
                    # 创建SSH客户端
                    logger.info(f"创建SSH连接到机器: {machine.host}")
                    ssh_client = SSHClient(
                        host=machine.host,
                        port=machine.port,
                        username=machine.username,
                        password=machine.password if hasattr(machine, 'password') and machine.password else None,
                        key_file=machine.key_file if hasattr(machine, 'key_file') and machine.key_file else None
                    )
                    
                    # 连接到服务器
                    try:
                        await ssh_client.connect()
                        logger.info(f"SSH连接成功: {machine.host}")
                    except Exception as ssh_error:
                        error_msg = f"SSH连接失败: {str(ssh_error)}"
                        logger.error(error_msg)
                        log_messages.append(error_msg)
                        raise Exception(error_msg)
                    
                    # 检查目录是否存在
                    logger.info(f"检查目标目录是否存在: {deploy_path}")
                    
                    # 改进的服务器系统类型检测方法
                    is_windows = False
                    try:
                        # 先尝试最可靠的检测方法 - 运行Windows特有命令
                        test_cmd = "cmd /c echo %OS%"
                        exit_status, stdout, stderr = await ssh_client.execute_command(test_cmd)
                        if exit_status == 0 and "Windows" in stdout:
                            is_windows = True
                            logger.info("检测到Windows服务器 (通过cmd测试)")
                        else:
                            # 尝试PowerShell命令
                            test_cmd = "powershell -Command \"echo $env:OS\""
                            exit_status, stdout, stderr = await ssh_client.execute_command(test_cmd)
                            if exit_status == 0 and "Windows" in stdout:
                                is_windows = True
                                logger.info("检测到Windows服务器 (通过PowerShell测试)")
                            else:
                                # 最后尝试获取系统类型
                                test_cmd = "uname -s"
                                exit_status, stdout, stderr = await ssh_client.execute_command(test_cmd)
                                if exit_status == 0 and ("Linux" in stdout or "Darwin" in stdout):
                                    is_windows = False
                                    logger.info(f"检测到Unix类系统: {stdout.strip()}")
                                else:
                                    # 如果无法确定，通过IP地址或机器设置推断
                                    if machine.host.startswith('192.168.') or machine.host == 'localhost' or machine.host == '127.0.0.1':
                                        # 本地机器，根据本地系统类型判断
                                        is_windows = os.name == 'nt'
                                        logger.info(f"通过本地系统类型推断为{'Windows' if is_windows else 'Linux'}")
                                    elif hasattr(machine, 'is_windows') and machine.is_windows is not None:
                                        # 如果机器对象有明确标记，使用该标记
                                        is_windows = machine.is_windows
                                        logger.info(f"通过机器设置检测为{'Windows' if is_windows else 'Linux'}")
                                    else:
                                        # 默认情况下假设为Linux
                                        is_windows = False
                                        logger.info("无法检测系统类型，默认为Linux服务器")
                    except Exception as e:
                        logger.warning(f"系统类型检测异常: {str(e)}，默认为Linux系统")
                        is_windows = False
                    
                    # 根据检测到的系统类型设置文件路径分隔符
                    path_separator = '\\' if is_windows else '/'
                    log_messages.append(f"检测到{'Windows' if is_windows else 'Linux'}服务器")
                    
                    # 根据服务器系统类型使用正确的命令
                    if is_windows:
                        check_dir_cmd = f"if exist {deploy_path} (echo EXISTS) else (echo NOT_EXISTS)"
                    else:
                        check_dir_cmd = f"if [ -d \"{deploy_path}\" ]; then echo 'EXISTS'; else echo 'NOT_EXISTS'; fi"
                    
                    exit_status, stdout, stderr = await ssh_client.execute_command(check_dir_cmd)
                    dir_check_result = stdout.strip()
                    log_messages.append(f"检查目录结果: {dir_check_result}")
                    
                    if "NOT_EXISTS" in dir_check_result:
                        log_messages.append(f"目标目录不存在，将创建目录: {deploy_path}")
                        logger.info(f"目标目录不存在，创建目录: {deploy_path}")
                        
                        # 创建目录命令
                        if is_windows:
                            mkdir_cmd = f"mkdir \"{deploy_path}\" 2>nul || echo 创建目录"
                        else:
                            mkdir_cmd = f"mkdir -p \"{deploy_path}\""
                        
                        exit_status, stdout, stderr = await ssh_client.execute_command(mkdir_cmd)
                        
                        if exit_status != 0:
                            error_msg = f"创建目录失败: {stderr}"
                            logger.error(error_msg)
                            log_messages.append(error_msg)
                            raise Exception(error_msg)
                        
                        log_messages.append(f"成功创建目录: {deploy_path}")
                        logger.info(f"成功创建目录: {deploy_path}")
                    
                    # 根据项目类型进行不同的同步操作
                    if project.repository_type == "git":
                        # Git项目，执行git pull
                        logger.info(f"检测为Git项目，准备执行git pull")
                        log_messages.append("Git项目，执行git pull")
                        
                        # 检查是否为git仓库
                        git_check_cmd = f"cd {deploy_path} && git rev-parse --is-inside-work-tree 2>/dev/null || echo 'NOT_GIT'"
                        exit_status, stdout, stderr = await ssh_client.execute_command(git_check_cmd)
                        git_check_result = stdout.strip()
                        
                        if "NOT_GIT" in git_check_result or exit_status != 0:
                            # 目录不是git仓库，需要执行clone操作
                            log_messages.append(f"目录 {deploy_path} 不是git仓库，将执行git clone")
                            logger.info(f"目录 {deploy_path} 不是git仓库，执行git clone")
                            
                            # 获取仓库URL
                            if not project.repository_url:
                                error_msg = f"项目没有设置Git仓库URL，无法克隆"
                                logger.error(error_msg)
                                log_messages.append(error_msg)
                                raise Exception(error_msg)
                            
                            # 清空目录内容（如果目录非空）
                            clear_cmd = f"rm -rf {deploy_path}/*"
                            if os.name == 'nt':  # Windows环境
                                clear_cmd = f"del /q /f {deploy_path}\\* 2>nul"
                            
                            await ssh_client.execute_command(clear_cmd)
                            log_messages.append(f"清空目录内容: {deploy_path}")
                            
                            # 执行git clone
                            clone_cmd = f"git clone {project.repository_url} {deploy_path}"
                            logger.info(f"执行git clone: {clone_cmd}")
                            log_messages.append(f"执行git clone: {project.repository_url} -> {deploy_path}")
                            
                            exit_status, stdout, stderr = await ssh_client.execute_command(clone_cmd)
                            
                            if exit_status != 0:
                                error_msg = f"Git clone失败: {stderr}"
                                logger.error(error_msg)
                                log_messages.append(error_msg)
                                raise Exception(error_msg)
                            
                            clone_result = stdout.strip()
                            logger.info(f"Git clone完成")
                            log_messages.append(f"Git clone结果: {clone_result}")
                            log_messages.append(f"成功克隆代码")
                        else:
                            # 目录是git仓库，执行git pull
                            logger.info(f"执行git pull操作")
                            pull_cmd = f"cd {deploy_path} && git pull"
                            exit_status, stdout, stderr = await ssh_client.execute_command(pull_cmd)
                            
                            if exit_status != 0:
                                error_msg = f"Git pull失败: {stderr}"
                                logger.error(error_msg)
                                log_messages.append(error_msg)
                                raise Exception(error_msg)
                            
                            pull_result = stdout.strip()
                            logger.info(f"Git pull完成: {pull_result}")
                            log_messages.append(f"Git pull结果: {pull_result}")
                            
                            # 检查是否有文件更新
                            if "Already up to date" in pull_result or "Already up-to-date" in pull_result:
                                log_messages.append("代码已是最新，无需更新")
                            else:
                                log_messages.append("成功拉取新代码")
                            
                            # 检查是否需要安装依赖
                            logger.info(f"检查项目依赖")
                            exit_status, stdout, stderr = await ssh_client.execute_command(f"ls {deploy_path}")
                            ls_result = stdout
                            
                            if "package.json" in ls_result:
                                log_messages.append("检测到package.json，执行npm install")
                                npm_cmd = f"cd {deploy_path} && npm install"
                                logger.info(f"执行npm install")
                                exit_status, stdout, stderr = await ssh_client.execute_command(npm_cmd)
                                
                                if exit_status != 0:
                                    log_messages.append(f"npm install警告: {stderr}")
                                else:
                                    log_messages.append("npm install完成")
                            
                            if "requirements.txt" in ls_result:
                                log_messages.append("检测到requirements.txt，执行pip install")
                                pip_cmd = f"cd {deploy_path} && pip install -r requirements.txt"
                                logger.info(f"执行pip install")
                                exit_status, stdout, stderr = await ssh_client.execute_command(pip_cmd)
                                
                                if exit_status != 0:
                                    log_messages.append(f"pip install警告: {stderr}")
                                else:
                                    log_messages.append("pip install完成")
                    else:
                        # 本地项目，改为逐个文件上传
                        logger.info(f"检测到本地项目，准备逐个文件上传")
                        log_messages.append("本地项目，准备文件上传")
                        
                        # 获取项目存储路径
                        project_storage_path = project.storage_path
                        if not project_storage_path:
                            error_msg = "项目存储路径为空，无法上传文件"
                            logger.error(error_msg)
                            log_messages.append(error_msg)
                            raise Exception(error_msg)
                        
                        logger.info(f"项目本地存储路径: {project_storage_path}")
                        log_messages.append(f"项目本地存储路径: {project_storage_path}")
                        
                        try:
                            # 使用SFTP逐个上传文件
                            logger.info(f"开始SFTP逐个文件传输")
                            log_messages.append("开始SFTP文件传输")
                            
                            # 打开SFTP会话
                            sftp = await ssh_client.open_sftp()
                            
                            # 确保目标目录存在
                            if is_windows:
                                mkdir_cmd = f"if not exist \"{deploy_path}\" mkdir \"{deploy_path}\""
                            else:
                                mkdir_cmd = f"mkdir -p \"{deploy_path}\""
                            await ssh_client.execute_command(mkdir_cmd)
                            
                            # 定义递归上传函数
                            async def upload_directory(local_dir, remote_dir):
                                logger.info(f"上传目录: {local_dir} -> {remote_dir}")
                                
                                # 确保远程目录存在
                                if is_windows:
                                    mkdir_cmd = f"if not exist \"{remote_dir}\" mkdir \"{remote_dir}\""
                                else:
                                    mkdir_cmd = f"mkdir -p \"{remote_dir}\""
                                await ssh_client.execute_command(mkdir_cmd)
                                
                                # 获取远程目录文件列表
                                try:
                                    remote_files = []
                                    if is_windows:
                                        ls_cmd = f"dir \"{remote_dir}\" /b"
                                        exit_status, stdout, stderr = await ssh_client.execute_command(ls_cmd)
                                        if exit_status == 0 and stdout.strip():
                                            remote_files = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
                                    else:
                                        # 在Linux上使用sftp的listdir更可靠
                                        try:
                                            remote_files = await asyncio.to_thread(sftp.listdir, remote_dir)
                                        except:
                                            # 如果目录还不存在或无法访问
                                            remote_files = []
                                    
                                    logger.debug(f"远程目录 {remote_dir} 中有 {len(remote_files)} 个文件")
                                except Exception as e:
                                    logger.warning(f"获取远程文件列表失败: {str(e)}，继续上传")
                                    remote_files = []

                                # 计数器
                                uploaded_count = 0
                                skipped_count = 0
                                
                                # 遍历本地目录中的文件和子目录
                                for item in os.listdir(local_dir):
                                    # 跳过隐藏文件和临时文件
                                    if item.startswith('.') or item.endswith('.tmp') or item.endswith('.temp'):
                                        continue
                                        
                                    local_path = os.path.join(local_dir, item)
                                    # 确保路径分隔符一致
                                    remote_path = os.path.join(remote_dir, item).replace('\\', '/')
                                    
                                    if os.path.isdir(local_path):
                                        # 递归处理子目录
                                        sub_uploaded, sub_skipped = await upload_directory(local_path, remote_path)
                                        uploaded_count += sub_uploaded
                                        skipped_count += sub_skipped
                                    else:
                                        # 上传文件
                                        try:
                                            # 检查文件是否已存在
                                            file_exists = item in remote_files
                                            
                                            if file_exists:
                                                # 如果存在，检查是否需要更新（这里可以添加时间戳或哈希值比较）
                                                local_mtime = os.path.getmtime(local_path)
                                                local_size = os.path.getsize(local_path)
                                                
                                                # 获取远程文件信息（通过SFTP的stat函数）
                                                try:
                                                    remote_stat = await asyncio.to_thread(sftp.stat, remote_path)
                                                    remote_mtime = remote_stat.st_mtime
                                                    remote_size = remote_stat.st_size
                                                    
                                                    # 如果文件大小和修改时间相同，则跳过
                                                    if abs(local_size - remote_size) < 10 and abs(local_mtime - remote_mtime) < 5:
                                                        logger.debug(f"跳过未修改文件: {item}")
                                                        skipped_count += 1
                                                        continue
                                                except:
                                                    # 无法获取远程文件信息，上传文件
                                                    pass
                                            
                                            # 上传文件
                                            logger.debug(f"上传文件: {local_path} -> {remote_path}")
                                            await asyncio.to_thread(sftp.put, local_path, remote_path)
                                            uploaded_count += 1
                                            
                                        except Exception as e:
                                            # 记录错误但继续上传其他文件
                                            logger.error(f"上传文件 {local_path} 失败: {str(e)}")
                                            log_messages.append(f"警告: 文件 {item} 上传失败: {str(e)}")
                                
                                return uploaded_count, skipped_count
                            
                            # 开始上传整个目录
                            uploaded_files, skipped_files = await upload_directory(project_storage_path, deploy_path)
                            
                            # 关闭SFTP会话
                            await asyncio.to_thread(sftp.close)
                            
                            logger.info(f"文件上传完成，上传: {uploaded_files}个，跳过: {skipped_files}个")
                            log_messages.append(f"文件上传完成，上传: {uploaded_files}个，跳过: {skipped_files}个")
                            
                        except Exception as e:
                            error_msg = f"文件上传过程中出错: {str(e)}"
                            logger.error(error_msg)
                            log_messages.append(error_msg)
                            raise Exception(error_msg)
                        
                    # 检查是否需要安装依赖
                    logger.info(f"检查项目依赖")
                    if is_windows:
                        ls_cmd = f"dir \"{deploy_path}\" /b"
                    else:
                        ls_cmd = f"ls -la \"{deploy_path}\""
                    
                    exit_status, stdout, stderr = await ssh_client.execute_command(ls_cmd)
                    ls_result = stdout
                    log_messages.append(f"目录内容: {ls_result}")
                    
                    if "package.json" in ls_result:
                        log_messages.append("检测到package.json，执行npm install")
                        npm_cmd = f"cd \"{deploy_path}\" && npm install"
                        logger.info(f"执行npm install")
                        exit_status, stdout, stderr = await ssh_client.execute_command(npm_cmd)
                        
                        if exit_status != 0:
                            log_messages.append(f"npm install警告: {stderr}")
                        else:
                            log_messages.append("npm install完成")
                    
                    if "requirements.txt" in ls_result:
                        log_messages.append("检测到requirements.txt，执行pip install")
                        pip_cmd = f"cd \"{deploy_path}\" && pip install -r requirements.txt"
                        logger.info(f"执行pip install")
                        exit_status, stdout, stderr = await ssh_client.execute_command(pip_cmd)
                        
                        if exit_status != 0:
                            log_messages.append(f"pip install警告: {stderr}")
                        else:
                            log_messages.append("pip install完成")
                    
                    # 同步完成，更新状态
                    log_messages.append(f"[{datetime.now()}] 同步完成")
                    logger.info(f"项目同步成功，部署ID: {deployment_id}")
                    deployment.status = "success"
                    deployment.log = (deployment.log or "") + "\n\n" + "\n".join(log_messages)
                    await session.commit()
                    
                except Exception as e:
                    # 处理同步过程中的错误
                    error_msg = f"同步过程失败: {str(e)}"
                    logger.exception(error_msg)
                    log_messages.append(f"[{datetime.now()}] 同步失败: {str(e)}")
                    
                    deployment.status = "sync_failed"
                    deployment.log = (deployment.log or "") + "\n\n" + "\n".join(log_messages)
                    await session.commit()
                
                finally:
                    # 确保关闭SSH连接
                    if 'ssh_client' in locals():
                        try:
                            await ssh_client.close()
                            logger.info("SSH连接已关闭")
                        except Exception as close_error:
                            logger.error(f"关闭SSH连接时出错: {str(close_error)}")
    
    except Exception as outer_error:
        # 处理数据库会话或其他外部错误
        logger.exception(f"同步任务外部错误: {str(outer_error)}")
        try:
            async with async_session_factory() as emergency_session:
                # 尝试更新部署状态
                result = await emergency_session.execute(select(Deployment).filter(Deployment.id == deployment_id))
                deployment = result.scalars().first()
                if deployment:
                    deployment.status = "sync_failed"
                    deployment.log = (deployment.log or "") + f"\n\n[{datetime.now()}] 同步任务严重错误: {str(outer_error)}"
                    await emergency_session.commit()
        except Exception as final_error:
            logger.critical(f"无法更新部署状态，最终错误: {str(final_error)}")

async def start_application_task(deployment_id: int, db: AsyncSession):
    """后台任务：启动应用"""
    async with db.begin():
        result = await db.execute(
            select(Deployment)
            .options(selectinload(Deployment.project), selectinload(Deployment.machine))
            .filter(Deployment.id == deployment_id)
        )
        deployment = result.scalars().first()
        
        if not deployment:
            logger.error(f"启动应用任务：找不到部署ID {deployment_id}")
            return
        
        try:
            # 获取必要信息
            machine = deployment.machine
            deploy_path = deployment.deploy_path
            
            # 创建SSH客户端
            ssh_client = SSHClient(
                host=machine.host,
                port=machine.port,
                username=machine.username,
                password=machine.password if hasattr(machine, 'password') else None
            )
            
            # 连接到服务器
            await ssh_client.connect()
            
            log_messages = []
            log_messages.append(f"[{datetime.now()}] 开始启动应用")
            
            # 检查目录是否存在
            # 根据服务器地址判断可能的操作系统
            is_windows = False
            try:
                test_cmd = "powershell -Command \"echo 'WINDOWS'\""
                exit_status, stdout, stderr = await ssh_client.execute_command(test_cmd)
                if "WINDOWS" in stdout:
                    is_windows = True
                    logger.info("检测到Windows服务器")
            except:
                logger.info("PowerShell命令失败，判断为Linux服务器")
            
            # 根据服务器系统类型使用正确的命令
            if is_windows:
                check_dir_cmd = f"if exist \"{deploy_path}\" (echo EXISTS) else (echo NOT_EXISTS)"
            else:
                check_dir_cmd = f"if [ -d \"{deploy_path}\" ]; then echo 'EXISTS'; else echo 'NOT_EXISTS'; fi"
            
            exit_status, stdout, stderr = await ssh_client.execute_command(check_dir_cmd)
            dir_check_result = stdout.strip()
            log_messages.append(f"检查目录结果: {dir_check_result}")
            
            if "NOT_EXISTS" in dir_check_result:
                log_messages.append(f"目标目录不存在，无法启动应用")
                # 更新部署状态为失败
                deployment.status = "start_failed"
                deployment.log = (deployment.log or "") + "\n\n" + "\n".join(log_messages)
                await db.commit()
                return
            
            # 检查启动脚本是否存在
            log_messages.append("检查启动脚本")
            
            # 根据系统类型确定可能的启动脚本名称
            possible_scripts = []
            if is_windows:
                possible_scripts = ["start_all.py","start.bat", "start_all.bat", "run.bat", "app.bat"]
            else:
                possible_scripts = ["start_all.py", "start.sh", "start_all.sh", "run.sh", "app.sh"]
            
            # 检查启动脚本
            found_script = None
            for script in possible_scripts:
                script_path = os.path.join(deploy_path, script).replace('\\', '/')
                if is_windows:
                    check_cmd = f"if exist \"{script_path}\" (echo EXISTS) else (echo NOT_EXISTS)"
                else:
                    check_cmd = f"[ -f \"{script_path}\" ] && echo 'EXISTS' || echo 'NOT_EXISTS'"
                
                exit_status, stdout, stderr = await ssh_client.execute_command(check_cmd)
                if "EXISTS" in stdout:
                    found_script = script
                    log_messages.append(f"找到启动脚本: {script}")
                    break
            
            # 优先检查start_all.py是否存在
            start_all_py_path = os.path.join(deploy_path, "start_all.py").replace('\\', '/')
            if is_windows:
                check_cmd = f"if exist \"{start_all_py_path}\" (echo EXISTS) else (echo NOT_EXISTS)"
            else:
                check_cmd = f"[ -f \"{start_all_py_path}\" ] && echo 'EXISTS' || echo 'NOT_EXISTS'"
            
            exit_status, stdout, stderr = await ssh_client.execute_command(check_cmd)
            has_start_all_py = "EXISTS" in stdout
            
            # 如果找到了启动脚本
            if has_start_all_py:
                # 优先使用start_all.py
                log_messages.append("优先使用start_all.py启动应用")
                if is_windows:
                    # 添加编码和端口参数
                    start_command = f"cd \"{deploy_path}\" && set PYTHONIOENCODING=utf-8 && python3 start_all.py --port=0"
                else:
                    # 添加编码和端口参数
                    start_command = f"cd \"{deploy_path}\" && export PYTHONIOENCODING=utf-8 && python3 start_all.py --port=0"
            elif found_script:
                script_path = os.path.join(deploy_path, found_script).replace('\\', '/')
                
                # 确保脚本有执行权限（仅Linux）
                if not is_windows and found_script.endswith('.sh'):
                    await ssh_client.execute_command(f"chmod +x \"{script_path}\"")
                
                if is_windows:
                    # 对于Python脚本特殊处理，添加编码设置
                    if found_script.endswith('.py'):
                        start_command = f"cd \"{deploy_path}\" && set PYTHONIOENCODING=utf-8 && python3 {found_script} --port=0"
                    else:
                        start_command = f"cd \"{deploy_path}\" && {found_script}"
                else:
                    # 对于Python脚本特殊处理，添加编码设置
                    if found_script.endswith('.py'):
                        start_command = f"cd \"{deploy_path}\" && export PYTHONIOENCODING=utf-8 && python3 {found_script} --port=0"
                    else:
                        start_command = f"cd \"{deploy_path}\" && ./{found_script}"
            
            # 执行启动命令
            log_messages.append(f"执行启动命令: {start_command}")
            start_result = await ssh_client.execute_command(start_command)
            log_messages.append(f"启动结果: {start_result}")
            
            # 检查启动是否成功（这里可以根据项目类型增加更多的检查）
            # 例如，可以尝试检查进程或HTTP端点是否可访问
            
            # 关闭连接
            await ssh_client.close()
            
            # 更新部署状态
            deployment.status = "running"
            deployment.log = (deployment.log or "") + "\n\n" + "\n".join(log_messages)
            await db.commit()
            
            logger.info(f"成功启动部署ID {deployment_id} 的应用")
            
        except Exception as e:
            error_message = f"启动应用错误：{str(e)}"
            logger.error(error_message)
            
            # 更新部署状态为失败
            deployment.status = "start_failed"
            deployment.log = (deployment.log or "") + f"\n\n[{datetime.now()}] 启动失败：\n{error_message}"
            await db.commit()

async def stop_application_task(deployment_id: int, db: AsyncSession):
    """后台任务：停止应用"""
    async with db.begin():
        result = await db.execute(
            select(Deployment)
            .options(selectinload(Deployment.project), selectinload(Deployment.machine))
            .filter(Deployment.id == deployment_id)
        )
        deployment = result.scalars().first()
        
        if not deployment:
            logger.error(f"停止应用任务：找不到部署ID {deployment_id}")
            return
        
        try:
            # 获取必要信息
            machine = deployment.machine
            deploy_path = deployment.deploy_path
            
            # 创建SSH客户端
            ssh_client = SSHClient(
                host=machine.host,
                port=machine.port,
                username=machine.username,
                password=machine.password if hasattr(machine, 'password') else None
            )
            
            # 连接到服务器
            await ssh_client.connect()
            
            log_messages = []
            log_messages.append(f"[{datetime.now()}] 开始停止应用")
            
            # 检查目录是否存在
            # 根据服务器地址判断可能的操作系统
            is_windows = False
            try:
                test_cmd = "powershell -Command \"echo 'WINDOWS'\""
                exit_status, stdout, stderr = await ssh_client.execute_command(test_cmd)
                if "WINDOWS" in stdout:
                    is_windows = True
                    logger.info("检测到Windows服务器")
            except:
                logger.info("PowerShell命令失败，判断为Linux服务器")
            
            # 根据服务器系统类型使用正确的命令
            if is_windows:
                check_dir_cmd = f"if exist \"{deploy_path}\" (echo EXISTS) else (echo NOT_EXISTS)"
            else:
                check_dir_cmd = f"if [ -d \"{deploy_path}\" ]; then echo 'EXISTS'; else echo 'NOT_EXISTS'; fi"
            
            exit_status, stdout, stderr = await ssh_client.execute_command(check_dir_cmd)
            dir_check_result = stdout.strip()
            log_messages.append(f"检查目录结果: {dir_check_result}")
            
            if "NOT_EXISTS" in dir_check_result:
                log_messages.append(f"目标目录不存在，无法停止应用")
                # 更新部署状态为失败
                deployment.status = "stop_failed"
                deployment.log = (deployment.log or "") + "\n\n" + "\n".join(log_messages)
                await db.commit()
                return
            
            # 优先检查start_all.py是否存在
            start_all_py_path = os.path.join(deploy_path, "start_all.py").replace('\\', '/')
            if is_windows:
                check_cmd = f"if exist \"{start_all_py_path}\" (echo EXISTS) else (echo NOT_EXISTS)"
            else:
                check_cmd = f"[ -f \"{start_all_py_path}\" ] && echo 'EXISTS' || echo 'NOT_EXISTS'"
            
            exit_status, stdout, stderr = await ssh_client.execute_command(check_cmd)
            has_start_all_py = "EXISTS" in stdout
            
            # 优先使用start_all.py --stop进行停止
            if has_start_all_py:
                log_messages.append("优先使用start_all.py --stop命令停止应用")
                if is_windows:
                    stop_command = f"cd \"{deploy_path}\" && set PYTHONIOENCODING=utf-8 && python3 start_all.py --stop"
                else:
                    stop_command = f"cd \"{deploy_path}\" && export PYTHONIOENCODING=utf-8 && python3 start_all.py --stop"
            else:
                # 检查停止脚本是否存在
                stop_script = "stop_all.sh"
                if is_windows:
                    stop_script = "stop_all.bat"
                
                script_path = os.path.join(deploy_path, stop_script).replace('\\', '/')
                if is_windows:
                    script_check_cmd = f"if exist \"{script_path}\" (echo EXISTS) else (echo NOT_EXISTS)"
                else:
                    script_check_cmd = f"[ -f \"{script_path}\" ] && echo 'EXISTS' || echo 'NOT_EXISTS'"
                
                exit_status, stdout, stderr = await ssh_client.execute_command(script_check_cmd)
                script_check_result = stdout.strip()
                log_messages.append(f"检查停止脚本结果: {script_check_result}")
                
                if "EXISTS" in script_check_result:
                    # 使用已存在的停止脚本
                    if is_windows:
                        stop_command = f"cd \"{deploy_path}\" && {stop_script}"
                    else:
                        # 确保脚本有执行权限
                        await ssh_client.execute_command(f"chmod +x \"{script_path}\"")
                        stop_command = f"cd \"{deploy_path}\" && ./{stop_script}"
                else:
                    # 尝试根据项目类型生成停止命令
                    log_messages.append(f"停止脚本不存在，尝试自动生成停止命令")
                    
                    project_type = deployment.project.project_type
                    
                    if is_windows:
                        # 在Windows上停止进程
                        if project_type == "backend":
                            stop_command = "taskkill /F /IM python.exe"
                        elif project_type == "frontend":
                            stop_command = "taskkill /F /IM node.exe"
                        else:
                            stop_command = "taskkill /F /IM python.exe && taskkill /F /IM node.exe"
                    else:
                        # Linux环境
                        # 尝试找出与项目相关的进程并杀死
                        project_name = deployment.project.name.replace(" ", "_").lower()
                        if project_type == "backend":
                            stop_command = f"pkill -f 'python.*{project_name}' || echo 'No process found'"
                        elif project_type == "frontend":
                            stop_command = f"pkill -f 'node.*{project_name}' || echo 'No process found'"
                        else:
                            stop_command = f"pkill -f '{project_name}' || echo 'No process found'"
                    
                    log_messages.append(f"自动生成的停止命令: {stop_command}")
            
            # 执行停止命令
            log_messages.append(f"执行停止命令: {stop_command}")
            exit_status, stdout, stderr = await ssh_client.execute_command(stop_command)
            log_messages.append(f"停止结果: 退出状态={exit_status}, 输出={stdout}, 错误={stderr}")
            
            # 关闭连接
            await ssh_client.close()
            
            # 更新部署状态
            deployment.status = "stopped"
            deployment.log = (deployment.log or "") + "\n\n" + "\n".join(log_messages)
            await db.commit()
            
            logger.info(f"成功停止部署ID {deployment_id} 的应用")
            
        except Exception as e:
            error_message = f"停止应用错误：{str(e)}"
            logger.error(error_message)
            
            # 更新部署状态为失败
            deployment.status = "stop_failed"
            deployment.log = (deployment.log or "") + f"\n\n[{datetime.now()}] 停止失败：\n{error_message}"
            await db.commit()

# 辅助函数
async def get_deployment_or_404(db: AsyncSession, deployment_id: int, current_user: User) -> Deployment:
    """
    根据ID获取部署记录，如果不存在则返回404错误
    """
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.project), selectinload(Deployment.machine))
        .filter(Deployment.id == deployment_id)
    )
    deployment = result.scalars().first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail=f"部署记录未找到: {deployment_id}")
    
    return deployment 