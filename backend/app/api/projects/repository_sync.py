"""
仓库同步模块

该模块包含项目仓库同步的相关功能，包括Git仓库克隆/拉取和本地目录同步。
"""

import os
import shutil
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Form, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func

from app.db.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectResponse
from app.api.deps import get_current_active_user
from app.utils.ignore_handler import get_gitignore_patterns as get_ignore_patterns, should_ignore_file
from app.utils.file_utils import custom_copytree
from app.api.projects.websocket import manager

router = APIRouter()

@router.post("/{project_id}/clone", response_model=ProjectResponse)
async def clone_from_git(
    project_id: int,
    repository_url: str = Form(...),
    branch: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """从Git仓库克隆项目"""
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
    
    # 清理项目目录
    if os.path.exists(project.storage_path):
        shutil.rmtree(project.storage_path)
    
    os.makedirs(project.storage_path, exist_ok=True)
    
    # 构建git命令
    cmd = ["git", "clone"]
    if branch:
        cmd.extend(["--branch", branch])
    
    cmd.extend([repository_url, project.storage_path])
    
    try:
        # 执行git克隆命令
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Git克隆失败: {stderr.decode()}"
            )
        
        # 更新项目的仓库URL
        project.repository_url = repository_url
        await db.commit()
        await db.refresh(project)
        
        return project
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"克隆过程中发生错误: {str(e)}"
        )


@router.post("/{project_id}/sync", response_model=ProjectResponse)
async def sync_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """同步项目信息"""
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
    
    # 根据仓库类型同步项目信息
    if project.repository_type == "git":
        # 如果是Git仓库，则克隆/更新仓库
        await sync_git_repository(project)
    elif project.repository_type == "local":
        # 如果是本地路径，则同步本地文件夹
        await sync_local_folder(project)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的仓库类型",
        )
    
    # 更新项目最后更新时间
    project.last_updated = func.now()
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


