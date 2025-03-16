import asyncio
import os
import sys
import pytest
import unittest.mock as mock
from datetime import datetime

# 确保能正确导入app模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
print(f"已添加路径: {parent_dir}")

# 现在导入所需的模块
from app.api.deployments import sync_project_task
from app.models.project import Deployment, Project
from app.models.machine import Machine
from app.utils.ssh import SSHClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

# 创建测试用的mock数据
@pytest.fixture
def mock_deployment():
    """创建模拟的部署对象"""
    project = mock.MagicMock(spec=Project)
    project.id = 1
    project.name = "测试项目"
    project.repository_type = "git"
    
    machine = mock.MagicMock(spec=Machine)
    machine.id = 1
    machine.name = "测试机器"
    machine.host = "localhost"
    machine.port = 22
    machine.username = "test_user"
    machine.password = "test_password"
    
    deployment = mock.MagicMock(spec=Deployment)
    deployment.id = 1
    deployment.project_id = project.id
    deployment.machine_id = machine.id
    deployment.deploy_path = "/home/test_user/test_project"
    deployment.status = "pending"
    deployment.project = project
    deployment.machine = machine
    deployment.log = "初始日志"
    
    return deployment

@pytest.fixture
def mock_db_session():
    """创建模拟的数据库会话"""
    db_session = mock.AsyncMock(spec=AsyncSession)
    
    # 模拟execute方法的返回值
    mock_result = mock.MagicMock()
    mock_result.scalars.return_value.first.return_value = None  # 初始设为None，在测试中修改
    
    db_session.execute.return_value = mock_result
    db_session.begin.return_value.__aenter__.return_value = None
    db_session.begin.return_value.__aexit__.return_value = None
    
    return db_session

@pytest.fixture
def mock_ssh_client():
    """创建模拟的SSH客户端"""
    with mock.patch('app.api.deployments.SSHClient', autospec=True) as mock_ssh:
        ssh_instance = mock.AsyncMock(spec=SSHClient)
        mock_ssh.return_value = ssh_instance
        
        # 模拟连接方法
        ssh_instance.connect.return_value = None
        
        # 模拟命令执行方法 - 返回 (exit_status, stdout, stderr)
        ssh_instance.execute_command.return_value = (0, "命令执行成功", "")
        
        # 模拟关闭方法
        ssh_instance.close.return_value = None
        
        yield ssh_instance

@pytest.mark.asyncio
async def test_sync_project_task_success(mock_deployment, mock_db_session, mock_ssh_client):
    """测试成功同步项目的情况"""
    # 设置数据库查询结果为mock_deployment
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_deployment
    
    # 设置ssh客户端返回值
    mock_ssh_client.execute_command.side_effect = [
        # 检查目录是否存在
        (0, "EXISTS", ""),
        # 检查是否为git仓库
        (0, "true", ""),
        # 执行git pull
        (0, "Already up to date.", ""),
        # 列出目录内容
        (0, "package.json\nrequirements.txt", ""),
        # npm install
        (0, "npm install 成功", ""),
        # pip install
        (0, "pip install 成功", "")
    ]
    
    # 执行被测试的函数
    await sync_project_task(mock_deployment.id, mock_db_session)
    
    # 验证调用
    assert mock_ssh_client.connect.called
    assert mock_ssh_client.execute_command.call_count >= 3
    assert mock_ssh_client.close.called
    
    # 验证状态更新
    assert mock_deployment.status == "success"
    assert "同步完成" in mock_deployment.log
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_sync_project_task_directory_not_exist(mock_deployment, mock_db_session, mock_ssh_client):
    """测试目录不存在的情况"""
    # 设置数据库查询结果为mock_deployment
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_deployment
    
    # 设置ssh客户端返回值 - 目录不存在
    mock_ssh_client.execute_command.return_value = (0, "NOT_EXISTS", "")
    
    # 执行被测试的函数
    await sync_project_task(mock_deployment.id, mock_db_session)
    
    # 验证调用
    assert mock_ssh_client.connect.called
    assert mock_ssh_client.execute_command.called
    assert mock_ssh_client.close.called
    
    # 验证状态更新
    assert mock_deployment.status == "sync_failed"
    assert "目标目录不存在" in mock_deployment.log
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_sync_project_task_not_git_repo(mock_deployment, mock_db_session, mock_ssh_client):
    """测试不是git仓库的情况"""
    # 设置数据库查询结果为mock_deployment
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_deployment
    
    # 设置ssh客户端返回值
    mock_ssh_client.execute_command.side_effect = [
        # 检查目录是否存在
        (0, "EXISTS", ""),
        # 检查是否为git仓库 - 不是
        (0, "NOT_GIT", "")
    ]
    
    # 执行被测试的函数
    await sync_project_task(mock_deployment.id, mock_db_session)
    
    # 验证调用
    assert mock_ssh_client.connect.called
    assert mock_ssh_client.execute_command.call_count == 2
    assert mock_ssh_client.close.called
    
    # 验证状态更新
    assert mock_deployment.status == "sync_failed"
    assert "目录不是git仓库" in mock_deployment.log
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_sync_project_task_exception(mock_deployment, mock_db_session, mock_ssh_client):
    """测试发生异常的情况"""
    # 设置数据库查询结果为mock_deployment
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_deployment
    
    # 设置ssh客户端抛出异常
    mock_ssh_client.connect.side_effect = Exception("连接错误")
    
    # 执行被测试的函数
    await sync_project_task(mock_deployment.id, mock_db_session)
    
    # 验证状态更新
    assert mock_deployment.status == "sync_failed"
    assert "同步失败" in mock_deployment.log
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_sync_project_task_deployment_not_found(mock_db_session, mock_ssh_client):
    """测试部署记录不存在的情况"""
    # 设置数据库查询结果为None
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None
    
    # 执行被测试的函数
    await sync_project_task(999, mock_db_session)
    
    # 验证调用
    assert not mock_ssh_client.connect.called
    
    # 验证没有提交更改
    assert not mock_db_session.commit.called

if __name__ == "__main__":
    # 直接运行单个测试
    print("正在运行sync_project_task测试...")
    pytest.main(["-xvs", __file__]) 