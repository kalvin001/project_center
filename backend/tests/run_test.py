"""
直接运行此文件即可执行测试
"""
import os
import sys
import pytest

if __name__ == "__main__":
    print("正在运行sync_project_task测试...")
    # 在当前目录下运行测试
    pytest.main(["-xvs", "test_sync_project.py"]) 