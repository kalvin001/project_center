import os
import tempfile
import zipfile
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.database import Base, engine, get_db
from app.models.user import User
from app.models.project import Project
from sqlalchemy.orm import Session

client = TestClient(app)

def setup_module(module):
    """测试前的准备工作"""
    # 创建测试数据库
    Base.metadata.create_all(bind=engine)
    
    # 创建测试用户
    with Session(engine) as session:
        # 检查是否已存在测试用户
        if not session.query(User).filter(User.username == "testuser").first():
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
                is_active=True,
                is_admin=False
            )
            session.add(user)
            session.commit()

def teardown_module(module):
    """测试后的清理工作"""
    # 删除测试项目目录
    if os.path.exists(settings.PROJECTS_DIR):
        for item in os.listdir(settings.PROJECTS_DIR):
            item_path = os.path.join(settings.PROJECTS_DIR, item)
            if os.path.isdir(item_path):
                try:
                    for subitem in os.listdir(item_path):
                        sub_path = os.path.join(item_path, subitem)
                        if os.path.isdir(sub_path):
                            os.rmdir(sub_path)
                        else:
                            os.remove(sub_path)
                    os.rmdir(item_path)
                except:
                    pass

def get_token():
    """获取测试用户的token"""
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "secret"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_project_upload():
    """测试项目上传功能"""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 创建项目
    project_data = {
        "name": "测试项目",
        "description": "这是一个测试项目",
        "project_type": "frontend"
    }
    response = client.post("/api/projects/", headers=headers, json=project_data)
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # 创建一个简单的ZIP文件用于测试
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
            zipf.writestr('test.txt', 'This is a test file.')
            zipf.writestr('index.html', '<html><body>Hello World</body></html>')
        
        # 上传ZIP文件
        with open(temp_zip.name, 'rb') as f:
            response = client.post(
                f"/api/projects/upload/{project_id}",
                headers=headers,
                files={"file": ("test.zip", f, "application/zip")}
            )
        
        # 清理临时文件
        os.unlink(temp_zip.name)
    
    assert response.status_code == 200
    
    # 检查项目详情
    response = client.get(f"/api/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    
    # 检查文件列表
    response = client.get(f"/api/projects/{project_id}/files", headers=headers)
    assert response.status_code == 200
    files_data = response.json()
    
    # 验证文件是否存在
    file_names = [f["name"] for f in files_data["files"]]
    assert "test.txt" in file_names
    assert "index.html" in file_names
    
    # 检查文件内容
    response = client.get(
        f"/api/projects/{project_id}/files/content",
        headers=headers,
        params={"file_path": "test.txt"}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "This is a test file."
    
    print("项目上传测试成功完成!") 