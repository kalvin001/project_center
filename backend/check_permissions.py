import os
import stat
from pathlib import Path

def check_directory_permissions(directory_path):
    """检查目录的权限"""
    try:
        path = Path(directory_path)
        
        # 检查目录是否存在
        if not path.exists():
            print(f"目录不存在: {path}")
            return
        
        # 检查是否是目录
        if not path.is_dir():
            print(f"路径不是目录: {path}")
            return
        
        # 获取目录的权限
        st_mode = path.stat().st_mode
        permissions = stat.filemode(st_mode)
        
        print(f"目录: {path}")
        print(f"权限: {permissions}")
        
        # 检查读权限
        if os.access(path, os.R_OK):
            print("✓ 有读取权限")
        else:
            print("✗ 没有读取权限")
        
        # 检查写权限
        if os.access(path, os.W_OK):
            print("✓ 有写入权限")
        else:
            print("✗ 没有写入权限")
        
        # 检查执行权限
        if os.access(path, os.X_OK):
            print("✓ 有执行权限")
        else:
            print("✗ 没有执行权限")
        
        # 列出目录内容
        print("\n目录内容:")
        for item in path.iterdir():
            item_st_mode = item.stat().st_mode
            item_permissions = stat.filemode(item_st_mode)
            
            if item.is_dir():
                print(f"[目录] {item.name} ({item_permissions})")
            else:
                print(f"[文件] {item.name} ({item_permissions})")
    
    except Exception as e:
        print(f"检查权限时发生错误: {str(e)}")

if __name__ == "__main__":
    from app.core.config import settings
    
    # 检查项目根目录
    print("===== 检查项目根目录 =====")
    check_directory_permissions(settings.PROJECTS_DIR)
    
    # 检查具体项目目录
    print("\n===== 检查具体项目目录 =====")
    projects_dir = Path(settings.PROJECTS_DIR)
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            print(f"\n----- 项目: {project_dir.name} -----")
            check_directory_permissions(project_dir) 