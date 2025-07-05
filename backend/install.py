#!/usr/bin/env python
"""
项目依赖安装启动脚本
只需运行 `python backend/install.py` 即可从任何目录安装依赖
使用uv作为包管理器，比pip更快且依赖解析更好
"""

import os
import sys
import subprocess
import platform
import shutil

def main():
    """主函数"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查是否安装了uv
    try:
        subprocess.check_call(["uv", "--version"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        print("✓ 检测到uv已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("正在安装uv包管理器...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
            print("✓ uv安装成功")
        except subprocess.CalledProcessError:
            print("❌ 无法安装uv，请手动运行:")
            print(f"  {sys.executable} -m pip install uv")
            sys.exit(1)
    
    # 检查虚拟环境
    venv_dir = os.path.join(current_dir, ".venv")
    if not os.path.exists(venv_dir):
        print("创建虚拟环境...")
        try:
            subprocess.check_call([sys.executable, "-m", "uv", "venv", venv_dir])
            print(f"✓ 虚拟环境已创建在: {venv_dir}")
        except subprocess.CalledProcessError:
            print("❌ 创建虚拟环境失败")
            sys.exit(1)
    else:
        print(f"✓ 已存在虚拟环境: {venv_dir}")
    
    # 获取虚拟环境中的Python解释器路径
    if platform.system() == "Windows":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")
    
    # 安装开发模式下的当前包
    print("安装当前包(开发模式)...")
    try:
        subprocess.check_call([venv_python, "-m", "uv", "pip", "install", "-e", "."], cwd=current_dir)
        print("✓ 当前包已安装")
    except subprocess.CalledProcessError:
        print("❌ 安装当前包失败")
        sys.exit(1)
    
    # 构建install_deps.py的完整路径
    install_deps_path = os.path.join(current_dir, "install_deps.py")
    
    print(f"正在运行依赖安装脚本: {install_deps_path}")
    
    # 获取命令行参数
    args = sys.argv[1:]
    
    # 构建命令
    cmd = [venv_python, install_deps_path] + args
    
    # 执行install_deps.py
    try:
        subprocess.run(cmd, check=True)
        print("✓ 所有依赖安装完成")
    except subprocess.CalledProcessError:
        print("❌ 依赖安装过程中出现错误")
        sys.exit(1)
    
    print("\n安装完成! 可以使用以下命令启动项目:")
    if platform.system() == "Windows":
        print(f"  {venv_dir}\\Scripts\\python.exe -m app")
    else:
        print(f"  {venv_dir}/bin/python -m app")

if __name__ == "__main__":
    main() 