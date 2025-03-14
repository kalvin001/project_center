#!/usr/bin/env python
"""
项目存储目录调试脚本

这个脚本用于检查和修复项目存储目录的权限问题，并测试文件上传功能。
"""

import os
import sys
import tempfile
import zipfile
import shutil
import stat
from pathlib import Path
import datetime
import traceback
import json

# 将当前目录添加到路径，以便能够导入app模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.project import Project

def print_separator(title):
    """打印分隔符"""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)

def check_directory_permissions(directory_path):
    """检查目录的权限"""
    try:
        path = Path(directory_path)
        
        # 确保目录存在
        if not path.exists():
            print(f"目录不存在: {path}")
            try:
                os.makedirs(path, exist_ok=True)
                print(f"已创建目录: {path}")
            except Exception as e:
                print(f"创建目录失败: {e}")
                return False
        
        # 检查是否是目录
        if not path.is_dir():
            print(f"路径不是目录: {path}")
            return False
        
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
            return False
        
        # 检查写权限
        if os.access(path, os.W_OK):
            print("✓ 有写入权限")
        else:
            print("✗ 没有写入权限")
            return False
        
        # 检查执行权限
        if os.access(path, os.X_OK):
            print("✓ 有执行权限")
        else:
            print("✗ 没有执行权限")
            # 在Windows上，文件夹可能没有执行权限但仍然可以使用
            if os.name != 'nt':
                return False
        
        return True
    
    except Exception as e:
        print(f"检查权限时发生错误: {str(e)}")
        return False

def test_create_project_directory():
    """测试项目目录创建"""
    print_separator("测试项目目录创建")
    
    project_id = f"test_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    storage_path = str(settings.PROJECTS_DIR / project_id)
    
    print(f"项目根目录: {settings.PROJECTS_DIR}")
    print(f"测试项目目录: {storage_path}")
    
    # 确保根目录存在
    if not check_directory_permissions(settings.PROJECTS_DIR):
        print("项目根目录存在权限问题，请检查!")
        return False
    
    # 创建测试项目目录
    try:
        os.makedirs(storage_path, exist_ok=True)
        print(f"成功创建项目目录: {storage_path}")
        
        # 检查新创建的目录权限
        if not check_directory_permissions(storage_path):
            print("新创建的项目目录存在权限问题!")
            return False
        
        # 创建测试文件
        test_file_path = os.path.join(storage_path, "test_file.txt")
        with open(test_file_path, "w") as f:
            f.write("这是一个测试文件，用于验证项目目录的写入权限。")
        
        print(f"成功创建测试文件: {test_file_path}")
        
        # 读取测试文件
        with open(test_file_path, "r") as f:
            content = f.read()
        
        print(f"成功读取测试文件，内容: {content[:30]}...")
        
        return True
    
    except Exception as e:
        print(f"创建项目目录时发生错误: {str(e)}")
        traceback.print_exc()
        return False
    
    finally:
        # 清理测试目录
        try:
            shutil.rmtree(storage_path)
            print(f"已清理测试目录: {storage_path}")
        except Exception as e:
            print(f"清理测试目录失败: {str(e)}")

def test_upload_file():
    """测试文件上传和解压"""
    print_separator("测试文件上传和解压")
    
    project_id = f"test_upload_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    storage_path = str(settings.PROJECTS_DIR / project_id)
    
    print(f"测试项目目录: {storage_path}")
    
    try:
        # 创建项目目录
        os.makedirs(storage_path, exist_ok=True)
        print(f"成功创建项目目录: {storage_path}")
        
        # 创建测试ZIP文件
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w') as zipf:
                # 添加几个测试文件
                zipf.writestr('index.html', '<html><body><h1>测试项目</h1></body></html>')
                zipf.writestr('styles.css', 'body { font-family: Arial; color: #333; }')
                zipf.writestr('script.js', 'console.log("Hello, World!");')
                # 添加子目录和文件
                zipf.writestr('images/logo.txt', '这是项目的logo')
            
            zip_path = tmp_file.name
            print(f"创建测试ZIP文件: {zip_path}")
        
        # 解压文件到项目目录
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"ZIP文件中包含 {len(file_list)} 个文件:")
            for file_name in file_list:
                print(f" - {file_name}")
            
            zip_ref.extractall(storage_path)
        
        print(f"已解压文件到项目目录: {storage_path}")
        
        # 检查解压结果
        extracted_files = []
        for root, dirs, files in os.walk(storage_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), storage_path)
                extracted_files.append(rel_path.replace('\\', '/'))  # 统一路径分隔符
        
        print(f"\n解压后的文件列表:")
        for file in extracted_files:
            print(f" - {file}")
        
        # 验证解压结果
        expected_files = ['index.html', 'styles.css', 'script.js', 'images/logo.txt']
        missing_files = [f for f in expected_files if f not in extracted_files]
        
        if missing_files:
            print(f"\n❌ 缺少以下文件: {missing_files}")
            return False
        else:
            print("\n✓ 所有文件解压成功!")
            return True
    
    except Exception as e:
        print(f"测试上传文件时发生错误: {str(e)}")
        traceback.print_exc()
        return False
    
    finally:
        # 清理测试目录和临时文件
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
                print(f"已删除临时ZIP文件: {zip_path}")
            
            if os.path.exists(storage_path):
                shutil.rmtree(storage_path)
                print(f"已清理测试目录: {storage_path}")
        except Exception as e:
            print(f"清理临时文件失败: {str(e)}")

