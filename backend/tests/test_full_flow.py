#!/usr/bin/env python
"""
完整流程测试脚本

测试从创建项目到上传文件和浏览文件的完整流程
"""

import os
import sys
import json
import tempfile
import zipfile
import requests
from pathlib import Path
from datetime import datetime

# API基础URL
API_URL = "http://localhost:8011/api"

def login(username, password):
    """登录获取令牌"""
    print("\n===== 登录获取令牌 =====")
    try:
        login_data = {
            "username": username,
            "password": password
        }
        print(f"发送登录请求: {login_data}")
        response = requests.post(
            f"{API_URL}/auth/login", 
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        print(f"✓ 登录成功，获取到令牌")
        return token
    except Exception as e:
        print(f"× 登录失败: {str(e)}")
        if hasattr(response, 'text'):
            print(f"响应内容: {response.text}")
        return None

def create_project(token, project_name, project_description):
    """创建项目"""
    print(f"\n===== 创建项目 {project_name} =====")
    try:
        project_data = {
            "name": project_name,
            "description": project_description,
            "project_type": "web",
            "repository_url": None,
            "is_active": True
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_URL}/projects", json=project_data, headers=headers)
        response.raise_for_status()
        project = response.json()
        print(f"✓ 成功创建项目: {project['name']} (ID: {project['id']})")
        return project
    except Exception as e:
        print(f"× 创建项目失败: {str(e)}")
        if hasattr(response, 'text'):
            print(f"响应内容: {response.text}")
        return None

def create_test_zip():
    """创建测试ZIP文件"""
    print("\n===== 创建测试ZIP文件 =====")
    try:
        # 创建临时目录用于准备ZIP内容
        temp_dir = tempfile.mkdtemp()
        print(f"创建临时目录: {temp_dir}")
        
        # 创建测试文件
        files_to_create = [
            {"path": "index.html", "content": "<html><body><h1>测试项目</h1></body></html>"},
            {"path": "styles.css", "content": "body { font-family: Arial; }"},
            {"path": "script.js", "content": "console.log('Hello, world!');"},
            {"path": "images/logo.txt", "content": "这是logo描述文件"},
            {"path": "src/main.py", "content": "print('Hello, world!')"},
            {"path": "docs/README.md", "content": "# 测试项目\n\n这是一个测试项目。"}
        ]
        
        for file_info in files_to_create:
            file_path = os.path.join(temp_dir, file_info["path"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info["content"])
            print(f"  创建测试文件: {file_info['path']}")
        
        # 创建ZIP文件
        zip_path = os.path.join(temp_dir, "test_project.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file == "test_project.zip":  # 跳过ZIP文件本身
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
                    print(f"  添加到ZIP: {arcname}")
        
        print(f"✓ 成功创建测试ZIP文件: {zip_path}")
        return zip_path, temp_dir
    except Exception as e:
        print(f"× 创建测试ZIP文件失败: {str(e)}")
        return None, None

def upload_project_files(token, project_id, zip_path):
    """上传项目文件"""
    print(f"\n===== 上传项目文件 =====")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # 删除Authorization头中的Content-Type，让请求自动设置为multipart/form-data
        with open(zip_path, 'rb') as zip_file:
            files = {"file": (os.path.basename(zip_path), zip_file, 'application/zip')}
            data = {"mode": "replace"}
            
            response = requests.post(
                f"{API_URL}/projects/upload/{project_id}", 
                headers=headers,
                files=files,
                data=data
            )
            
        response.raise_for_status()
        print(f"✓ 成功上传项目文件")
        return True
    except Exception as e:
        print(f"× 上传项目文件失败: {str(e)}")
        if hasattr(response, 'text'):
            print(f"响应内容: {response.text}")
        return False

def list_project_files(token, project_id, path=""):
    """列出项目文件"""
    print(f"\n===== 获取项目文件列表 (路径: '{path}') =====")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"path": path}
        response = requests.get(f"{API_URL}/projects/{project_id}/files", headers=headers, params=params)
        response.raise_for_status()
        file_list = response.json()
        
        print(f"当前路径: {file_list['current_path']}")
        
        if file_list.get('is_empty', False):
            print("目录为空")
            return file_list
        
        print("\n目录:")
        for directory in file_list["directories"]:
            print(f"  📁 {directory['name']} ({directory['path']})")
        
        print("\n文件:")
        for file in file_list["files"]:
            print(f"  📄 {file['name']} ({file['path']}) - {file['size']} 字节")
        
        return file_list
    except Exception as e:
        print(f"× 获取项目文件列表失败: {str(e)}")
        if hasattr(response, 'text'):
            print(f"响应内容: {response.text}")
        return None

def fetch_file_content(token, project_id, file_path):
    """获取文件内容"""
    print(f"\n===== 获取文件内容 (文件: '{file_path}') =====")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"path": file_path}
        response = requests.get(f"{API_URL}/projects/{project_id}/files/content", headers=headers, params=params)
        response.raise_for_status()
        file_content = response.json()
        
        print(f"文件名: {file_content['name']}")
        print(f"大小: {file_content['size']} 字节")
        print(f"修改时间: {file_content['modified']}")
        print(f"内容前100个字符: {file_content['content'][:100]}")
        
        return file_content
    except Exception as e:
        print(f"× 获取文件内容失败: {str(e)}")
        if hasattr(response, 'text'):
            print(f"响应内容: {response.text}")
        return None

def main():
    """主函数"""
    print("\n======== 项目完整流程测试 ========")
    
    # 设置用户凭据 - 使用正确的密码
    username = "admin"
    password = "12345678"
    
    # 登录获取令牌
    token = login(username, password)
    if not token:
        print("登录失败，无法继续测试")
        return
    
    # 创建测试项目
    project_name = f"测试项目 {datetime.now().strftime('%Y%m%d%H%M%S')}"
    project = create_project(token, project_name, "这是一个自动创建的测试项目")
    if not project:
        print("创建项目失败，无法继续测试")
        return
    
    project_id = project["id"]
    
    # 创建测试ZIP文件
    zip_path, temp_dir = create_test_zip()
    if not zip_path:
        print("创建测试ZIP文件失败，无法继续测试")
        return
    
    # 上传项目文件
    upload_success = upload_project_files(token, project_id, zip_path)
    if not upload_success:
        print("上传项目文件失败，无法继续测试")
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        return
    
    # 列出根目录文件
    root_files = list_project_files(token, project_id)
    if not root_files:
        print("获取根目录文件列表失败")
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        return
    
    # 检查images目录
    images_files = list_project_files(token, project_id, "images")
    
    # 检查src目录
    src_files = list_project_files(token, project_id, "src")
    
    # 获取README.md文件内容
    if root_files and not root_files.get('is_empty', False):
        for directory in root_files.get("directories", []):
            if directory["name"] == "docs":
                docs_files = list_project_files(token, project_id, "docs")
                if docs_files and not docs_files.get('is_empty', False):
                    for file in docs_files.get("files", []):
                        if file["name"] == "README.md":
                            readme_content = fetch_file_content(token, project_id, "docs/README.md")
    
    # 清理临时目录
    if temp_dir and os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n✓ 清理临时目录: {temp_dir}")
    
    print("\n======== 测试完成 ========")

if __name__ == "__main__":
    main() 