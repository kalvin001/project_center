import os
import sys
import json
import paramiko
import logging
import asyncio
import tempfile
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

# 修改导入路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.models.machine import Machine
from app.models.machine_log import MachineLog
from app.schemas.machine import MachineCreate, MachineUpdate, MachineStatus, MachineMetrics

logger = logging.getLogger(__name__)

class MachineManager:
    """机器管理服务"""
    
    @staticmethod
    async def get_machine(db: AsyncSession, machine_id: int) -> Optional[Machine]:
        """获取机器信息"""
        result = await db.execute(select(Machine).filter(Machine.id == machine_id))
        return result.scalars().first()
    
    @staticmethod
    async def get_machine_by_name(db: AsyncSession, name: str) -> Optional[Machine]:
        """通过名称获取机器信息"""
        result = await db.execute(select(Machine).filter(Machine.name == name))
        return result.scalars().first()
    
    @staticmethod
    async def get_machines(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Machine]:
        """获取机器列表"""
        result = await db.execute(select(Machine).offset(skip).limit(limit))
        return result.scalars().all()
    
    @staticmethod
    async def create_machine(db: AsyncSession, machine: MachineCreate) -> Machine:
        """创建新机器"""
        db_machine = Machine(
            name=machine.name,
            host=machine.host,
            port=machine.port,
            username=machine.username,
            password=machine.password,  # 保存密码到数据库
            key_file=machine.key_file,
            description=machine.description
        )
        db.add(db_machine)
        await db.commit()
        await db.refresh(db_machine)
        
        # 记录日志
        log = MachineLog(
            machine_id=db_machine.id,
            log_type="create",
            content=f"添加了新机器: {machine.name} ({machine.host}:{machine.port})",
            status="success"
        )
        db.add(log)
        await db.commit()
        
        return db_machine
    
    @staticmethod
    async def update_machine(
        db: AsyncSession, 
        machine_id: int, 
        machine_data: MachineUpdate
    ) -> Optional[Machine]:
        """更新机器信息"""
        # 获取当前机器信息
        db_machine = await MachineManager.get_machine(db, machine_id)
        if not db_machine:
            return None
        
        # 准备更新数据
        update_data = machine_data.dict(exclude_unset=True)
        
        if update_data:
            # 更新机器信息
            await db.execute(
                update(Machine)
                .where(Machine.id == machine_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(db_machine)
            
            # 记录日志
            log = MachineLog(
                machine_id=db_machine.id,
                log_type="update",
                content=f"更新机器信息: {', '.join(f'{k}={v}' for k, v in update_data.items() if k != 'password')}",
                status="success"
            )
            db.add(log)
            await db.commit()
        
        return db_machine
    
    @staticmethod
    async def delete_machine(db: AsyncSession, machine_id: int) -> bool:
        """删除机器"""
        # 检查机器是否存在
        db_machine = await MachineManager.get_machine(db, machine_id)
        if not db_machine:
            return False
        
        machine_name = db_machine.name
        
        # 删除机器
        await db.execute(delete(Machine).where(Machine.id == machine_id))
        await db.commit()
        
        # 记录日志
        return True
    
    @staticmethod
    async def get_ssh_client(machine: Machine, password: Optional[str] = None) -> Tuple[Optional[paramiko.SSHClient], str]:
        """获取SSH客户端连接"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 详细日志记录
        logger.info(f"尝试连接到 {machine.host}:{machine.port} 用户名: {machine.username}")
        
        # 优先使用传入的密码，如果没有则使用数据库中存储的密码
        actual_password = password if password else machine.password
        
        # 检查密码参数
        has_password = bool(actual_password)
        has_keyfile = bool(machine.key_file)
        logger.info(f"认证方式: {'密码' if has_password else ''}{' 和 ' if has_password and has_keyfile else ''}{('密钥文件:' + machine.key_file) if has_keyfile else ''}")
        logger.info(f"密码状态: {'有密码' if has_password else '无密码'}, 密码长度: {len(str(actual_password)) if actual_password else 0}")
        
        error_msg = ""
        
        # 准备连接参数
        connect_kwargs = {
            "hostname": machine.host,
            "port": machine.port,
            "username": machine.username,
            "timeout": 15,  # 增加超时时间
        }
        
        # 添加认证参数
        if actual_password:
            # 显式转换密码为字符串类型
            connect_kwargs["password"] = str(actual_password)
            logger.info(f"使用密码认证，密码长度: {len(str(actual_password))}")
        elif machine.key_file:
            if os.path.exists(machine.key_file):
                connect_kwargs["key_filename"] = machine.key_file
                logger.info(f"使用密钥文件: {machine.key_file}")
            else:
                error_msg = f"密钥文件不存在: {machine.key_file}"
                logger.error(error_msg)
                return None, error_msg
        else:
            # 如果既没有密码也没有密钥，尝试使用默认密钥
            logger.warning("未提供密码且无密钥文件，尝试使用默认密钥认证")
        
        # 尝试连接
        try:
            logger.info(f"开始SSH连接... 连接参数: {connect_kwargs['hostname']}:{connect_kwargs['port']} 用户名: {connect_kwargs['username']}")
            client.connect(**connect_kwargs)
            logger.info("SSH连接成功")
            return client, ""
        except paramiko.AuthenticationException as e:
            error_msg = f"SSH认证失败: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except paramiko.SSHException as e:
            error_msg = f"SSH连接异常: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"SSH连接失败: {str(e)}"
            logger.error(f"连接出错: {error_msg}")
            return None, error_msg
    
    @staticmethod
    async def execute_command(
        client: paramiko.SSHClient, 
        command: str
    ) -> Tuple[str, str, int]:
        """执行远程命令"""
        stdin, stdout, stderr = client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        
        out = stdout.read().decode('utf-8').strip()
        err = stderr.read().decode('utf-8').strip()
        
        return out, err, exit_code
    
    @staticmethod
    async def check_machine_status(
        db: AsyncSession, 
        machine_id: int
    ) -> Tuple[bool, MachineStatus, str]:
        """检查机器状态"""
        # 获取机器信息
        db_machine = await MachineManager.get_machine(db, machine_id)
        if not db_machine:
            logger.error(f"机器ID {machine_id} 不存在")
            return False, MachineStatus(), "机器不存在"
        
        # 记录详细日志
        logger.info(f"开始检查机器状态: ID={machine_id}, 机器名={db_machine.name}")
        
        # 获取SSH连接
        client, error = await MachineManager.get_ssh_client(db_machine)
        if not client:
            logger.error(f"无法连接到机器 {db_machine.name}: {error}")
            
            # 更新机器状态为离线
            await db.execute(
                update(Machine)
                .where(Machine.id == machine_id)
                .values(
                    is_online=False,
                    last_check=datetime.now()
                )
            )
            await db.commit()
            
            # 确保日志内容使用UTF-8编码
            error_msg = f"状态检查失败: {error}"
            try:
                # 尝试编码然后解码，确保不会有编码问题
                error_msg_bytes = error_msg.encode('utf-8')
                error_msg = error_msg_bytes.decode('utf-8')
            except Exception as e:
                logger.error(f"日志编码处理错误: {str(e)}")
                error_msg = "状态检查失败: SSH连接错误"
            
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="status",
                content=error_msg,
                status="failed"
            )
            db.add(log)
            await db.commit()
            
            return False, MachineStatus(is_online=False), error
        
        try:
            status = MachineStatus(is_online=True)
            
            # 检查后端进程
            out, _, _ = await MachineManager.execute_command(
                client, 
                "ps aux | grep 'uvicorn app.main:app' | grep -v grep"
            )
            status.backend_running = bool(out.strip())
            
            # 检查前端进程
            out, _, _ = await MachineManager.execute_command(
                client, 
                "ps aux | grep 'pnpm dev' | grep -v grep"
            )
            status.frontend_running = bool(out.strip())
            
            # 检查CPU使用情况
            out, _, _ = await MachineManager.execute_command(client, "uptime")
            status.cpu_usage = out.strip()
            
            # 检查内存使用情况
            out, _, _ = await MachineManager.execute_command(client, "free -h | head -2")
            status.memory_usage = out.strip()
            
            # 检查磁盘使用情况
            out, _, _ = await MachineManager.execute_command(
                client, 
                "df -h | grep -E '^/dev/' | head -1"
            )
            status.disk_usage = out.strip()
            
            status.last_check = datetime.now()
            
            # 更新机器状态
            await db.execute(
                update(Machine)
                .where(Machine.id == machine_id)
                .values(
                    is_online=status.is_online,
                    backend_running=status.backend_running,
                    frontend_running=status.frontend_running,
                    cpu_usage=status.cpu_usage,
                    memory_usage=status.memory_usage,
                    disk_usage=status.disk_usage,
                    last_check=status.last_check
                )
            )
            await db.commit()
            
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="status",
                content=f"状态检查成功: 在线={status.is_online}, 后端={status.backend_running}, 前端={status.frontend_running}",
                status="success"
            )
            db.add(log)
            await db.commit()
            
            return True, status, ""
        
        except Exception as e:
            error = f"状态检查出错: {str(e)}"
            
            # 更新机器状态
            await db.execute(
                update(Machine)
                .where(Machine.id == machine_id)
                .values(
                    is_online=True,  # 连接成功但检查出错
                    last_check=datetime.now()
                )
            )
            await db.commit()
            
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="status",
                content=f"状态检查出错: {error}",
                status="failed"
            )
            db.add(log)
            await db.commit()
            
            return False, MachineStatus(is_online=True), error
        
        finally:
            client.close()
    
    @staticmethod
    async def deploy_project(
        db: AsyncSession, 
        machine_id: int
    ) -> Tuple[bool, str]:
        """部署项目到机器"""
        # 获取机器信息
        db_machine = await MachineManager.get_machine(db, machine_id)
        if not db_machine:
            return False, "机器不存在"
        
        # 获取SSH连接
        client, error = await MachineManager.get_ssh_client(db_machine)
        if not client:
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="deploy",
                content=f"部署失败: {error}",
                status="failed"
            )
            db.add(log)
            await db.commit()
            
            return False, error
        
        try:
            # 创建项目目录
            out, err, exit_code = await MachineManager.execute_command(
                client, 
                "mkdir -p ~/project_center ~/project_center/logs"
            )
            if exit_code != 0:
                error = f"创建目录失败: {err}"
                
                # 记录日志
                log = MachineLog(
                    machine_id=machine_id,
                    log_type="deploy",
                    content=f"部署失败: {error}",
                    status="failed"
                )
                db.add(log)
                await db.commit()
                
                return False, error
            
            # 使用SFTP上传启动脚本
            sftp = client.open_sftp()
            
            # 创建临时目录存放脚本文件
            with tempfile.TemporaryDirectory() as temp_dir:
                # 创建Linux启动脚本
                start_script = Path(temp_dir) / "start_all.sh"
                with open(start_script, "w") as f:
                    f.write("""#!/bin/bash
echo "项目管理中心启动脚本"
echo "====================="

# 检查后端环境
echo "检查后端环境..."
cd backend

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "创建后端虚拟环境..."
    python3 -m pip install uv
    uv venv
    
    echo "安装后端依赖..."
    .venv/bin/pip install -e .
    
    echo "安装额外依赖..."
    .venv/bin/python install_deps.py --force
else
    echo "后端环境已存在，检查是否可用..."
    
    # 检查pip是否可用
    if ! .venv/bin/pip --version &> /dev/null; then
        echo "检测到虚拟环境损坏，重新创建..."
        rm -rf .venv
        python3 -m pip install uv
        uv venv
        
        echo "安装后端依赖..."
        .venv/bin/pip install -e .
        
        echo "安装额外依赖..."
        .venv/bin/python install_deps.py --force
    else
        echo "后端环境正常，检查依赖是否变化..."
    
        # 检查依赖是否变化
        if [ ! -f ".deps_checksum.txt" ]; then
            echo "未找到依赖校验文件，检查依赖是否需要更新..."
            cp pyproject.toml .deps_checksum.txt
            .venv/bin/python install_deps.py
        else
            if ! cmp -s pyproject.toml .deps_checksum.txt; then
                echo "检测到pyproject.toml变化，更新依赖..."
                .venv/bin/pip install -e .
                
                echo "更新依赖校验信息..."
                cp pyproject.toml .deps_checksum.txt
                
                echo "检查并安装额外依赖..."
                .venv/bin/python install_deps.py
            else
                echo "pyproject.toml无变化，检查其他依赖..."
                .venv/bin/python install_deps.py
            fi
        fi
    fi
fi

# 检查前端环境
echo "检查前端环境..."
cd ../frontend
# 检查依赖是否变化
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install -g pnpm
    pnpm install
    
    echo "保存前端依赖校验信息..."
    cp package.json .pkg_checksum.txt
else
    echo "前端环境已存在，检查依赖是否变化..."
    
    if [ ! -f ".pkg_checksum.txt" ]; then
        echo "未找到前端依赖校验文件，需要重新安装依赖..."
        pnpm install
        
        echo "保存前端依赖校验信息..."
        cp package.json .pkg_checksum.txt
    else
        if ! cmp -s package.json .pkg_checksum.txt; then
            echo "检测到前端依赖变化，需要更新..."
            pnpm install
            
            echo "更新前端依赖校验信息..."
            cp package.json .pkg_checksum.txt
        else
            echo "前端依赖无变化，跳过安装步骤..."
        fi
    fi
fi

# 启动后端和前端（先启动后端）
echo "启动后端服务..."
LOGS_DIR="../logs"
mkdir -p $LOGS_DIR

BACKEND_LOG="$LOGS_DIR/backend_$(date +%Y%m%d_%H%M%S).log"
FRONTEND_LOG="$LOGS_DIR/frontend_$(date +%Y%m%d_%H%M%S).log"

cd ../backend
nohup .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8011 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "后端进程ID: $BACKEND_PID"
echo $BACKEND_PID > "$LOGS_DIR/backend.pid"

# 等待后端启动
echo "等待后端启动 (5秒)..."
sleep 5

# 启动前端
echo "启动前端服务..."
cd ../frontend
nohup pnpm dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo "前端进程ID: $FRONTEND_PID"
echo $FRONTEND_PID > "$LOGS_DIR/frontend.pid"

echo "服务启动中..."
echo "后端地址: http://localhost:8011"
echo "前端地址: http://localhost:8012"
echo "API文档地址: http://localhost:8011/api/docs"
echo "后端日志: $BACKEND_LOG"
echo "前端日志: $FRONTEND_LOG"
echo "====================="
echo "服务已在后台启动。使用 stop_all.sh 停止服务"
""")
                
                # 创建停止脚本
                stop_script = Path(temp_dir) / "stop_all.sh"
                with open(stop_script, "w") as f:
                    f.write("""#!/bin/bash
echo "停止项目管理中心服务"
echo "====================="

LOGS_DIR="logs"

# 停止后端服务
if [ -f "$LOGS_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$LOGS_DIR/backend.pid")
    if ps -p $BACKEND_PID > /dev/null; then
        echo "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo "后端服务已停止"
    else
        echo "后端服务未运行"
    fi
    rm "$LOGS_DIR/backend.pid"
else
    echo "未找到后端服务进程ID文件"
    pkill -f "uvicorn app.main:app"
fi

# 停止前端服务
if [ -f "$LOGS_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOGS_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo "前端服务已停止"
    else
        echo "前端服务未运行"
    fi
    rm "$LOGS_DIR/frontend.pid"
else
    echo "未找到前端服务进程ID文件"
    pkill -f "pnpm dev"
fi

echo "所有服务已停止"
""")
                
                # 上传脚本
                try:
                    sftp.put(str(start_script), "/home/ubuntu/project_center/start_all.sh")
                    sftp.put(str(stop_script), "/home/ubuntu/project_center/stop_all.sh")
                    
                    # 设置执行权限
                    await MachineManager.execute_command(
                        client, 
                        "chmod +x ~/project_center/start_all.sh ~/project_center/stop_all.sh"
                    )
                except Exception as e:
                    error = f"上传脚本失败: {str(e)}"
                    
                    # 记录日志
                    log = MachineLog(
                        machine_id=machine_id,
                        log_type="deploy",
                        content=f"部署失败: {error}",
                        status="failed"
                    )
                    db.add(log)
                    await db.commit()
                    
                    return False, error
            
            # 部署项目代码
            # 这里应该使用git克隆仓库或者上传项目文件
            # 为简化示例，这里假设通过git部署
            
            # 检查git是否安装
            out, err, exit_code = await MachineManager.execute_command(client, "which git")
            if exit_code != 0:
                # 安装git
                out, err, exit_code = await MachineManager.execute_command(
                    client, 
                    "sudo apt-get update && sudo apt-get install -y git"
                )
                if exit_code != 0:
                    error = f"安装git失败: {err}"
                    
                    # 记录日志
                    log = MachineLog(
                        machine_id=machine_id,
                        log_type="deploy",
                        content=f"部署失败: {error}",
                        status="failed"
                    )
                    db.add(log)
                    await db.commit()
                    
                    return False, error
            
            # 部署成功
            log = MachineLog(
                machine_id=machine_id,
                log_type="deploy",
                content="部署成功",
                status="success"
            )
            db.add(log)
            await db.commit()
            
            return True, "部署成功"
        
        except Exception as e:
            error = f"部署失败: {str(e)}"
            
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="deploy",
                content=error,
                status="failed"
            )
            db.add(log)
            await db.commit()
            
            return False, error
        
        finally:
            client.close()
    
    @staticmethod
    async def start_project(
        db: AsyncSession, 
        machine_id: int
    ) -> Tuple[bool, str]:
        """启动远程项目"""
        # 获取机器信息
        db_machine = await MachineManager.get_machine(db, machine_id)
        if not db_machine:
            return False, "机器不存在"
        
        # 获取SSH连接
        client, error = await MachineManager.get_ssh_client(db_machine)
        if not client:
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="start",
                content=f"启动失败: {error}",
                status="failed"
            )
            db.add(log)
            await db.commit()
            
            return False, error
        
        try:
            # 执行启动脚本
            out, err, exit_code = await MachineManager.execute_command(
                client, 
                "cd ~/project_center && ./start_all.sh"
            )
            
            if exit_code != 0:
                error = f"启动失败: {err}"
                
                # 记录日志
                log = MachineLog(
                    machine_id=machine_id,
                    log_type="start",
                    content=error,
                    status="failed"
                )
                db.add(log)
                await db.commit()
                
                return False, error
            
            # 更新机器状态
            await db.execute(
                update(Machine)
                .where(Machine.id == machine_id)
                .values(
                    backend_running=True,
                    frontend_running=True,
                    last_check=datetime.now()
                )
            )
            await db.commit()
            
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="start",
                content="项目启动成功",
                status="success"
            )
            db.add(log)
            await db.commit()
            
            return True, "项目启动成功"
        
        except Exception as e:
            error = f"启动失败: {str(e)}"
            
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="start",
                content=error,
                status="failed"
            )
            db.add(log)
            await db.commit()
            
            return False, error
        
        finally:
            client.close()
    
    @staticmethod
    async def stop_project(
        db: AsyncSession, 
        machine_id: int
    ) -> Tuple[bool, str]:
        """停止远程项目"""
        # 获取机器信息
        db_machine = await MachineManager.get_machine(db, machine_id)
        if not db_machine:
            return False, "机器不存在"
        
        # 获取SSH连接
        client, error = await MachineManager.get_ssh_client(db_machine)
        if not client:
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="stop",
                content=f"停止失败: {error}",
                status="failed"
            )
            db.add(log)
            await db.commit()
            
            return False, error
        
        try:
            # 执行停止脚本
            out, err, exit_code = await MachineManager.execute_command(
                client, 
                "cd ~/project_center && ./stop_all.sh"
            )
            
            # 更新机器状态
            await db.execute(
                update(Machine)
                .where(Machine.id == machine_id)
                .values(
                    backend_running=False,
                    frontend_running=False,
                    last_check=datetime.now()
                )
            )
            await db.commit()
            
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="stop",
                content="项目停止成功",
                status="success"
            )
            db.add(log)
            await db.commit()
            
            return True, "项目停止成功"
        
        except Exception as e:
            error = f"停止失败: {str(e)}"
            
            # 记录日志
            log = MachineLog(
                machine_id=machine_id,
                log_type="stop",
                content=error,
                status="failed"
            )
            db.add(log)
            await db.commit()
            
            return False, error
        
        finally:
            client.close()
    
    @staticmethod
    async def get_logs(
        db: AsyncSession, 
        machine_id: int, 
        log_type: str = "backend", 
        lines: int = 100
    ) -> Tuple[bool, str, str]:
        """获取远程日志"""
        # 获取机器信息
        db_machine = await MachineManager.get_machine(db, machine_id)
        if not db_machine:
            return False, "", "机器不存在"
        
        # 获取SSH连接
        client, error = await MachineManager.get_ssh_client(db_machine)
        if not client:
            return False, "", error
        
        try:
            # 确定日志文件模式
            if log_type == "backend":
                log_pattern = "backend_*.log"
            elif log_type == "frontend":
                log_pattern = "frontend_*.log"
            else:
                log_pattern = "*.log"
            
            # 获取最新的日志文件
            out, err, exit_code = await MachineManager.execute_command(
                client, 
                f"cd ~/project_center/logs && ls -t {log_pattern} | head -1"
            )
            
            if not out or exit_code != 0:
                return False, "", f"未找到日志文件: {err}"
            
            log_file = out.strip()
            
            # 读取日志内容
            out, err, exit_code = await MachineManager.execute_command(
                client, 
                f"cd ~/project_center/logs && tail -n {lines} {log_file}"
            )
            
            if exit_code != 0:
                return False, "", f"读取日志失败: {err}"
            
            return True, out, ""
        
        except Exception as e:
            return False, "", f"获取日志失败: {str(e)}"
        
        finally:
            client.close()
    
    @staticmethod
    async def get_machine_metrics(
        db: AsyncSession, 
        machine_id: int
    ) -> Tuple[bool, MachineMetrics, str]:
        """获取机器监控指标"""
        # 获取机器信息
        machine = await MachineManager.get_machine(db, machine_id)
        if not machine:
            return False, None, "机器不存在"
        
        try:
            # 记录详细日志
            logger.info(f"开始获取机器监控指标: ID={machine_id}, 机器名={machine.name}, 主机={machine.host}")
            logger.info(f"机器密码状态: {'有密码' if machine.password else '无密码'}, 密码长度: {len(str(machine.password)) if machine.password else 0}")
            
            # 获取SSH客户端
            ssh_client, error = await MachineManager.get_ssh_client(machine)
            if not ssh_client:
                logger.error(f"连接到机器失败: {error}")
                return False, None, f"连接到机器失败: {error}"
            
            try:
                # 执行命令获取CPU信息
                logger.debug("获取CPU信息...")
                cpu_cmd = "cat /proc/cpuinfo | grep processor | wc -l && cat /proc/loadavg && top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'"
                cpu_output, cpu_error, cpu_code = await MachineManager.execute_command(ssh_client, cpu_cmd)
                
                if cpu_code != 0:
                    logger.error(f"获取CPU信息失败: {cpu_error}")
                    return False, None, f"获取CPU信息失败: {cpu_error}"
                
                logger.debug(f"CPU命令输出: {cpu_output}")
                cpu_lines = cpu_output.strip().split('\n')
                if len(cpu_lines) < 3:
                    logger.error(f"CPU信息格式不正确: {cpu_output}")
                    return False, None, f"CPU信息格式不正确: {cpu_output}"
                    
                cpu_cores = int(cpu_lines[0])
                load_avg = [float(x) for x in cpu_lines[1].split()[:3]]
                cpu_usage = float(cpu_lines[2])
                
                # 获取内存信息
                logger.debug("获取内存信息...")
                mem_cmd = "free -b | grep Mem"
                mem_output, mem_error, mem_code = await MachineManager.execute_command(ssh_client, mem_cmd)
                
                if mem_code != 0:
                    logger.error(f"获取内存信息失败: {mem_error}")
                    return False, None, f"获取内存信息失败: {mem_error}"
                
                logger.debug(f"内存命令输出: {mem_output}")
                mem_info = mem_output.strip().split()
                if len(mem_info) < 4:
                    logger.error(f"内存信息格式不正确: {mem_output}")
                    return False, None, f"内存信息格式不正确: {mem_output}"
                    
                mem_total = int(mem_info[1])
                mem_used = int(mem_info[2])
                mem_free = int(mem_info[3])
                mem_usage_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0
                
                # 获取磁盘信息
                logger.debug("获取磁盘信息...")
                disk_cmd = "df -B1 / | tail -1"
                disk_output, disk_error, disk_code = await MachineManager.execute_command(ssh_client, disk_cmd)
                
                if disk_code != 0:
                    logger.error(f"获取磁盘信息失败: {disk_error}")
                    return False, None, f"获取磁盘信息失败: {disk_error}"
                
                logger.debug(f"磁盘命令输出: {disk_output}")
                disk_info = disk_output.strip().split()
                if len(disk_info) < 4:
                    logger.error(f"磁盘信息格式不正确: {disk_output}")
                    return False, None, f"磁盘信息格式不正确: {disk_output}"
                    
                disk_total = int(disk_info[1])
                disk_used = int(disk_info[2])
                disk_free = int(disk_info[3])
                disk_usage_percent = (disk_used / disk_total) * 100 if disk_total > 0 else 0
                
                # 获取网络信息
                logger.debug("获取网络信息...")
                net_cmd = "cat /proc/net/dev | grep -E 'eth0|ens|enp' | awk '{print $2,$10,$3,$11}'"
                net_output, net_error, net_code = await MachineManager.execute_command(ssh_client, net_cmd)
                
                if net_code != 0:
                    logger.error(f"获取网络信息失败: {net_error}")
                    # 网络信息获取失败不影响整体结果，使用默认值
                    rx_bytes = tx_bytes = rx_packets = tx_packets = 0
                else:
                    logger.debug(f"网络命令输出: {net_output}")
                    net_info = net_output.strip().split()
                    if len(net_info) >= 4:
                        rx_bytes = int(net_info[0])
                        tx_bytes = int(net_info[1])
                        rx_packets = int(net_info[2])
                        tx_packets = int(net_info[3])
                    else:
                        logger.warning(f"网络信息格式不正确: {net_output}，使用默认值")
                        rx_bytes = tx_bytes = rx_packets = tx_packets = 0
                
                # 获取进程信息
                logger.debug("获取进程信息...")
                proc_cmd = "ps -e | wc -l && ps -e | grep -c 'R' || echo 0 && ps -e | grep -c 'S' || echo 0"
                proc_output, proc_error, proc_code = await MachineManager.execute_command(ssh_client, proc_cmd)
                
                if proc_code != 0:
                    logger.error(f"获取进程信息失败: {proc_error}")
                    return False, None, f"获取进程信息失败: {proc_error}"
                
                logger.debug(f"进程命令输出: {proc_output}")
                proc_lines = proc_output.strip().split('\n')
                if len(proc_lines) < 3:
                    logger.error(f"进程信息格式不正确: {proc_output}")
                    # 进程信息获取失败不影响整体结果，使用默认值
                    total_procs = running_procs = sleeping_procs = 0
                else:
                    total_procs = int(proc_lines[0])
                    running_procs = int(proc_lines[1])
                    sleeping_procs = int(proc_lines[2])
                
                # 关闭SSH连接
                ssh_client.close()
                
                # 构建监控指标
                metrics = MachineMetrics(
                    timestamp=datetime.now(),
                    cpu={
                        "cores": cpu_cores,
                        "usage_percent": cpu_usage,
                        "load_avg": load_avg
                    },
                    memory={
                        "total": mem_total,
                        "used": mem_used,
                        "free": mem_free,
                        "usage_percent": mem_usage_percent
                    },
                    disk={
                        "total": disk_total,
                        "used": disk_used,
                        "free": disk_free,
                        "usage_percent": disk_usage_percent
                    },
                    network={
                        "rx_bytes": rx_bytes,
                        "tx_bytes": tx_bytes,
                        "rx_packets": rx_packets,
                        "tx_packets": tx_packets
                    },
                    processes={
                        "total": total_procs,
                        "running": running_procs,
                        "sleeping": sleeping_procs
                    }
                )
                
                return True, metrics, ""
                
            except Exception as e:
                import traceback
                error_msg = f"获取机器监控指标失败: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return False, None, error_msg
            
            finally:
                if ssh_client:
                    ssh_client.close()
        
        except Exception as e:
            import traceback
            logger.error(f"获取机器监控指标失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False, None, f"获取机器监控指标失败: {str(e)}" 
        

if __name__ == "__main__":
    import asyncio
    import sys
    import os
    
    # 添加项目根目录到Python路径
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    
    from app.db.database import async_session_factory
    
    async def test_get_machine_metrics():
        """测试获取机器监控指标"""
        print("开始测试获取机器监控指标...")
        
        try:
            # 创建数据库会话
            async with async_session_factory() as db:
                # 假设数据库中有ID为1的机器
                machine_id = 1
                
                # 先获取机器信息，确认机器存在
                machine = await MachineManager.get_machine(db, machine_id)
                if not machine:
                    print(f"错误: 数据库中不存在ID为{machine_id}的机器")
                    return
                
                print(f"找到机器: {machine.name} ({machine.host}:{machine.port})")
                print(f"用户名: {machine.username}")
                print(f"密码状态: {'有密码' if machine.password else '无密码'}")
                print(f"密钥文件: {machine.key_file if machine.key_file else '无'}")
                
                # 测试SSH连接
                print("测试SSH连接...")
                client, error = await MachineManager.get_ssh_client(machine)
                if not client:
                    print(f"SSH连接失败: {error}")
                    return
                
                print("SSH连接成功，关闭连接...")
                client.close()
                
                # 获取监控指标
                print("获取监控指标...")
                success, metrics, error = await MachineManager.get_machine_metrics(db, machine_id)
                
                if success:
                    print(f"成功获取机器监控指标:")
                    print(f"CPU: {metrics.cpu}")
                    print(f"内存: {metrics.memory}")
                    print(f"磁盘: {metrics.disk}")
                    print(f"网络: {metrics.network}")
                    print(f"进程: {metrics.processes}")
                else:
                    print(f"获取机器监控指标失败: {error}")
        except Exception as e:
            import traceback
            print(f"测试过程中发生错误: {str(e)}")
            print(traceback.format_exc())
    
    # 设置日志级别为DEBUG
    logging.basicConfig(level=logging.DEBUG)
    
    # 运行测试函数
    asyncio.run(test_get_machine_metrics())

