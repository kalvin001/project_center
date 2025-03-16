"""
项目CRUD模块

该模块包含项目的基本CRUD（创建、读取、更新、删除）操作。
"""

import os
import shutil
import uuid
import logging
import time
import subprocess
import traceback
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from typing import List
from datetime import datetime

from app.core.config import settings
from app.db.database import get_db
from app.models.project import Project, Deployment
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectWithDeployments
from app.api.deps import get_current_active_user
from app.utils.file_utils import format_size
from app.api.projects.repository_sync import sync_git_repository, sync_local_folder
from app.models.machine import Machine

router = APIRouter()

# 项目统计功能
async def count_project_stats(storage_path: str) -> dict:
    """统计项目文件数量、总大小和代码行数"""
    from app.utils.ignore_handler import parse_ignore_file, should_ignore_file
    
    stats = {
        "file_count": 0,
        "total_size_bytes": 0,
        "code_lines": 0,
        "total_size_human": "",
        "ignore_file_exists": False
    }
    
    # 检查.gitignore文件是否存在
    gitignore_file_path = os.path.join(storage_path, ".gitignore")
    ignore_patterns = parse_ignore_file(gitignore_file_path)
    stats["ignore_file_exists"] = os.path.exists(gitignore_file_path)
    
    # 统计文件
    for root, dirs, files in os.walk(storage_path):
        # 转换为相对路径
        rel_path = os.path.relpath(root, storage_path)
        rel_path = "" if rel_path == "." else rel_path
        
        # 检查当前目录是否应该被忽略
        if should_ignore_file(rel_path, ignore_patterns):
            dirs[:] = []  # 清空子目录列表，不再遍历
            continue
        
        # 对目录列表进行过滤
        dirs[:] = [d for d in dirs if not should_ignore_file(os.path.join(rel_path, d), ignore_patterns)]
        
        for file in files:
            file_path = os.path.join(rel_path, file)
            # 检查文件是否应该被忽略
            if should_ignore_file(file_path, ignore_patterns):
                continue
            
            # 增加文件计数
            stats["file_count"] += 1
            
            # 获取文件大小
            full_path = os.path.join(root, file)
            file_size = os.path.getsize(full_path)
            stats["total_size_bytes"] += file_size
            
            # 计算代码行数 (仅对常见代码文件)
            code_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', 
                               '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.php', 
                               '.rb', '.go', '.rs', '.swift', '.kt', '.sql']
            
            if any(full_path.endswith(ext) for ext in code_extensions):
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        stats["code_lines"] += sum(1 for _ in f)
                except Exception as e:
                    logging.warning(f"统计代码行数出错: {full_path}, {e}")
    
    # 格式化总大小为人类可读格式
    stats["total_size_human"] = format_size(stats["total_size_bytes"])
    
    return stats


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建新项目"""
    # 验证仓库类型
    if project_in.repository_type not in ["git", "local"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的仓库类型，只支持 git 或 local",
        )
        
    # 如果是本地路径，检查路径是否存在
    if project_in.repository_type == "local" and (not os.path.exists(project_in.repository_url) or not os.path.isdir(project_in.repository_url)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"本地路径不存在或不是文件夹: {project_in.repository_url}",
        )
    
    # 生成存储路径
    project_id = str(uuid.uuid4())
    storage_path = str(settings.PROJECTS_DIR / project_id)
    os.makedirs(storage_path, exist_ok=True)
    
    # 复制根目录的.gitignore文件到项目目录
    # 使用项目目录的.gitignore文件
    root_gitignore_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".gitignore")
    if os.path.exists(root_gitignore_path):
        try:
            shutil.copy2(root_gitignore_path, os.path.join(storage_path, ".gitignore"))
            print(f"已复制根目录.gitignore文件到项目目录: {storage_path}")
        except Exception as e:
            print(f"复制.gitignore文件时出错: {str(e)}")
    
    # 创建项目记录
    db_project = Project(
        **project_in.dict(),
        owner_id=current_user.id,
        storage_path=storage_path,
    )
    
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    
    # 同步项目信息
    try:
        if db_project.repository_type == "git":
            await sync_git_repository(db_project)
        elif db_project.repository_type == "local":
            await sync_local_folder(db_project)
            
        # 更新项目最后更新时间
        db_project.last_updated = func.now()
        await db.commit()
        
        # 重新查询项目以避免异步懒加载问题
        result = await db.execute(
            select(Project).where(Project.id == db_project.id)
        )
        db_project = result.scalars().first()
        
    except HTTPException as e:
        # 如果同步失败，继续返回创建的项目，但记录错误
        print(f"项目创建成功，但同步失败: {e.detail}")
    
    # 创建一个安全的响应数据字典，避免懒加载问题
    project_data = {
        "id": db_project.id,
        "name": db_project.name,
        "description": db_project.description,
        "owner_id": db_project.owner_id,
        "repository_url": db_project.repository_url,
        "repository_type": db_project.repository_type,
        "is_active": db_project.is_active,
        "project_type": db_project.project_type,
        "tech_stack": db_project.tech_stack,
        "storage_path": db_project.storage_path,
        "created_at": db_project.created_at,
        "last_updated": db_project.last_updated
    }
    
    return ProjectResponse(**project_data)


@router.get("/", response_model=List[ProjectResponse])
async def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目列表"""
    # 管理员可以看到所有项目，普通用户只能看到自己的项目
    if current_user.is_admin:
        result = await db.execute(
            select(Project).offset(skip).limit(limit)
        )
    else:
        result = await db.execute(
            select(Project).where(Project.owner_id == current_user.id).offset(skip).limit(limit)
        )
    
    projects = result.scalars().all()
    
    # 转换为安全的响应数据列表
    project_responses = []
    for project in projects:
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "repository_url": project.repository_url,
            "repository_type": project.repository_type,
            "is_active": project.is_active,
            "project_type": project.project_type,
            "tech_stack": project.tech_stack,
            "storage_path": project.storage_path,
            "created_at": project.created_at,
            "last_updated": project.last_updated
        }
        project_responses.append(ProjectResponse(**project_data))
    
    return project_responses


