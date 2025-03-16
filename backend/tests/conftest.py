"""
测试配置文件，用于设置 pytest 相关环境
"""

import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"已添加路径: {parent_dir}")

# 打印当前路径信息，用于调试
print(f"当前工作目录: {os.getcwd()}")
print(f"Python 路径: {sys.path}") 