@router.post("/{project_id}/ignore")
async def create_or_update_ignore_file(
    project_id: int,
    content: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建或更新项目的.gitignore文件"""
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
    
    # 确保项目目录存在
    if not os.path.exists(project.storage_path):
        os.makedirs(project.storage_path, exist_ok=True)
    
    # 写入.gitignore文件
    gitignore_file_path = os.path.join(project.storage_path, ".gitignore")
    try:
        with open(gitignore_file_path, 'w', encoding='utf-8') as f:
            f.write(content.get("content", ""))
        
        # 更新项目最后更新时间
        project.last_updated = func.now()
        await db.commit()
        
        return {"message": ".gitignore文件已创建/更新"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建.gitignore文件失败: {str(e)}",
        )


@router.websocket("/ws/{project_id}/sync-progress")
async def websocket_sync_progress(websocket: WebSocket, project_id: int):
    """WebSocket端点，用于实时同步进度通知"""
    await manager.connect(websocket, project_id)
    try:
        while True:
            # 保持连接活跃，等待消息
            data = await websocket.receive_text()
            # 可以处理客户端发来的消息，但在这个例子中我们不需要
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)


async def sync_git_repository(project: Project):
    """同步Git仓库"""
    repository_url = project.repository_url
    storage_path = project.storage_path
    project_id = project.id
    
    # 发送开始同步的消息
    await manager.broadcast_to_project(
        project_id, 
        {"status": "start", "message": "开始同步Git仓库...", "progress": 0}
    )
    
    # 检查根目录的.gitignore文件
    root_gitignore_path = os.path.join(os.path.dirname(os.path.dirname(storage_path)), ".gitignore")
    ignore_patterns = get_ignore_patterns(storage_path)
    
    # 指定必须保留的重要文件
    important_files = ["start_all.bat", "README.md", "prompt.txt", ".gitignore"]
    
    # 更新进度消息
    if ignore_patterns:
        await manager.broadcast_to_project(
            project_id, 
            {"status": "progress", "message": f"找到.gitignore文件，将忽略 {len(ignore_patterns)} 个模式", "progress": 5}
        )
    
    # 检查仓库是否已存在
    git_dir = os.path.join(storage_path, ".git")
    if os.path.exists(git_dir):
        # 如果已存在，则执行git pull
        try:
            # 切换到仓库目录
            os.chdir(storage_path)
            
            # 更新进度消息
            await manager.broadcast_to_project(
                project_id, 
                {"status": "progress", "message": "拉取最新代码...", "progress": 30}
            )
            
            # 执行git pull
            process = await asyncio.create_subprocess_exec(
                "git", "pull",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # 更新进度消息
                await manager.broadcast_to_project(
                    project_id, 
                    {"status": "progress", "message": "拉取失败，准备重新克隆...", "progress": 40}
                )
                
                print(f"Git pull failed: {stderr.decode()}")
                # 如果pull失败，尝试重新克隆
                
                # 备份重要文件
                important_files_content = {}
                for file in important_files:
                    file_path = os.path.join(storage_path, file)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        try:
                            with open(file_path, 'rb') as f:
                                important_files_content[file] = f.read()
                        except Exception as e:
                            print(f"备份重要文件 {file} 失败: {str(e)}")
                
                if os.path.exists(storage_path):
                    shutil.rmtree(storage_path)
                os.makedirs(storage_path, exist_ok=True)
                
                # 更新进度消息
                await manager.broadcast_to_project(
                    project_id, 
                    {"status": "progress", "message": "克隆仓库中...", "progress": 50}
                )
                
                # 重新克隆
                process = await asyncio.create_subprocess_exec(
                    "git", "clone", repository_url, storage_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    # 更新进度消息 - 失败
                    await manager.broadcast_to_project(
                        project_id, 
                        {"status": "error", "message": f"同步Git仓库失败: {stderr.decode()}", "progress": 100}
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"同步Git仓库失败: {stderr.decode()}",
                    )
                else:
                    # 恢复重要文件
                    for file, content in important_files_content.items():
                        file_path = os.path.join(storage_path, file)
                        try:
                            # 检查文件是否已存在（可能在Git仓库中也有）
                            if not os.path.exists(file_path):
                                with open(file_path, 'wb') as f:
                                    f.write(content)
                                print(f"恢复重要文件: {file}")
                        except Exception as e:
                            print(f"恢复重要文件 {file} 失败: {str(e)}")
                            
                    # 更新进度消息 - 成功
                    await manager.broadcast_to_project(
                        project_id, 
                        {"status": "progress", "message": "克隆仓库完成", "progress": 90}
                    )
            else:
                # 更新进度消息 - 成功拉取
                await manager.broadcast_to_project(
                    project_id, 
                    {"status": "progress", "message": "拉取代码完成", "progress": 90}
                )
        except Exception as e:
            # 更新进度消息 - 错误
            await manager.broadcast_to_project(
                project_id, 
                {"status": "error", "message": f"同步过程发生错误: {str(e)}", "progress": 100}
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"同步Git仓库失败: {str(e)}",
            )
    else:
        # 如果不存在，则执行git clone
        try:
            # 确保存储目录存在
            if os.path.exists(storage_path):
                # 备份重要文件
                important_files_content = {}
                for file in important_files:
                    file_path = os.path.join(storage_path, file)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        try:
                            with open(file_path, 'rb') as f:
                                important_files_content[file] = f.read()
                        except Exception as e:
                            print(f"备份重要文件 {file} 失败: {str(e)}")
                
                shutil.rmtree(storage_path)
            
            os.makedirs(storage_path, exist_ok=True)
            
            # 更新进度消息
            await manager.broadcast_to_project(
                project_id, 
                {"status": "progress", "message": "克隆仓库中...", "progress": 30}
            )
            
            # 执行git clone
            process = await asyncio.create_subprocess_exec(
                "git", "clone", repository_url, storage_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # 更新进度消息 - 失败
                await manager.broadcast_to_project(
                    project_id, 
                    {"status": "error", "message": f"克隆Git仓库失败: {stderr.decode()}", "progress": 100}
                )
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Git克隆失败: {stderr.decode()}"
                )
            
            # 恢复重要文件
            if 'important_files_content' in locals():
                for file, content in important_files_content.items():
                    file_path = os.path.join(storage_path, file)
                    try:
                        # 检查文件是否已存在（可能在Git仓库中也有）
                        if not os.path.exists(file_path):
                            with open(file_path, 'wb') as f:
                                f.write(content)
                            print(f"恢复重要文件: {file}")
                    except Exception as e:
                        print(f"恢复重要文件 {file} 失败: {str(e)}")
            
            # 更新进度消息 - 成功
            await manager.broadcast_to_project(
                project_id, 
                {"status": "progress", "message": "克隆仓库完成", "progress": 90}
            )
        except Exception as e:
            # 更新进度消息 - 错误
            await manager.broadcast_to_project(
                project_id, 
                {"status": "error", "message": f"克隆过程发生错误: {str(e)}", "progress": 100}
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"克隆过程中发生错误: {str(e)}"
            )
    
    # Git克隆/拉取完成后，应用.gitignore规则进行清理
    if ignore_patterns:
        await manager.broadcast_to_project(
            project_id, 
            {"status": "progress", "message": "应用.gitignore规则清理文件...", "progress": 95}
        )
        
        try:
            # 复制根目录的.gitignore文件到项目目录
            if os.path.exists(root_gitignore_path):
                shutil.copy2(root_gitignore_path, os.path.join(storage_path, ".gitignore"))
                
            # 重新获取忽略规则，包括项目目录中可能存在的规则
            ignore_patterns = get_ignore_patterns(storage_path)
        
            # 遍历项目目录并删除应该被忽略的文件
            for root, dirs, files in os.walk(storage_path, topdown=True):
                # 转换为相对路径(相对于项目目录)
                rel_path = os.path.relpath(root, storage_path)
                rel_path = "" if rel_path == "." else rel_path
                
                # 过滤要忽略的目录
                dirs_to_remove = []
                for i, dir_name in enumerate(dirs):
                    dir_path = os.path.join(rel_path, dir_name) if rel_path else dir_name
                    
                    # 不要删除.git目录
                    if dir_name == ".git":
                        continue
                        
                    if should_ignore_file(dir_path, ignore_patterns):
                        dirs_to_remove.append(i)
                        print(f"忽略目录: {dir_path}")
                
                # 从后向前删除，避免索引混乱
                for i in sorted(dirs_to_remove, reverse=True):
                    full_dir_path = os.path.join(root, dirs[i])
                    if os.path.exists(full_dir_path) and os.path.isdir(full_dir_path):
                        shutil.rmtree(full_dir_path)
                    dirs.pop(i)
                
                # 删除要忽略的文件
                for file_name in files:
                    # 保护重要文件
                    if file_name in important_files:
                        continue
                        
                    file_path = os.path.join(rel_path, file_name) if rel_path else file_name
                    if should_ignore_file(file_path, ignore_patterns):
                        full_file_path = os.path.join(root, file_name)
                        if os.path.exists(full_file_path):
                            os.remove(full_file_path)
                            print(f"删除忽略的文件: {file_path}")
                
        except Exception as e:
            print(f"应用.gitignore规则时出错: {str(e)}")
            # 继续执行，不中断流程
    
    # 最终完成消息
    await manager.broadcast_to_project(
        project_id, 
        {"status": "complete", "message": "Git仓库同步完成!", "progress": 100}
    )


async def sync_local_folder(project: Project):
    """同步本地文件夹"""
    local_path = project.repository_url
    storage_path = project.storage_path
    project_id = project.id
    
    # 发送开始同步的消息
    await manager.broadcast_to_project(
        project_id, 
        {"status": "start", "message": "开始同步本地文件夹...", "progress": 0}
    )
    
    # 检查本地路径是否存在
    if not os.path.exists(local_path) or not os.path.isdir(local_path):
        # 更新进度消息 - 错误
        await manager.broadcast_to_project(
            project_id, 
            {"status": "error", "message": f"本地路径不存在或不是文件夹: {local_path}", "progress": 100}
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"本地路径不存在或不是文件夹: {local_path}",
        )
    
    # 更新进度消息
    await manager.broadcast_to_project(
        project_id, 
        {"status": "progress", "message": "清理存储路径...", "progress": 20}
    )
    
    # 清空存储路径
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)
    os.makedirs(storage_path, exist_ok=True)
    
    try:
        # 更新进度消息
        await manager.broadcast_to_project(
            project_id, 
            {"status": "progress", "message": "复制文件中...", "progress": 40}
        )
        
        # 获取根目录.gitignore文件并复制到项目目录
        # 修正根目录路径计算，避免过度嵌套
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(storage_path)))
        root_gitignore_path = os.path.join(project_root, ".gitignore")
        
        if os.path.exists(root_gitignore_path):
            shutil.copy2(root_gitignore_path, os.path.join(storage_path, ".gitignore"))
            await manager.broadcast_to_project(
                project_id, 
                {"status": "progress", "message": "已复制根目录.gitignore文件到项目", "progress": 45}
            )
        
        # 获取忽略模式
        ignore_patterns = get_ignore_patterns(storage_path)
        
        if ignore_patterns:
            await manager.broadcast_to_project(
                project_id, 
                {"status": "progress", "message": f"应用忽略规则，将排除 {len(ignore_patterns)} 个模式", "progress": 50}
            )
        
        # 指定必须包含的重要文件
        important_files = ["start_all.bat", "README.md", "prompt.txt", ".gitignore"]
        
        # 使用自定义复制函数
        custom_copytree(local_path, storage_path, ignore_patterns, important_files)
        
        # 更新进度消息 - 成功
        await manager.broadcast_to_project(
            project_id, 
            {"status": "complete", "message": "本地文件夹同步完成!", "progress": 100}
        )
    except Exception as e:
        # 更新进度消息 - 错误
        await manager.broadcast_to_project(
            project_id, 
            {"status": "error", "message": f"同步本地文件夹失败: {str(e)}", "progress": 100}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步本地文件夹失败: {str(e)}",
        ) 