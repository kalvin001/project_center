"""
项目启动脚本
用于启动前后端服务，在启动前会先终止占用相同端口的进程
"""

import os
import sys
import time
import subprocess
import logging
import signal
import socket
from datetime import datetime
import shutil
import platform
import argparse  # 添加argparse模块

# 设置控制台编码为UTF-8
if platform.system() == "Windows":
    # 尝试设置Windows控制台编码
    try:
        subprocess.run("chcp 65001", shell=True, check=True)
        os.system("") # 刷新控制台设置
    except:
        pass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # 明确指定日志编码
)
logger = logging.getLogger(__name__)

# 检查并安装psutil库
try:
    import psutil
except ImportError:
    logger.info("未检测到psutil库，正在安装...")
    subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], check=True)
    import psutil

# 检查并安装yaml库
try:
    import yaml
except ImportError:
    logger.info("未检测到yaml库，正在安装...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml"], check=True)
    import yaml

def get_script_dir():
    """获取脚本所在目录"""
    return os.path.dirname(os.path.abspath(__file__))

def ensure_dir(directory):
    """确保目录存在，如不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")

def read_config(config_file=None):
    """
    读取配置文件 
    如果config_reader.py不存在，则直接读取yaml文件
    """
    if config_file is None:
        config_file = os.path.join(get_script_dir(), 'config.yaml')
    
    logger.info(f"正在读取配置文件: {config_file}")
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        logger.error(f"错误：配置文件 {config_file} 不存在!")
        sys.exit(1)
    
    try:
        # 首先尝试导入config_reader模块
        try:
            from config_reader import read_config as reader_func
            return reader_func(config_file)
        except ImportError:
            logger.info("未找到config_reader模块，直接读取YAML配置文件")
            
            # 直接读取YAML配置文件
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 提取配置项到平面字典
            config = {}
            
            # 基本设置
            if '基本设置' in config_data:
                for key, value in config_data['基本设置'].items():
                    config[key] = value
            
            # 后端配置
            if '后端' in config_data:
                for key, value in config_data['后端'].items():
                    config[key] = value
            
            # 前端配置
            if '前端' in config_data:
                for key, value in config_data['前端'].items():
                    config[key] = value
            
            # 显示读取到的配置项
            for key, value in config.items():
                logger.info(f"已加载配置: {key}={value}")
            
            logger.info(f"成功加载了 {len(config)} 个配置项")
            
            # 检查必要的配置项
            required_configs = [
                'PROJECT_NAME', 'BACKEND_PORT', 'FRONTEND_PORT', 
                'BACKEND_HOST', 'FRONTEND_HOST', 'BACKEND_CMD', 
                'FRONTEND_CMD', 'BACKEND_WINDOW', 'FRONTEND_WINDOW'
            ]
            
            missing_configs = [config_name for config_name in required_configs if config_name not in config]
            
            if missing_configs:
                logger.error(f"错误：配置文件缺少必要的配置项: {', '.join(missing_configs)}")
                sys.exit(1)
            
            logger.info("配置已成功加载！")
            return config
            
    except yaml.YAMLError as e:
        logger.error(f"错误：配置文件格式错误 - {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"错误：读取配置文件时出错 - {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def is_port_in_use(port):
    """检查端口是否被占用，使用多种方式进行检测"""
    # 方法1: 尝试建立socket连接
    socket_check = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                socket_check = True
    except:
        pass
        
    # 方法2: 使用netstat命令检查（Windows系统）
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{port}"',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                return True
        except:
            pass
    
    return socket_check

def kill_process_by_port(port):
    """根据端口号杀死进程"""
    try:
        if platform.system() == "Windows":
            # Windows系统使用netstat查找端口占用
            result = subprocess.run(
                f'netstat -ano | findstr ":{port}"',
                shell=True,
                capture_output=True,
                text=True
            )
            
            killed_any = False
            # 解析输出找到PID
            for line in result.stdout.splitlines():
                if f":{port}" in line and ("LISTENING" in line or "已建立" in line or "ESTABLISHED" in line or "TCP" in line):
                    parts = line.strip().split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        logger.info(f"找到占用端口 {port} 的进程 PID: {pid}")
                        try:
                            # 尝试使用taskkill终止进程及其子进程
                            subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, check=True)
                            logger.info(f"已终止 PID 为 {pid} 的进程及其子进程")
                            killed_any = True
                        except subprocess.CalledProcessError:
                            logger.warning(f"无法终止 PID 为 {pid} 的进程")
            
            # 最后尝试netsh命令直接关闭端口连接
            if is_port_in_use(port):
                logger.info(f"尝试使用netsh强制关闭端口 {port}...")
                try:
                    subprocess.run(f"netsh interface ipv4 delete tcpconnection localport={port} protocol=tcp", shell=True)
                    time.sleep(1)
                    killed_any = True
                except Exception as e:
                    logger.error(f"使用netsh终止端口连接失败: {str(e)}")
            
            # 双重检查确保端口被释放
            if killed_any:
                logger.info(f"等待端口 {port} 完全释放 (2秒)...")
                time.sleep(2)
        else:
            # Linux/Mac 系统使用lsof查找端口占用
            result = subprocess.run(
                f"lsof -i :{port} -t",
                shell=True,
                capture_output=True,
                text=True
            )
            
            # 解析输出找到PID
            for pid in result.stdout.splitlines():
                if pid:
                    logger.info(f"找到占用端口 {port} 的进程 PID: {pid}")
                    try:
                        # 终止进程及其子进程
                        os.kill(int(pid), signal.SIGTERM)
                        logger.info(f"已终止 PID 为 {pid} 的进程")
                        
                        # 给进程一些时间来终止
                        time.sleep(1)
                        
                        # 如果进程还存在，强制终止
                        if psutil.pid_exists(int(pid)):
                            os.kill(int(pid), signal.SIGKILL)
                            logger.info(f"已强制终止 PID 为 {pid} 的进程")
                    except OSError:
                        logger.warning(f"无法终止 PID 为 {pid} 的进程")
                        
        # 最后验证端口是否已释放
        if is_port_in_use(port):
            logger.warning(f"警告：尽管尝试终止相关进程，但端口 {port} 仍被占用")
        else:
            logger.info(f"端口 {port} 已成功释放")
                        
    except Exception as e:
        logger.error(f"终止占用端口 {port} 的进程时出错: {str(e)}")

def check_backend_env():
    """检查后端环境"""
    logger.info("检查后端环境...")
    
    # 切换到后端目录
    backend_dir = os.path.join(get_script_dir(), 'backend')
    if not os.path.exists(backend_dir):
        logger.error(f"错误：后端目录 {backend_dir} 不存在！")
        sys.exit(1)
        
    os.chdir(backend_dir)
    
    venv_dir = os.path.join(backend_dir, '.venv')
    deps_checksum_file = os.path.join(backend_dir, '.deps_checksum.txt')
    deps_hash_file = os.path.join(backend_dir, '.deps_hash.txt')
    pyproject_file = os.path.join(backend_dir, 'pyproject.toml')
    
    if not os.path.exists(pyproject_file):
        logger.error(f"错误：后端项目文件 {pyproject_file} 不存在！")
        sys.exit(1)
    
    # 获取虚拟环境解释器路径
    if platform.system() == "Windows":
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:
        venv_python = os.path.join(venv_dir, 'bin', 'python')
    
    # 检查是否安装了uv
    logger.info("检查是否安装了uv...")
    try:
        subprocess.check_call(["uv", "--version"], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
        logger.info("uv已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.info("安装uv包管理器...")
        try:
            # 在Linux上使用系统包管理器安装uv
            if platform.system() == "Linux":
                subprocess.check_call(["pipx", "install", "uv"])
            else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
            logger.info("uv安装成功")
        except subprocess.CalledProcessError:
            logger.error("错误：安装uv失败，请手动安装")
            sys.exit(1)
    
    # 检查虚拟环境是否存在
    if not os.path.exists(venv_dir):
        logger.info("创建后端虚拟环境...")
        try:
            # 使用uv创建虚拟环境
            subprocess.check_call(["uv", "venv", venv_dir])
            logger.info(f"虚拟环境已创建在: {venv_dir}")
            
            # 安装开发模式下的后端项目
            logger.info("安装后端项目(开发模式)...")
            subprocess.check_call(["uv", "pip", "install", "-e", "."], cwd=backend_dir)
            
            # 强制运行install_deps.py安装所有依赖
            logger.info("安装所有依赖...")
            install_deps_script = os.path.join(backend_dir, 'install_deps.py')
            if os.path.exists(install_deps_script):
                try:
                    subprocess.check_call(
                        [venv_python, install_deps_script, "--force"], 
                        encoding='utf-8', 
                        errors='replace'
                    )
                    logger.info("所有依赖安装完成")
                except subprocess.CalledProcessError as e:
                    logger.error(f"依赖安装过程中出现错误: {e}")
                    logger.warning("继续执行，但部分功能可能不可用")
            else:
                logger.warning("未找到install_deps.py文件，可能缺少部分依赖")
        except subprocess.CalledProcessError as e:
            logger.error(f"错误：创建虚拟环境或安装依赖失败: {e}")
            sys.exit(1)
    else:
        logger.info("后端环境已存在，检查是否可用...")
        
        # 检查虚拟环境是否可用
        try:
            # 使用虚拟环境中的Python检查版本
            subprocess.check_call([venv_python, "--version"], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
            
            logger.info("后端环境正常，检查依赖是否变化...")
            
            # 检查依赖是否需要更新
            force_install = False
            
            # 情况1: pyproject.toml更新了但deps_checksum未更新
            if not os.path.exists(deps_checksum_file) or os.path.getmtime(pyproject_file) > os.path.getmtime(deps_checksum_file):
                logger.info("检测到pyproject.toml变化，需要更新依赖...")
                force_install = True
                # 更新校验文件
                with open(deps_checksum_file, 'w') as f:
                    f.write(f"上次更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 情况2: deps_hash.txt不存在或内容变化了
            install_deps_script = os.path.join(backend_dir, 'install_deps.py')
            if os.path.exists(install_deps_script):
                if not os.path.exists(deps_hash_file):
                    logger.info("依赖哈希文件不存在，需要重新安装依赖...")
                    force_install = True
                else:
                    # 尝试使用install_deps.py检查依赖是否变化
                    try:
                        result = subprocess.run(
                            [venv_python, install_deps_script], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            text=True,
                            encoding='utf-8',
                            errors='replace'  # 处理编码错误
                        )
                        # 检查result.stdout是否为None
                        if result.stdout and "依赖没有变化，跳过安装步骤" not in result.stdout:
                            logger.info("检测到依赖变化，需要更新...")
                            force_install = True
                    except Exception as e:
                        logger.warning(f"检查依赖时出错: {e}")
                        logger.info("为安全起见，强制更新依赖...")
                        force_install = True
            
            # 如果需要安装，就强制安装所有依赖
            if force_install:
                try:
                    logger.info("强制更新所有依赖...")
                    if os.path.exists(install_deps_script):
                        try:
                            subprocess.check_call(
                                [venv_python, install_deps_script, "--force"],
                                encoding='utf-8', 
                                errors='replace'
                            )
                            logger.info("所有依赖更新完成")
                        except subprocess.CalledProcessError as e:
                            logger.error(f"依赖更新过程中出现错误: {e}")
                            logger.warning("继续执行，但部分功能可能不可用")
                    else:
                        logger.warning("未找到install_deps.py文件，尝试使用uv直接更新...")
                        subprocess.check_call(["uv", "pip", "install", "-e", "."], cwd=backend_dir)
                except subprocess.CalledProcessError as e:
                    logger.error(f"错误：更新依赖失败: {e}")
            else:
                logger.info("依赖没有变化，跳过更新步骤")
                
        except subprocess.CalledProcessError:
            logger.warning("检测到虚拟环境损坏，尝试修复...")
            
            # 如果虚拟环境损坏，尝试重新创建
            try:
                # 删除损坏的虚拟环境
                if os.path.exists(venv_dir):
                    if platform.system() == "Windows":
                        subprocess.run(f"rmdir /s /q {venv_dir}", shell=True, check=True)
                    else:
                        shutil.rmtree(venv_dir)
                
                # 重新创建虚拟环境
                subprocess.check_call(["uv", "venv", venv_dir])
                
                # 安装开发模式下的后端项目
                subprocess.check_call(["uv", "pip", "install", "-e", "."], cwd=backend_dir)
                
                # 强制运行install_deps.py安装所有依赖
                install_deps_script = os.path.join(backend_dir, 'install_deps.py')
                if os.path.exists(install_deps_script):
                    try:
                        subprocess.check_call(
                            [venv_python, install_deps_script, "--force"],
                            encoding='utf-8', 
                            errors='replace'
                        )
                        logger.info("所有依赖安装完成")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"依赖安装过程中出现错误: {e}")
                        logger.warning("继续执行，但部分功能可能不可用")
                else:
                    logger.warning("未找到install_deps.py文件，可能缺少部分依赖")
            except subprocess.CalledProcessError as e:
                logger.error(f"错误：修复虚拟环境失败: {e}")
                sys.exit(1)
    
    logger.info("后端环境检查完成")

def check_frontend_env():
    """检查前端环境"""
    logger.info("检查前端环境...")
    
    # 切换到前端目录
    frontend_dir = os.path.join(get_script_dir(), 'frontend')
    if not os.path.exists(frontend_dir):
        logger.error(f"错误：前端目录 {frontend_dir} 不存在！")
        sys.exit(1)
        
    os.chdir(frontend_dir)
    
    node_modules_dir = os.path.join(frontend_dir, 'node_modules')
    pkg_checksum_file = os.path.join(frontend_dir, '.pkg_checksum.txt')
    package_json_file = os.path.join(frontend_dir, 'package.json')
    
    if not os.path.exists(package_json_file):
        logger.error(f"错误：前端项目文件 {package_json_file} 不存在！")
        sys.exit(1)
    
    # 检查依赖是否存在
    if not os.path.exists(node_modules_dir):
        logger.info("安装前端依赖...")
        
        # 安装pnpm
        subprocess.run("npm install -g pnpm", shell=True, check=True)
        
        # 安装依赖
        subprocess.run("pnpm install", shell=True, check=True)
        
        # 保存校验信息
        shutil.copy2(package_json_file, pkg_checksum_file)
    else:
        logger.info("前端环境已存在，检查依赖是否变化...")
        
        if not os.path.exists(pkg_checksum_file):
            logger.info("未找到前端依赖校验文件，需要重新安装依赖...")
            
            # 安装依赖
            subprocess.run("pnpm install", shell=True, check=True)
            
            # 保存校验信息
            shutil.copy2(package_json_file, pkg_checksum_file)
        else:
            # 比较package.json是否变化
            with open(package_json_file, 'rb') as f1, open(pkg_checksum_file, 'rb') as f2:
                if f1.read() != f2.read():
                    logger.info("检测到前端依赖变化，需要更新...")
                    
                    # 更新依赖
                    subprocess.run("pnpm install", shell=True, check=True)
                    
                    # 更新校验信息
                    shutil.copy2(package_json_file, pkg_checksum_file)
                else:
                    logger.info("前端依赖无变化，跳过安装步骤...")

def stop_services():
    """停止所有服务"""
    logger.info("停止所有服务...")
    
    try:
        # 获取配置文件中的端口
        config = read_config()
        backend_port = int(config['BACKEND_PORT'])
        frontend_port = int(config['FRONTEND_PORT'])
        
        # 检查并终止前端端口占用
        if is_port_in_use(frontend_port):
            logger.info(f"前端端口 {frontend_port} 被占用，正在终止...")
            kill_process_by_port(frontend_port)
        else:
            logger.info(f"前端端口 {frontend_port} 未被占用")
                
        # 检查并终止后端端口占用
        if is_port_in_use(backend_port):
            logger.info(f"后端端口 {backend_port} 被占用，正在终止...")
            kill_process_by_port(backend_port)
        else:
            logger.info(f"后端端口 {backend_port} 未被占用")
        
        # 最终检查
        time.sleep(1)  # 等待进程完全终止
        ports_still_in_use = []
        if is_port_in_use(backend_port):
            ports_still_in_use.append(f"后端({backend_port})")
        if is_port_in_use(frontend_port):
            ports_still_in_use.append(f"前端({frontend_port})")
            
        if ports_still_in_use:
            logger.warning(f"以下端口仍被占用: {', '.join(ports_still_in_use)}")
        else:
            logger.info("所有端口已成功释放")
        
        # 删除PID文件 - 仅作记录用，不影响实际终止进程
        logs_dir = os.path.join(get_script_dir(), 'logs')
        ensure_dir(logs_dir)
        for pid_file in ['backend.pid', 'frontend.pid']:
            pid_path = os.path.join(logs_dir, pid_file)
            if os.path.exists(pid_path):
                os.remove(pid_path)
                logger.info(f"已删除PID文件: {pid_file}")
        
    except Exception as e:
        logger.error(f"终止服务时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def start_backend(config):
    """启动后端服务"""
    logger.info("启动后端服务...")
    
    # 切换到后端目录
    backend_dir = os.path.join(get_script_dir(), 'backend')
    os.chdir(backend_dir)
    
    # 准备日志目录和日志文件
    logs_dir = os.path.join(get_script_dir(), 'logs')
    ensure_dir(logs_dir)
    
    # 生成日志文件名，包含时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backend_log = os.path.join(logs_dir, f"backend_{timestamp}.log")
    
    # 替换命令中的占位符
    backend_cmd = config['BACKEND_CMD']
    backend_cmd = backend_cmd.replace('{host}', config['BACKEND_HOST'])
    backend_cmd = backend_cmd.replace('{port}', str(config['BACKEND_PORT']))
    
    logger.info(f"后端启动命令: {backend_cmd}")
    
    # 启动后端进程
    if platform.system() == "Windows":
        backend_process = subprocess.Popen(
            backend_cmd,
            shell=True,
            stdout=open(backend_log, 'w', encoding='utf-8'),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        backend_process = subprocess.Popen(
            backend_cmd,
            shell=True,
            stdout=open(backend_log, 'w', encoding='utf-8'),
            stderr=subprocess.STDOUT
        )
    
    # 保存进程ID (仅用于记录)
    with open(os.path.join(logs_dir, 'backend.pid'), 'w') as f:
        f.write(str(backend_process.pid))
    
    logger.info(f"后端进程ID: {backend_process.pid}")
    
    # 等待后端启动
    logger.info("等待后端启动 (5秒)...")
    time.sleep(5)
    
    return backend_process, backend_log

def start_frontend(config):
    """启动前端服务"""
    logger.info("启动前端服务...")
    
    # 切换到前端目录
    frontend_dir = os.path.join(get_script_dir(), 'frontend')
    os.chdir(frontend_dir)
    
    # 准备日志目录和日志文件
    logs_dir = os.path.join(get_script_dir(), 'logs')
    ensure_dir(logs_dir)
    
    # 生成日志文件名，包含时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    frontend_log = os.path.join(logs_dir, f"frontend_{timestamp}.log")
    
    # 替换命令中的占位符
    frontend_cmd = config['FRONTEND_CMD']
    frontend_cmd = frontend_cmd.replace('{port}', str(config['FRONTEND_PORT']))
    
    logger.info(f"前端启动命令: {frontend_cmd}")
    
    # 启动前端进程
    if platform.system() == "Windows":
        frontend_process = subprocess.Popen(
            frontend_cmd,
            shell=True,
            stdout=open(frontend_log, 'w', encoding='utf-8'),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        frontend_process = subprocess.Popen(
            frontend_cmd,
            shell=True,
            stdout=open(frontend_log, 'w', encoding='utf-8'),
            stderr=subprocess.STDOUT
        )
    
    # 保存进程ID (仅用于记录)
    with open(os.path.join(logs_dir, 'frontend.pid'), 'w') as f:
        f.write(str(frontend_process.pid))
    
    logger.info(f"前端进程ID: {frontend_process.pid}")
    
    return frontend_process, frontend_log

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='项目服务管理脚本')
    parser.add_argument('--stop', action='store_true', help='仅停止服务，不重新启动')
    return parser.parse_args()

def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 检查config.yaml文件是否存在
        config_file = os.path.join(get_script_dir(), 'config.yaml')
        if not os.path.exists(config_file):
            logger.error(f"错误：配置文件 {config_file} 不存在!")
            sys.exit(1)
            
        # 读取配置
        config = read_config()
        
        # 显示项目信息
        print(f"\n{config['PROJECT_NAME']}启动脚本")
        print("=====================")
        
        # 创建日志目录
        logs_dir = os.path.join(get_script_dir(), 'logs')
        ensure_dir(logs_dir)
        
        # 获取端口
        backend_port = int(config['BACKEND_PORT'])
        frontend_port = int(config['FRONTEND_PORT'])
        
        # 如果只是停止服务，使用简化的流程
        if args.stop:
            logger.info("执行停止服务操作...")
            stop_services()  # 停止所有服务
            
            # 检查端口是否已释放
            ports_still_in_use = []
            if is_port_in_use(backend_port):
                ports_still_in_use.append(f"后端({backend_port})")
            if is_port_in_use(frontend_port):
                ports_still_in_use.append(f"前端({frontend_port})")
            
            # 输出结果
            print("\n服务已停止")
            if ports_still_in_use:
                print(f"警告：以下端口仍被占用: {', '.join(ports_still_in_use)}")
                print("这可能需要手动终止相关进程或重启计算机")
            else:
                print("所有端口已成功释放")
            print("=====================")
            return
        
        # 继续启动服务的流程
        logger.info("检查并终止已存在的进程...")
        stop_services()
        
        # 检查后端环境
        check_backend_env()
        
        # 检查前端环境
        check_frontend_env()
        
        # 启动后端服务
        backend_process, backend_log = start_backend(config)
        
        # 启动前端服务
        frontend_process, frontend_log = start_frontend(config)
        
        # 返回到项目根目录
        os.chdir(get_script_dir())
        
        # 显示服务信息
        print("\n服务启动中...")
        print(f"后端地址: http://{config['BACKEND_HOST']}:{config['BACKEND_PORT']}")
        print(f"前端地址: http://{config['FRONTEND_HOST']}:{config['FRONTEND_PORT']}")
        print(f"API文档地址: http://{config['BACKEND_HOST']}:{config['BACKEND_PORT']}/api/docs")
        print(f"后端日志: {backend_log}")
        print(f"前端日志: {frontend_log}")
        print("=====================")
        print("服务已在后台启动。再次运行此脚本可停止并重启服务")
        
    except Exception as e:
        logger.error(f"启动服务时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 
    # python D:\code\projects\project_center\start_all.py --stop