@router.get("/{project_id}", response_model=ProjectWithDeployments)
async def read_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目详情"""
    try:
        # 获取项目
        if current_user.is_admin:
            result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
        else:
            result = await db.execute(
                select(Project).where(
                    and_(Project.id == project_id, Project.owner_id == current_user.id)
                )
            )
        
        project = result.scalars().first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在或没有访问权限",
            )
        
        # 获取项目部署记录
        deployment_result = await db.execute(
            select(Deployment).where(Deployment.project_id == project_id)
        )
        db_deployments = deployment_result.scalars().all()
        
        # 转换部署记录为响应模型
        deployments = []
        for dep in db_deployments:
            try:
                # 获取机器信息以获取server_host
                machine_result = await db.execute(
                    select(Machine).where(Machine.id == dep.machine_id)
                )
                machine = machine_result.scalars().first()
                
                # 检查机器是
                if machine:
                    server_host = machine.hostname
                    server_port = machine.ssh_port
                else:
                    logging.warning(f"部署ID {dep.id} 引用的机器ID {dep.machine_id} 不存在")
                    server_host = "unknown"
                    server_port = None
                
                # 创建部署响应对象
                deployment_data = {
                    "id": dep.id,
                    "project_id": dep.project_id,
                    "environment": dep.environment,
                    "server_host": server_host,
                    "server_port": server_port,
                    "deploy_path": dep.deploy_path or "",
                    "status": dep.status,
                    "log": dep.log,
                    "deployed_at": dep.deployed_at or datetime.now(),
                    "created_at": dep.created_at
                }
                deployments.append(deployment_data)
            except Exception as e:
                logging.error(f"处理部署ID {dep.id} 时出错: {e}")
                # 继续处理其他部署记录，不中断流程
        
        # 获取项目统计信息
        stats = {"file_count": 0, "total_size_bytes": 0, "code_lines": 0, "total_size_human": "0 B", "ignore_file_exists": False}
        try:
            if os.path.exists(project.storage_path) and os.path.isdir(project.storage_path):
                stats = await count_project_stats(project.storage_path)
            else:
                logging.warning(f"项目存储路径不存在或不是目录: {project.storage_path}")
        except Exception as e:
            logging.error(f"计算项目统计信息时出错: {e}")
            logging.error(traceback.format_exc())
        
        # 创建响应数据
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "repository_url": project.repository_url,
            "repository_type": project.repository_type,
            "is_active": project.is_active,
            "project_type": project.project_type,
            "tech_stack": project.tech_stack,
            "storage_path": project.storage_path,
            "created_at": project.created_at,
            "last_updated": project.last_updated,
            "deployments": deployments,
            "stats": stats  # 添加统计信息
        }
        
        return ProjectWithDeployments(**project_data)
    except Exception as e:
        logging.error(f"获取项目详情时出错 (项目ID: {project_id}): {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目详情时出错: {str(e)}",
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新项目"""
    # 管理员可以更新所有项目，普通用户只能更新自己的项目
    if current_user.is_admin:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
    else:
        result = await db.execute(
            select(Project).where(
                and_(Project.id == project_id, Project.owner_id == current_user.id)
            )
        )
    
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在或没有访问权限",
        )
    
    # 更新项目
    update_data = project_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    
    await db.commit()
    
    # 重新查询项目以避免异步懒加载问题
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalars().first()
    
    # 创建一个安全的响应数据字典
    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "owner_id": project.owner_id,
        "repository_url": project.repository_url,
        "repository_type": project.repository_type,
        "is_active": project.is_active,
        "project_type": project.project_type,
        "tech_stack": project.tech_stack,
        "storage_path": project.storage_path,
        "created_at": project.created_at,
        "last_updated": project.last_updated
    }
    
    return ProjectResponse(**project_data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除项目"""
    # 管理员可以删除所有项目，普通用户只能删除自己的项目
    if current_user.is_admin:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
    else:
        result = await db.execute(
            select(Project).where(
                and_(Project.id == project_id, Project.owner_id == current_user.id)
            )
        )
    
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在或没有访问权限",
        )
    
    # 删除项目文件
    storage_path = project.storage_path
    deletion_success = True
    
    if os.path.exists(storage_path):
        try:
            # 首先尝试常规删除
            shutil.rmtree(storage_path)
        except PermissionError as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"删除项目文件时遇到权限错误: {e}")
            deletion_success = False
            
            try:
                # 在Windows系统上，尝试使用特殊方法删除
                if os.name == 'nt':  # Windows系统
                    # 首先尝试关闭可能的文件句柄
                    import subprocess
                    import time
                    
                    # 等待一段时间，以便可能的文件操作完成
                    time.sleep(1)
                    
                    # 使用Windows命令强制删除
                    subprocess.run(['cmd', '/c', f'rmdir /s /q "{storage_path}"'], 
                                 shell=True, check=False)
                    
                    # 检查是否删除成功
                    if os.path.exists(storage_path):
                        logger.warning(f"尝试使用rmdir命令删除失败，将在数据库中标记项目为非活跃")
                        # 如果仍然无法删除，不要中断流程，继续删除数据库记录
                        # 只记录警告日志
                    else:
                        logger.info(f"使用rmdir命令成功删除项目文件: {storage_path}")
                        deletion_success = True
                else:
                    # 非Windows系统，重新尝试删除
                    time.sleep(1)
                    shutil.rmtree(storage_path, ignore_errors=True)
                    if not os.path.exists(storage_path):
                        deletion_success = True
            except Exception as ex:
                # 捕获所有异常，但不要中断流程
                logger.error(f"尝试清理项目文件时出错: {ex}")
                # 继续处理数据库记录的删除
    
    # 根据文件删除结果决定是删除记录还是标记为非活跃
    if deletion_success:
        # 完全删除项目记录
        await db.delete(project)
    else:
        # 文件删除失败，仅标记项目为非活跃
        project.is_active = False
        
    # 提交数据库更改
    await db.commit()
    
    return None 