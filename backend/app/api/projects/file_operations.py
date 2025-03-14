"""
项目文件操作模块

该模块包含项目文件操作的相关功能，包括列表文件、查看文件内容、上传下载等。
"""

import os
import shutil
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from typing import Dict, List

from app.db.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectResponse
from app.api.deps import get_current_active_user
from app.utils.ignore_handler import parse_ignore_file, should_ignore_file, get_ignore_patterns

router = APIRouter()

@router.get("/{project_id}/files", response_model=Dict)
async def list_project_files(
    project_id: int,
    path: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取项目文件列表"""
    print(f"获取项目 {project_id} 的文件列表，路径: '{path}'")
    
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
        print(f"项目 {project_id} 不存在或用户 {current_user.id} 无权访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在或没有访问权限",
        )
    
    print(f"找到项目: {project.name} (ID: {project.id}), 存储路径: {project.storage_path}")
    
    # 构建完整路径
    base_path = Path(project.storage_path)
    full_path = base_path / path if path else base_path
    
    print(f"完整路径: {full_path}")
    
    # 检查路径是否存在，如果不存在则创建
    if not full_path.exists():
        print(f"路径不存在，尝试创建: {full_path}")
        try:
            os.makedirs(full_path, exist_ok=True)
            print(f"成功创建目录: {full_path}")
        except Exception as e:
            print(f"创建目录失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建目录失败: {str(e)}",
            )
    
    # 检查路径是否在项目目录下
    if not str(full_path.resolve()).startswith(str(base_path.resolve())):
        print(f"路径不在项目目录下: {full_path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该目录",
        )
    
    # 获取文件和目录列表
    files = []
    directories = []
    
    try:
        print(f"开始读取目录内容: {full_path}")
        # 检查目录是否为空
        dir_empty = True
        for item in full_path.iterdir():
            dir_empty = False
            item_stat = item.stat()
            item_info = {
                "name": item.name,
                "path": str(item.relative_to(base_path)),
                "size": item_stat.st_size,
                "modified": datetime.fromtimestamp(item_stat.st_mtime).isoformat(),
            }
            
            if item.is_dir():
                print(f"发现目录: {item.name}")
                directories.append({**item_info, "type": "directory"})
            else:
                # 获取文件扩展名
                ext = item.suffix.lower()[1:] if item.suffix else ""
                print(f"发现文件: {item.name} (.{ext})")
                files.append({**item_info, "type": "file", "extension": ext})
        
        # 如果目录为空，打印提示信息
        if dir_empty:
            print(f"目录为空: {full_path}")
        
        # 按名称排序
        directories.sort(key=lambda x: x["name"])
        files.sort(key=lambda x: x["name"])
        
        print(f"共找到 {len(directories)} 个目录和 {len(files)} 个文件")
        
        return {
            "current_path": path,
            "directories": directories,
            "files": files,
            "is_empty": dir_empty,
        }
    except Exception as e:
        print(f"读取目录内容时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取目录内容失败: {str(e)}",
        )


@router.get("/{project_id}/files/content")
async def get_file_content(
    project_id: int,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取文件内容"""
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
    
    # 构建完整路径
    base_path = Path(project.storage_path)
    file_full_path = base_path / file_path
    
    # 检查文件是否存在
    if not file_full_path.exists() or not file_full_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在",
        )
    
    # 检查路径是否在项目目录下
    if not str(file_full_path.resolve()).startswith(str(base_path.resolve())):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该文件",
        )
    
    # 获取文件扩展名
    extension = file_full_path.suffix.lower()[1:] if file_full_path.suffix else ""
    
    # 检查文件大小
    file_size = file_full_path.stat().st_size
    # 增加文本文件的大小限制，允许较大的文本文件查看
    text_file_extensions = [
        'txt', 'py', 'js', 'jsx', 'ts', 'tsx', 'html', 'css', 'scss', 'less', 
        'md', 'json', 'xml', 'yaml', 'yml', 'ini', 'conf', 'cfg', 'config',
        'sh', 'bat', 'cmd', 'ps1', 'sql', 'java', 'c', 'cpp', 'cs', 'go', 'php',
        'rb', 'rs', 'swift', 'kt', 'properties', 'env', 'gitignore', 'dockerignore',
        'htaccess'
    ]
    
    max_size_limit = 5 * 1024 * 1024 if extension in text_file_extensions else 1 * 1024 * 1024  # 文本文件5MB，其他1MB
    
    if file_size > max_size_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大，无法显示 (大小限制: {max_size_limit // 1024 // 1024}MB)",
        )
    
    # 判断文件类型，是文本文件还是二进制文件
    # 文本文件的扩展名列表
    if extension in text_file_extensions:
        try:
            # 尝试以文本方式读取
            content = file_full_path.read_text(encoding='utf-8', errors='replace')
            
            return {
                "content": content,
                "extension": extension,
                "name": file_full_path.name,
                "path": file_path,
                "size": file_size,
                "modified": datetime.fromtimestamp(file_full_path.stat().st_mtime).isoformat(),
                "is_binary": False
            }
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                with open(file_full_path, 'r', encoding='gbk', errors='replace') as f:
                    content = f.read()
                
                return {
                    "content": content,
                    "extension": extension,
                    "name": file_full_path.name,
                    "path": file_path,
                    "size": file_size,
                    "modified": datetime.fromtimestamp(file_full_path.stat().st_mtime).isoformat(),
                    "is_binary": False
                }
            except Exception:
                # 如果还是失败，作为二进制文件处理
                return {
                    "content": "此文件内容无法显示，可能是二进制文件或使用了不支持的编码。",
                    "extension": extension,
                    "name": file_full_path.name,
                    "path": file_path,
                    "size": file_size,
                    "modified": datetime.fromtimestamp(file_full_path.stat().st_mtime).isoformat(),
                    "is_binary": True
                }
    else:
        # 尝试检测文件是否为文本文件
        try:
            # 读取文件的前4KB来判断是否为文本文件
            with open(file_full_path, 'rb') as f:
                chunk = f.read(4096)
                
            # 判断是否为文本文件
            is_text = True
            for byte in chunk:
                # 如果包含0字节或非ASCII字符（且不是常见的UTF-8编码字节），则可能是二进制文件
                if byte == 0 or (byte > 127 and byte not in [194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254]):
                    is_text = False
                    break
            
            if is_text:
                # 如果是文本文件，尝试以UTF-8读取
                try:
                    content = file_full_path.read_text(encoding='utf-8', errors='replace')
                    return {
                        "content": content,
                        "extension": extension,
                        "name": file_full_path.name,
                        "path": file_path,
                        "size": file_size,
                        "modified": datetime.fromtimestamp(file_full_path.stat().st_mtime).isoformat(),
                        "is_binary": False
                    }
                except Exception:
                    # 处理任何读取错误
                    return {
                        "content": "此文件可能是文本文件，但无法正确解码。",
                        "extension": extension,
                        "name": file_full_path.name,
                        "path": file_path,
                        "size": file_size,
                        "modified": datetime.fromtimestamp(file_full_path.stat().st_mtime).isoformat(),
                        "is_binary": True
                    }
            else:
                # 二进制文件
                return {
                    "content": "此文件是二进制文件，无法直接显示。",
                    "extension": extension,
                    "name": file_full_path.name,
                    "path": file_path,
                    "size": file_size,
                    "modified": datetime.fromtimestamp(file_full_path.stat().st_mtime).isoformat(),
                    "is_binary": True
                }
        except Exception as e:
            # 处理任何异常
            return {
                "content": f"读取文件时发生错误: {str(e)}",
                "extension": extension,
                "name": file_full_path.name,
                "path": file_path,
                "size": file_size,
                "modified": datetime.fromtimestamp(file_full_path.stat().st_mtime).isoformat(),
                "is_binary": True
            }


@router.post("/upload/{project_id}", response_model=ProjectResponse)
async def upload_project_files(
    project_id: int,
    file: UploadFile = File(...),
    mode: str = Form("replace"),  # 默认为替换模式
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """上传项目文件（ZIP格式）
    
    mode:
    - replace: 替换现有文件
    - increment: 增量更新
    """
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
    
    # 检查文件类型
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能上传ZIP格式的文件",
        )
    
    # 保存上传的文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    try:
        # 将上传的文件保存到临时文件
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # 确保目标目录存在
        os.makedirs(project.storage_path, exist_ok=True)
        
        # 读取.gitignore文件(如果存在)
        gitignore_file_path = os.path.join(project.storage_path, ".gitignore")
        ignore_patterns = parse_ignore_file(gitignore_file_path)  # 使用兼容函数名
        
        # 在替换模式下，如果.gitignore文件存在，需要保存它
        gitignore_content = None
        if mode == "replace" and os.path.exists(gitignore_file_path):
            with open(gitignore_file_path, 'r', encoding='utf-8') as f:
                gitignore_content = f.read()
        
        # 处理ZIP文件
        with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
            # 获取所有文件名列表
            file_list = zip_ref.namelist()
            
            # 检查是否有.gitignore文件
            gitignore_in_zip = next((f for f in file_list if f == ".gitignore" or f.endswith("/.gitignore")), None)
            if gitignore_in_zip:
                # 从ZIP中提取.gitignore文件
                gitignore_content = zip_ref.read(gitignore_in_zip).decode('utf-8', errors='ignore')
                # 更新忽略模式
                ignore_patterns = [line.strip() for line in gitignore_content.splitlines() 
                                  if line.strip() and not line.strip().startswith('#')]
            
            # 如果是替换模式，先清空目录
            if mode == "replace":
                for item in os.listdir(project.storage_path):
                    item_path = os.path.join(project.storage_path, item)
                    # 保留.gitignore文件
                    if item == ".gitignore":
                        continue
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
            
            # 计算需要解压的文件
            files_to_extract = []
            root_files_to_extract = []  # 专门存储根目录文件
            
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue
                
                file_path = file_info.filename
                
                # 检查文件是否应该被忽略
                if should_ignore_file(file_path, ignore_patterns):
                    print(f"忽略文件: {file_path}")
                    continue
                
                # 检查是否为直接在根目录下的文件
                is_root_file = '/' not in file_path and '\\' not in file_path
                
                # 添加到要解压的文件列表
                if is_root_file:
                    root_files_to_extract.append(file_info)
                    print(f"添加根目录文件: {file_path}")
                else:
                    files_to_extract.append(file_info)
            
            # 解压文件
            for file_info in files_to_extract:
                # 解压文件
                zip_ref.extract(file_info, project.storage_path)
                print(f"已解压文件: {file_info.filename}")
            
            # 特别处理根目录文件
            for file_info in root_files_to_extract:
                zip_ref.extract(file_info, project.storage_path)
                print(f"已解压根目录文件: {file_info.filename}")
        
        # 保存.gitignore文件内容（如果存在）
        if gitignore_content:
            with open(gitignore_file_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
                print(f"已更新.gitignore文件")
        
        # 更新项目最后更新时间
        project.last_updated = func.now()
        await db.commit()
        
        # 重新查询项目
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalars().first()
        
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
            "last_updated": project.last_updated
        }
        
        return ProjectResponse(**project_data)
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@router.post("/download/{project_id}")
async def download_project_files(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """下载项目文件（ZIP格式）"""
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
    
    # 检查项目目录是否存在
    if not os.path.exists(project.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目文件不存在",
        )
    
    # 创建临时zip文件
    temp_dir = tempfile.gettempdir()
    zip_file_name = f"{project.name}_{project_id}.zip"
    zip_file_path = os.path.join(temp_dir, zip_file_name)
    
    # 创建zip文件
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project.storage_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, project.storage_path)
                zipf.write(file_path, arcname)
    
    # 返回zip文件
    return FileResponse(
        path=zip_file_path,
        filename=zip_file_name,
        media_type="application/zip"
    )


@router.get("/{project_id}/files/download")
async def download_file(
    project_id: int,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """下载单个文件"""
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
    
    # 构建完整路径
    base_path = Path(project.storage_path)
    file_full_path = base_path / file_path
    
    # 检查文件是否存在
    if not file_full_path.exists() or not file_full_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在",
        )
    
    # 检查路径是否在项目目录下
    if not str(file_full_path.resolve()).startswith(str(base_path.resolve())):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该文件",
        )
    
    # 返回文件
    return FileResponse(
        path=str(file_full_path),
        filename=file_full_path.name,
        media_type="application/octet-stream"
    ) 