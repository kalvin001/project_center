"""
安装项目所需的所有依赖

此脚本可检测依赖变化并智能地决定是否需要安装依赖，
通过比较依赖列表的哈希值，避免每次运行时都重新安装所有依赖。
"""
import subprocess
import sys
import os
import json
import hashlib

def ensure_pip():
    """确保pip已安装且正常工作"""
    try:
        # 检查pip是否可用
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("警告: pip不可用，尝试安装/修复...")
        try:
            # 尝试使用ensurepip模块安装pip
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"], 
                                 stderr=subprocess.DEVNULL)
            print("pip安装成功!")
            return True
        except (subprocess.CalledProcessError, ImportError):
            print("错误: 无法安装pip，请手动运行:")
            print(f"{sys.executable} -m ensurepip --upgrade")
            print("或下载get-pip.py并运行:")
            print(f"{sys.executable} get-pip.py")
            return False

def install_tomli():
    """确保 tomli 库已安装"""
    try:
        import tomli
        return True
    except ImportError:
        print("安装 tomli 库用于解析 pyproject.toml...")
        if not ensure_pip():
            print("错误: 无法安装tomli，因为pip不可用")
            return False
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "tomli"])
            return True
        except subprocess.CalledProcessError as e:
            print(f"错误: 安装tomli失败: {e}")
            return False

def read_dependencies():
    """从pyproject.toml中读取依赖列表"""
    packages = [
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-multipart>=0.0.5",
        "aiosqlite>=0.19.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "email-validator>=2.0.0",
        "tomli>=2.0.0",  # 确保包含tomli库
        "pathspec"
    ]
    
    # 尝试从pyproject.toml中读取依赖（如果这个函数在将来更新）
    try:
        # 确保 tomli 已安装
        if not install_tomli():
            print("警告: 无法安装tomli，使用默认依赖列表")
            return packages
        
        import tomli
        with open("pyproject.toml", "rb") as f:
            data = tomli.load(f)
            if "dependencies" in data.get("project", {}):
                packages = data["project"]["dependencies"]
                # 确保tomli在列表中
                if not any(pkg.startswith("tomli") for pkg in packages):
                    packages.append("tomli>=2.0.0")
                print("从pyproject.toml中读取依赖列表")
    except (FileNotFoundError, KeyError, ImportError) as e:
        print(f"使用内置依赖列表: {e}")
    
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
    current_hash = calculate_deps_hash(packages)
    
    hash_file = ".deps_hash.txt"
    
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
    # 确保pip可用
    if not ensure_pip():
        print("错误: 无法继续安装依赖，因为pip不可用")
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
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"警告: 安装 {package} 时出错: {e}")
            print("继续安装其他依赖...")
    
    if success_count == len(packages):
        print("所有依赖安装完成！")
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