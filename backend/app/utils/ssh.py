import os
import paramiko
import logging
from typing import Optional, Tuple, List, Dict, Any
import socket
import time
import asyncio

logger = logging.getLogger(__name__)

class SSHClient:
    """SSH客户端封装，用于执行远程命令和文件传输"""
    
    def __init__(
        self, 
        host: str, 
        port: int = 22, 
        username: str = 'root', 
        password: Optional[str] = None, 
        key_file: Optional[str] = None,
        timeout: int = 10
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.timeout = timeout
        self._client = None
        
    async def connect(self) -> bool:
        """建立SSH连接"""
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.host,
                'port': self.port,
                'username': self.username,
                'timeout': self.timeout
            }
            
            if self.password:
                connect_kwargs['password'] = self.password
            
            if self.key_file and os.path.exists(self.key_file):
                connect_kwargs['key_filename'] = self.key_file
            
            # 在事件循环中执行阻塞操作
            await asyncio.to_thread(self._client.connect, **connect_kwargs)
            logger.info(f"成功连接到SSH服务器 {self.host}:{self.port}")
            return True
        except (paramiko.SSHException, socket.error) as e:
            logger.error(f"SSH连接失败: {str(e)}")
            return False
            
    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """执行远程命令并返回状态码、标准输出和标准错误"""
        if not self._client:
            raise Exception("SSH client未连接")
        
        try:
            logger.debug(f"执行命令: {command}")
            
            # 在事件循环中执行阻塞操作
            stdin, stdout, stderr = await asyncio.to_thread(self._client.exec_command, command)
            
            # 获取命令输出
            stdout_data = await asyncio.to_thread(stdout.read)
            stderr_data = await asyncio.to_thread(stderr.read)
            exit_status = await asyncio.to_thread(stdout.channel.recv_exit_status)
            
            stdout_str = stdout_data.decode('utf-8')
            stderr_str = stderr_data.decode('utf-8')
            
            logger.debug(f"命令退出状态: {exit_status}")
            if stdout_str:
                logger.debug(f"标准输出: {stdout_str}")
            if stderr_str:
                logger.debug(f"标准错误: {stderr_str}")
                
            return exit_status, stdout_str, stderr_str
        except Exception as e:
            logger.error(f"执行命令失败: {str(e)}")
            return 1, "", str(e)
    
    async def put_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件到远程服务器"""
        if not self._client:
            raise Exception("SSH client未连接")
        
        try:
            logger.debug(f"上传文件: {local_path} -> {remote_path}")
            
            # 创建SFTP客户端
            sftp = await asyncio.to_thread(self._client.open_sftp)
            
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_path)
            await self.execute_command(f"mkdir -p {remote_dir}")
            
            # 上传文件
            await asyncio.to_thread(sftp.put, local_path, remote_path)
            
            # 关闭SFTP会话
            await asyncio.to_thread(sftp.close)
            
            logger.debug(f"文件上传成功")
            return True
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return False
    
    async def open_sftp(self):
        """获取SFTP客户端会话
        
        返回一个SFTP客户端对象，用于更复杂的文件操作
        调用方负责在使用后关闭SFTP会话
        """
        if not self._client:
            raise Exception("SSH client未连接")
        
        try:
            logger.debug(f"打开SFTP会话")
            # 创建SFTP客户端
            sftp = await asyncio.to_thread(self._client.open_sftp)
            return sftp
        except Exception as e:
            logger.error(f"打开SFTP会话失败: {str(e)}")
            raise
    
    async def get_file(self, remote_path: str, local_path: str) -> bool:
        """从远程服务器下载文件"""
        if not self._client:
            raise Exception("SSH client未连接")
        
        try:
            logger.debug(f"下载文件: {remote_path} -> {local_path}")
            
            # 创建SFTP客户端
            sftp = await asyncio.to_thread(self._client.open_sftp)
            
            # 确保本地目录存在
            local_dir = os.path.dirname(local_path)
            os.makedirs(local_dir, exist_ok=True)
            
            # 下载文件
            await asyncio.to_thread(sftp.get, remote_path, local_path)
            
            # 关闭SFTP会话
            await asyncio.to_thread(sftp.close)
            
            logger.debug(f"文件下载成功")
            return True
        except Exception as e:
            logger.error(f"文件下载失败: {str(e)}")
            return False
    
    async def close(self):
        """关闭SSH连接"""
        if self._client:
            await asyncio.to_thread(self._client.close)
            self._client = None
            logger.debug(f"已关闭SSH连接 {self.host}:{self.port}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close() 