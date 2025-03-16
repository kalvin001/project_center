"""
运行项目测试
"""
import os
import sys
import pytest

if __name__ == "__main__":
    print("正在运行sync_project_task测试...")
    
    # 确保当前目录在Python路径中
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 运行测试
    pytest.main(["-xvs", "tests/test_sync_project.py"]) 