"""
安装项目所需的所有依赖

此脚本可检测依赖变化并智能地决定是否需要安装依赖，
通过比较依赖列表的哈希值，避免每次运行时都重新安装所有依赖。
使用uv作为包管理器，速度更快、依赖解析更好。
"""
import subprocess
import sys
import os
import json
import hashlib

def ensure_uv():
    """确保uv已安装且正常工作"""
    try:
        # 检查uv是否可用
        subprocess.check_call([sys.executable, "-m", "uv", "--version"], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("警告: uv不可用，尝试安装...")
        try:
            # 安装uv
            subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"],
                                 stderr=subprocess.DEVNULL)
            print("uv安装成功!")
            return True
        except subprocess.CalledProcessError:
            print("错误: 无法安装uv，请手动运行:")
            print(f"{sys.executable} -m pip install uv")
            return False

def install_tomli():
    """确保 tomli 库已安装"""
    try:
        import tomli
        return True
    except ImportError:
        print("安装 tomli 库用于解析 pyproject.toml...")
        if not ensure_uv():
            print("错误: 无法安装tomli，因为uv不可用")
            return False
        
        try:
            subprocess.check_call([sys.executable, "-m", "uv", "pip", "install", "tomli"])
            return True
        except subprocess.CalledProcessError as e:
            print(f"错误: 安装tomli失败: {e}")
            return False

def read_dependencies():
    """从pyproject.toml中读取依赖列表"""
    packages = []
    
    # 确保 tomli 已安装
    if not install_tomli():
        print("错误: 无法安装tomli，无法读取pyproject.toml")
        return packages
    
    try:
        import tomli
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pyproject_path = os.path.join(script_dir, "pyproject.toml")
        
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)
            if "dependencies" in data.get("project", {}):
                packages = data["project"]["dependencies"]
                # 确保tomli在列表中
                if not any(pkg.startswith("tomli") for pkg in packages):
                    packages.append("tomli>=2.0.0")
                print(f"从{pyproject_path}中读取依赖列表")
            else:
                print(f"警告: {pyproject_path}中未找到依赖项列表")
    except (FileNotFoundError, KeyError, ImportError) as e:
        print(f"错误: 无法从pyproject.toml读取依赖: {e}")
    
    return packages

def calculate_deps_hash(packages):
    """计算依赖的哈希值
    
    Args:
        packages: 依赖包列表
        
    Returns:
        依赖列表的MD5哈希值
    """
    deps_str = json.dumps(sorted(packages), sort_keys=True)
    return hashlib.md5(deps_str.encode()).hexdigest()

def check_deps_changed():
    """检查依赖是否变化
    
    通过比较当前依赖列表与之前保存的哈希值，
    检测依赖是否发生变化。
    
    Returns:
        True如果依赖变化或之前没有保存哈希，否则False
    """
    packages = read_dependencies()
    
    # 如果无法读取依赖，则强制安装
    if not packages:
        print("警告: 未读取到任何依赖，将强制进行安装步骤")
        return True
        
    current_hash = calculate_deps_hash(packages)
    
    # 使用脚本目录下的哈希文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hash_file = os.path.join(script_dir, ".deps_hash.txt")
    
    if not os.path.exists(hash_file):
        # 哈希文件不存在，认为依赖已变化
        with open(hash_file, "w") as f:
            f.write(current_hash)
        return True
    
    # 读取上次的哈希值
    with open(hash_file, "r") as f:
        previous_hash = f.read().strip()
    
    # 比较哈希值
    if current_hash != previous_hash:
        # 依赖变化，更新哈希文件
        with open(hash_file, "w") as f:
            f.write(current_hash)
        return True
    
    return False

def install_packages(force=False):
    """安装所需的依赖包
    
    Args:
        force: 是否强制安装依赖，即使它们没有变化
    """
    # 确保uv可用
    if not ensure_uv():
        print("错误: 无法继续安装依赖，因为uv不可用")
        return False
    
    # 检查依赖是否变化
    if not force and not check_deps_changed():
        print("依赖没有变化，跳过安装步骤")
        return True
    
    packages = read_dependencies()
    
    print("正在安装必要的依赖...")
    success_count = 0
    for package in packages:
        print(f"安装 {package}")
        try:
            subprocess.check_call([sys.executable, "-m", "uv", "pip", "install", package])
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"警告: 安装 {package} 时出错: {e}")
            print("继续安装其他依赖...")
    
    if success_count == len(packages):
        print("所有依赖安装完成！")
        
        # 对关键依赖进行验证检查
        critical_modules = ["aiofiles", "fastapi", "sqlalchemy", "pydantic"]
        missing_modules = []
        
        for module in critical_modules:
            try:
                # 尝试导入模块
                subprocess.check_call(
                    [sys.executable, "-c", f"import {module}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"警告: 以下关键模块可能未正确安装: {', '.join(missing_modules)}")
            print("尝试单独安装这些模块...")
            
            for module in missing_modules:
                try:
                    subprocess.check_call([sys.executable, "-m", "uv", "pip", "install", module])
                    print(f"模块 {module} 已成功安装")
                except subprocess.CalledProcessError:
                    print(f"错误: 无法安装模块 {module}")
        
        return True
    else:
        print(f"安装完成，但有 {len(packages) - success_count} 个依赖安装失败")
        return success_count > 0

if __name__ == "__main__":
    # 检查命令行参数
    force_install = "--force" in sys.argv
    success = install_packages(force=force_install)
    if not success:
        sys.exit(1) 