import asyncio
import pytest
import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 从测试文件导入所有测试
from tests.test_sync_project import (
    test_sync_project_task_success,
    test_sync_project_task_directory_not_exist,
    test_sync_project_task_not_git_repo,
    test_sync_project_task_exception,
    test_sync_project_task_deployment_not_found
)

# 主测试函数
async def run_all_tests():
    """运行所有sync_project_task相关的测试"""
    print("开始运行sync_project_task相关测试...")
    
    # 使用pytest运行测试
    result = await asyncio.to_thread(
        pytest.main, 
        ["-xvs", "tests/test_sync_project.py"]
    )
    
    if result == 0:
        print("所有测试通过!")
    else:
        print(f"测试失败，退出代码: {result}")
    
    return result

# 运行测试
if __name__ == "__main__":
    asyncio.run(run_all_tests()) 