def fix_storage_permissions():
    """修复存储目录权限"""
    print_separator("修复存储目录权限")
    
    projects_dir = settings.PROJECTS_DIR
    print(f"项目根目录: {projects_dir}")
    
    try:
        # 确保目录存在
        os.makedirs(projects_dir, exist_ok=True)
        
        # 在Windows上设置完全控制权限
        if os.name == 'nt':
            import subprocess
            
            # 使用icacls命令授予当前用户完全控制权限
            current_user = os.environ.get('USERNAME')
            command = f'icacls "{projects_dir}" /grant "{current_user}:(OI)(CI)F" /T'
            print(f"执行命令: {command}")
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("成功设置权限!")
                print(result.stdout)
            else:
                print("设置权限失败!")
                print(f"错误: {result.stderr}")
                return False
        else:
            # 在类Unix系统上设置权限
            os.chmod(projects_dir, 0o755)  # rwxr-xr-x
            
            # 设置子目录和文件的权限
            for root, dirs, files in os.walk(projects_dir):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o755)  # rwxr-xr-x
                for f in files:
                    os.chmod(os.path.join(root, f), 0o644)  # rw-r--r--
            
            print("成功设置权限!")
        
        return True
    
    except Exception as e:
        print(f"修复权限时发生错误: {str(e)}")
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print_separator("开始诊断项目存储问题")
    
    # 确保项目根目录存在
    os.makedirs(settings.PROJECTS_DIR, exist_ok=True)
    
    # 列出当前已有的项目目录
    print(f"当前已有的项目目录:")
    try:
        for item in os.listdir(settings.PROJECTS_DIR):
            path = os.path.join(settings.PROJECTS_DIR, item)
            if os.path.isdir(path):
                print(f" - {item}")
    except Exception as e:
        print(f"列出目录时发生错误: {str(e)}")
    
    # 检查项目根目录权限
    print("\n检查项目根目录权限...")
    root_perm_ok = check_directory_permissions(settings.PROJECTS_DIR)
    
    # 测试项目目录创建
    dir_create_ok = test_create_project_directory()
    
    # 测试文件上传
    upload_ok = test_upload_file()
    
    # 总结测试结果
    print_separator("测试结果汇总")
    print(f"1. 项目根目录权限检查: {'✓ 通过' if root_perm_ok else '❌ 失败'}")
    print(f"2. 项目目录创建测试: {'✓ 通过' if dir_create_ok else '❌ 失败'}")
    print(f"3. 文件上传测试: {'✓ 通过' if upload_ok else '❌ 失败'}")
    
    # 如果任何测试失败，尝试修复权限
    if not (root_perm_ok and dir_create_ok and upload_ok):
        print("\n检测到问题，尝试修复存储目录权限...")
        fix_storage_permissions()
        
        # 重新测试
        print("\n修复后重新测试...")
        retest_dir_create = test_create_project_directory()
        retest_upload = test_upload_file()
        
        print_separator("修复后测试结果")
        print(f"1. 项目目录创建重测: {'✓ 通过' if retest_dir_create else '❌ 失败'}")
        print(f"2. 文件上传重测: {'✓ 通过' if retest_upload else '❌ 失败'}")
        
        if retest_dir_create and retest_upload:
            print("\n✓ 问题已解决! 请重启应用并尝试创建和上传项目。")
        else:
            print("\n❌ 问题仍然存在，建议检查以下几点:")
            print(" - 确保当前用户对项目目录有完全控制权限")
            print(" - 检查是否有杀毒软件或防火墙阻止文件操作")
            print(" - 检查磁盘空间是否充足")
            print(" - 尝试以管理员身份运行应用")
    else:
        print("\n✓ 所有测试通过! 存储功能应该可以正常工作。")
        print("如果问题仍然存在，请检查应用的其他组件，如前后端通信。")

if __name__ == "__main__":
    run_all_tests() 