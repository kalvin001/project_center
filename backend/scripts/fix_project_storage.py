#!/usr/bin/env python
"""
修复项目存储目录脚本

这个脚本用于修复项目存储目录的权限问题
"""

import os
import sys
import stat
import shutil
import subprocess
from pathlib import Path

# 项目存储目录路径
DEFAULT_STORAGE_DIR = 'D:/data/code/project_center'

def fix_storage_permissions():
    """修复存储目录权限"""
    print(f"\n===== 修复存储目录权限 =====")
    print(f"存储目录: {DEFAULT_STORAGE_DIR}")
    
    # 确保目录存在
    if not os.path.exists(DEFAULT_STORAGE_DIR):
        try:
            os.makedirs(DEFAULT_STORAGE_DIR, exist_ok=True)
            print(f"✓ 创建存储目录成功")
        except Exception as e:
            print(f"× 创建存储目录失败: {str(e)}")
            return False
    
    # 在Windows上设置完全控制权限
    if os.name == 'nt':
        try:
            # 获取当前用户
            current_user = os.environ.get('USERNAME')
            print(f"当前用户: {current_user}")
            
            # 使用icacls命令设置权限
            command = f'icacls "{DEFAULT_STORAGE_DIR}" /grant "{current_user}":(OI)(CI)F /T'
            print(f"执行命令: {command}")
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ 设置权限成功")
                print(result.stdout)
            else:
                print(f"× 设置权限失败")
                print(f"错误: {result.stderr}")
                return False
        except Exception as e:
            print(f"× 设置权限时出错: {str(e)}")
            return False
    else:
        # 在Unix系统上设置权限
        try:
            os.chmod(DEFAULT_STORAGE_DIR, 0o755)
            print(f"✓ 设置目录权限为755")
            
            # 递归设置子目录和文件的权限
            for root, dirs, files in os.walk(DEFAULT_STORAGE_DIR):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o755)
                for f in files:
                    os.chmod(os.path.join(root, f), 0o644)
            print(f"✓ 递归设置子目录和文件权限")
        except Exception as e:
            print(f"× 设置权限时出错: {str(e)}")
            return False
    
    return True

def create_test_project():
    """创建测试项目目录"""
    print(f"\n===== 创建测试项目目录 =====")
    
    test_project_dir = os.path.join(DEFAULT_STORAGE_DIR, "test_project")
    print(f"测试项目目录: {test_project_dir}")
    
    # 创建测试项目目录
    try:
        if os.path.exists(test_project_dir):
            shutil.rmtree(test_project_dir)
            print(f"✓ 清理已存在的测试项目目录")
        
        os.makedirs(test_project_dir, exist_ok=True)
        print(f"✓ 创建测试项目目录成功")
        
        # 创建一些测试文件
        test_files = [
            {"path": "index.html", "content": "<html><body><h1>测试项目</h1></body></html>"},
            {"path": "styles.css", "content": "body { font-family: Arial; }"},
            {"path": "script.js", "content": "console.log('Hello, world!');"},
            {"path": "images/logo.txt", "content": "这是logo描述文件"},
            {"path": "src/main.py", "content": "print('Hello, world!')"},
            {"path": "docs/README.md", "content": "# 测试项目\n\n这是一个测试项目。"}
        ]
        
        for file_info in test_files:
            file_path = os.path.join(test_project_dir, file_info["path"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info["content"])
            print(f"  创建测试文件: {file_info['path']}")
        
        print(f"✓ 创建测试文件成功")
        return True
    except Exception as e:
        print(f"× 创建测试项目目录失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("\n======== 修复项目存储目录 ========")
    
    # 修复存储目录权限
    if not fix_storage_permissions():
        print("\n× 修复存储目录权限失败，请手动检查")
        return
    
    # 创建测试项目目录
    if not create_test_project():
        print("\n× 创建测试项目目录失败，请手动检查")
        return
    
    print("\n✓ 修复完成！请重启应用并测试文件上传功能")

if __name__ == "__main__":
    main() 