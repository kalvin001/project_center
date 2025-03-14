import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get("/directories")
async def list_directories(
    path: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    列出指定路径下的目录
    
    安全说明：
    - 只有经过身份验证的用户可以使用
    - 后端运行在服务器环境，可以访问服务器文件系统
    """
    try:
        if not os.path.isdir(path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"路径不是有效的目录: {path}"
            )
        
        # 获取目录内容
        entries = os.listdir(path)
        directories = []
        
        for entry in entries:
            # 构建完整路径
            entry_path = os.path.join(path, entry)
            
            # 只包括目录
            if os.path.isdir(entry_path):
                # 检查是否可以访问目录
                try:
                    # 尝试列出目录内容以检查访问权限
                    next(os.scandir(entry_path), None)
                    accessible = True
                except PermissionError:
                    accessible = False
                
                if accessible:
                    # 检查目录是否为空
                    is_empty = len(os.listdir(entry_path)) == 0
                    
                    directories.append({
                        "title": entry,  # 显示名称
                        "key": entry_path,  # 唯一键
                        "path": entry_path,  # 完整路径
                        "isLeaf": is_empty,  # 如果目录为空，标记为叶子节点
                    })
        
        # 按名称排序
        directories.sort(key=lambda x: x["title"].lower())
        
        return directories
    
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"没有权限访问目录: {path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取目录列表失败: {str(e)}"
        ) 