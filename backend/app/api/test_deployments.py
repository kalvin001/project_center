import pytest
from httpx import AsyncClient
from app.config import settings
from app.database.session import async_session_factory
from app.utils.token import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.project import Project
from app.models.machine import Machine
from app.models.deployment import Deployment

# 测试辅助函数
async def create_test_user(db: AsyncSession):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        is_active=True
    )
    user.set_password("testpassword")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_test_project(db: AsyncSession, user_id: int):
    """创建测试项目"""
    project = Project(
        name="Test Project",
        description="Test Project Description",
        git_url="https://github.com/test/test.git",
        owner_id=user_id
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

async def create_test_machine(db: AsyncSession, user_id: int):
    """创建测试部署机器"""
    machine = Machine(
        name="Test Machine",
        description="Test Machine Description",
        host="localhost",
        port=22,
        username="testuser",
        password="testpassword",
        owner_id=user_id
    )
    db.add(machine)
    await db.commit()
    await db.refresh(machine)
    return machine

async def create_test_deployment(db: AsyncSession, project_id: int, machine_id: int):
    """创建测试部署记录"""
    deployment = Deployment(
        name="Test Deployment",
        description="Test Deployment Description",
        project_id=project_id,
        machine_id=machine_id,
        deployment_path="/tmp/test_deployment",
        status="success"
    )
    db.add(deployment)
    await db.commit()
    await db.refresh(deployment)
    return deployment

@pytest.mark.asyncio
async def test_get_deployment_files(client: AsyncClient, test_db):
    """测试获取部署文件列表接口"""
    # 创建测试用户
    user = await create_test_user(test_db)
    
    # 创建测试项目
    project = await create_test_project(test_db, user.id)
    
    # 创建测试部署机器
    machine = await create_test_machine(test_db, user.id)
    
    # 创建测试部署记录
    deployment = await create_test_deployment(test_db, project.id, machine.id)
    
    # 创建测试目录结构
    import os
    import tempfile
    
    # 设置测试部署目录
    test_deployment_dir = os.path.join(settings.project_root_dir, f"test_deployment_{deployment.id}")
    os.makedirs(test_deployment_dir, exist_ok=True)
    
    # 创建测试子目录
    test_subdir = os.path.join(test_deployment_dir, "subdir")
    os.makedirs(test_subdir, exist_ok=True)
    
    # 创建测试文件
    with open(os.path.join(test_deployment_dir, "test.txt"), "w") as f:
        f.write("测试文件内容")
    
    with open(os.path.join(test_subdir, "subfile.txt"), "w") as f:
        f.write("子目录文件内容")
    
    # 更新部署记录的路径
    async with async_session_factory() as session:
        deployment.deployment_path = test_deployment_dir
        session.add(deployment)
        await session.commit()
    
    # 获取访问令牌
    token = create_access_token(data={"sub": user.username})
    
    try:
        # 测试获取根目录文件列表
        response = await client.get(
            f"/api/deployments/{deployment.id}/files",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "directories" in data
        assert "files" in data
        assert len(data["directories"]) == 1  # 有一个子目录
        assert len(data["files"]) == 1  # 有一个测试文件
        assert data["directories"][0]["name"] == "subdir"
        assert data["files"][0]["name"] == "test.txt"
        
        # 测试获取子目录文件列表
        response = await client.get(
            f"/api/deployments/{deployment.id}/files?path=subdir",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["directories"]) == 0  # 子目录中没有目录
        assert len(data["files"]) == 1  # 子目录中有一个文件
        assert data["files"][0]["name"] == "subfile.txt"
        
        # 测试获取文件内容
        response = await client.get(
            f"/api/deployments/{deployment.id}/file?file_path=test.txt",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file_name"] == "test.txt"
        assert data["content"] == "测试文件内容"
        
        # 测试获取子目录文件内容
        response = await client.get(
            f"/api/deployments/{deployment.id}/file?file_path=subdir/subfile.txt",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file_name"] == "subfile.txt"
        assert data["content"] == "子目录文件内容"
        
    finally:
        # 清理测试文件和目录
        import shutil
        if os.path.exists(test_deployment_dir):
            shutil.rmtree(test_deployment_dir) 