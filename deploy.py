import os
import sys
import argparse
import json
import time
import paramiko
import logging
from pathlib import Path
from getpass import getpass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("deploy.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("项目部署")

# 机器信息文件
MACHINES_FILE = "machines.json"

def save_machines(machines):
    """保存机器信息到文件"""
    with open(MACHINES_FILE, 'w', encoding='utf-8') as f:
        json.dump(machines, f, ensure_ascii=False, indent=2)
    logger.info(f"已更新机器信息文件: {MACHINES_FILE}")

def load_machines():
    """从文件加载机器信息"""
    if not os.path.exists(MACHINES_FILE):
        return {}
    
    try:
        with open(MACHINES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载机器信息失败: {e}")
        return {}

def add_machine(name, host, port, username, password=None, key_file=None):
    """添加新机器到配置中"""
    machines = load_machines()
    
    # 检查是否已存在
    if name in machines:
        logger.warning(f"机器 '{name}' 已存在，将被更新")
    
    # 保存机器信息（不保存密码，仅在首次连接时使用）
    machines[name] = {
        "host": host,
        "port": port,
        "username": username,
        "key_file": key_file
    }
    
    save_machines(machines)
    logger.info(f"已添加机器: {name} ({host}:{port})")
    return True

def remove_machine(name):
    """从配置中删除机器"""
    machines = load_machines()
    
    if name not in machines:
        logger.error(f"机器 '{name}' 不存在")
        return False
    
    del machines[name]
    save_machines(machines)
    logger.info(f"已删除机器: {name}")
    return True

def list_machines():
    """列出所有配置的机器"""
    machines = load_machines()
    
    if not machines:
        logger.info("没有配置任何机器")
        return
    
    logger.info(f"已配置的机器 ({len(machines)}):")
    for name, info in machines.items():
        logger.info(f"  - {name}: {info['username']}@{info['host']}:{info['port']}")

def get_ssh_client(machine_info, password=None):
    print("get_ssh_client---",machine_info,password)
    """创建SSH客户端连接"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 使用SSH密钥或密码连接
    connect_kwargs = {
        "hostname": machine_info["host"],
        "port": machine_info["port"],
        "username": machine_info["username"],
    }
    
    if password:
        connect_kwargs["password"] = password
    elif machine_info.get("key_file"):
        connect_kwargs["key_filename"] = machine_info["key_file"]
    else:
        # 如果没有提供密码且没有密钥文件，尝试使用默认密钥
        pass
    
    try:
        client.connect(**connect_kwargs)
        return client
    except Exception as e:
        logger.error(f"SSH连接失败: {e}")
        return None

def execute_command(client, command, log_output=True):
    """在远程执行命令并获取输出"""
    logger.info(f"执行命令: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    
    # 获取命令输出
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    
    if log_output:
        if out:
            logger.info(f"输出:\n{out}")
        if err:
            logger.error(f"错误:\n{err}")
    
    return out, err

def deploy_project(machine_name, password=None, show_logs=False):
    """部署项目到指定机器"""
    machines = load_machines()
    
    if machine_name not in machines:
        logger.error(f"机器 '{machine_name}' 不存在")
        return False
    
    machine_info = machines[machine_name]
    
    # 连接SSH
    if password is None and not machine_info.get("key_file"):
        password = getpass(f"请输入 {machine_info['username']}@{machine_info['host']} 的密码: ")
    
    client = get_ssh_client(machine_info, password)
    if not client:
        return False
    
    try:
        # 创建项目目录
        logger.info("创建项目目录...")
        execute_command(client, "mkdir -p ~/project_center")
        
        # 确认git是否安装
        logger.info("检查git是否已安装...")
        out, err = execute_command(client, "which git")
        if not out:
            logger.info("安装git...")
            execute_command(client, "sudo apt-get update && sudo apt-get install -y git")
        
        # 使用SFTP上传项目文件
        logger.info("上传项目文件...")
        sftp = client.open_sftp()
        
        # 创建远程目录结构
        for dir_path in ["frontend", "backend", "logs"]:
            try:
                sftp.mkdir(f"~/project_center/{dir_path}")
            except IOError:
                # 目录可能已存在
                pass
        
        # 上传启动脚本
        local_files = [
            "start_all.sh", 
            "stop_all.sh",
            "README.md"
        ]
        
        for file in local_files:
            if os.path.exists(file):
                remote_path = f"~/project_center/{file}"
                sftp.put(file, remote_path)
                execute_command(client, f"chmod +x ~/project_center/{file}")
                logger.info(f"上传 {file} 成功")
        
        # 使用git克隆或更新仓库
        logger.info("检查远程仓库状态...")
        # 检查是否已经有git仓库
        _, err = execute_command(client, "cd ~/project_center && git status")
        if "not a git repository" in err:
            logger.info("初始化git仓库...")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            repo_url = input("请输入git仓库URL (如果留空则使用本地上传): ")
            
            if repo_url:
                execute_command(client, f"cd ~/project_center && git clone {repo_url} .")
            else:
                # 上传backend和frontend目录的内容
                logger.info("上传backend目录...")
                for root, dirs, files in os.walk("backend"):
                    for file in files:
                        local_path = os.path.join(root, file)
                        remote_path = f"~/project_center/{local_path}"
                        remote_dir = os.path.dirname(remote_path)
                        execute_command(client, f"mkdir -p {remote_dir}", log_output=False)
                        sftp.put(local_path, remote_path)
                
                logger.info("上传frontend目录...")
                for root, dirs, files in os.walk("frontend"):
                    for file in files:
                        if "node_modules" in root:
                            continue
                        local_path = os.path.join(root, file)
                        remote_path = f"~/project_center/{local_path}"
                        remote_dir = os.path.dirname(remote_path)
                        execute_command(client, f"mkdir -p {remote_dir}", log_output=False)
                        sftp.put(local_path, remote_path)
        else:
            logger.info("更新远程仓库...")
            execute_command(client, "cd ~/project_center && git pull")
        
        # 启动项目
        logger.info("启动项目...")
        execute_command(client, "cd ~/project_center && ./start_all.sh")
        
        # 显示日志（可选）
        if show_logs:
            logger.info("显示最新日志...")
            execute_command(client, "cd ~/project_center/logs && tail -f *.log")
        
        logger.info(f"项目已成功部署到 {machine_name}")
        return True
    
    except Exception as e:
        logger.error(f"部署失败: {e}")
        return False
    
    finally:
        client.close()

def monitor_logs(machine_name, log_type="backend", password=None):
    """监控指定机器上的日志"""
    machines = load_machines()
    
    if machine_name not in machines:
        logger.error(f"机器 '{machine_name}' 不存在")
        return False
    
    machine_info = machines[machine_name]
    
    # 连接SSH
    if password is None and not machine_info.get("key_file"):
        password = getpass(f"请输入 {machine_info['username']}@{machine_info['host']} 的密码: ")
    
    client = get_ssh_client(machine_info, password)
    if not client:
        return False
    
    try:
        # 确定日志文件模式
        if log_type == "backend":
            log_pattern = "backend_*.log"
        elif log_type == "frontend":
            log_pattern = "frontend_*.log"
        else:
            log_pattern = "*.log"
        
        logger.info(f"监控 {machine_name} 上的 {log_type} 日志...")
        
        # 使用tail命令监控日志
        command = f"cd ~/project_center/logs && ls -t {log_pattern} | head -1 | xargs tail -f"
        stdin, stdout, stderr = client.exec_command(command)
        
        # 实时输出日志
        try:
            while True:
                line = stdout.readline()
                if not line:
                    break
                print(line.strip())
        except KeyboardInterrupt:
            logger.info("停止监控日志")
        
        return True
    
    except Exception as e:
        logger.error(f"监控日志失败: {e}")
        return False
    
    finally:
        client.close()

def check_status(machine_name, password=None):
    """检查指定机器上的项目状态"""
    machines = load_machines()
    
    if machine_name not in machines:
        logger.error(f"机器 '{machine_name}' 不存在")
        return False
    
    machine_info = machines[machine_name]
    
    # 连接SSH
    if password is None and not machine_info.get("key_file"):
        password = getpass(f"请输入 {machine_info['username']}@{machine_info['host']} 的密码: ")
    
    client = get_ssh_client(machine_info, password)
    if not client:
        return False
    
    try:
        # 检查前端和后端进程
        logger.info(f"检查 {machine_name} 上的项目状态...")
        
        # 检查后端进程
        out, _ = execute_command(client, "ps aux | grep 'uvicorn app.main:app' | grep -v grep")
        backend_running = bool(out.strip())
        
        # 检查前端进程
        out, _ = execute_command(client, "ps aux | grep 'pnpm dev' | grep -v grep")
        frontend_running = bool(out.strip())
        
        logger.info(f"后端状态: {'运行中' if backend_running else '已停止'}")
        logger.info(f"前端状态: {'运行中' if frontend_running else '已停止'}")
        
        # 检查磁盘使用情况
        logger.info("磁盘使用情况:")
        execute_command(client, "df -h | grep -E '^/dev/'")
        
        # 检查内存使用情况
        logger.info("内存使用情况:")
        execute_command(client, "free -h")
        
        # 检查CPU负载
        logger.info("CPU负载:")
        execute_command(client, "uptime")
        
        return True
    
    except Exception as e:
        logger.error(f"检查状态失败: {e}")
        return False
    
    finally:
        client.close()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="项目部署和管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 添加机器
    add_parser = subparsers.add_parser("add", help="添加机器配置")
    add_parser.add_argument("name", help="机器名称")
    add_parser.add_argument("host", help="主机地址")
    add_parser.add_argument("--port", type=int, default=22, help="SSH端口 (默认: 22)")
    add_parser.add_argument("--username", default="root", help="SSH用户名 (默认: root)")
    add_parser.add_argument("--key-file", help="SSH密钥文件路径")
    
    # 删除机器
    remove_parser = subparsers.add_parser("remove", help="删除机器配置")
    remove_parser.add_argument("name", help="机器名称")
    
    # 列出机器
    subparsers.add_parser("list", help="列出所有配置的机器")
    
    # 部署项目
    deploy_parser = subparsers.add_parser("deploy", help="部署项目到指定机器")
    deploy_parser.add_argument("name", help="目标机器名称")
    deploy_parser.add_argument("--logs", action="store_true", help="部署后显示日志")
    
    # 监控日志
    logs_parser = subparsers.add_parser("logs", help="监控远程日志")
    logs_parser.add_argument("name", help="目标机器名称")
    logs_parser.add_argument("--type", choices=["backend", "frontend", "all"], default="all", 
                             help="日志类型 (默认: all)")
    
    # 检查状态
    status_parser = subparsers.add_parser("status", help="检查项目状态")
    status_parser.add_argument("name", help="目标机器名称")
    
    # 启动项目
    start_parser = subparsers.add_parser("start", help="启动远程项目")
    start_parser.add_argument("name", help="目标机器名称")
    
    # 停止项目
    stop_parser = subparsers.add_parser("stop", help="停止远程项目")
    stop_parser.add_argument("name", help="目标机器名称")
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 根据命令执行相应操作
    if args.command == "add":
        add_machine(args.name, args.host, args.port, args.username, key_file=args.key_file)
    
    elif args.command == "remove":
        remove_machine(args.name)
    
    elif args.command == "list":
        list_machines()
    
    elif args.command == "deploy":
        deploy_project(args.name, show_logs=args.logs)
    
    elif args.command == "logs":
        monitor_logs(args.name, args.type)
    
    elif args.command == "status":
        check_status(args.name)
    
    elif args.command == "start":
        machines = load_machines()
        if args.name not in machines:
            logger.error(f"机器 '{args.name}' 不存在")
            return
        
        client = get_ssh_client(machines[args.name])
        if client:
            logger.info(f"启动 {args.name} 上的项目...")
            execute_command(client, "cd ~/project_center && ./start_all.sh")
            client.close()
    
    elif args.command == "stop":
        machines = load_machines()
        if args.name not in machines:
            logger.error(f"机器 '{args.name}' 不存在")
            return
        
        client = get_ssh_client(machines[args.name])
        if client:
            logger.info(f"停止 {args.name} 上的项目...")
            execute_command(client, "cd ~/project_center && ./stop_all.sh")
            client.close()
    
    else:
        logger.error("未指定有效命令，请使用 -h 查看帮助")

if __name__ == "__main__":
    #main() 
    machine_info = {
        "host": "47.237.6.218",
        "port": 22,
        "username": "root", 
    }

    ret = get_ssh_client(machine_info,"kalvin@tb1")
    print(ret)