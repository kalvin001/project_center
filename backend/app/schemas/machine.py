from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator

# 创建和更新机器的基础模型
class MachineBase(BaseModel):
    name: str = Field(..., description="机器名称", example="prod-server-1")
    host: str = Field(..., description="主机地址", example="192.168.1.100")
    port: int = Field(22, description="SSH端口", example=22)
    username: str = Field(..., description="SSH用户名", example="root")
    description: Optional[str] = Field(None, description="描述信息")

# 创建机器时的请求模型
class MachineCreate(MachineBase):
    password: str = Field(..., description="SSH密码")
    key_file: Optional[str] = Field(None, description="SSH密钥文件路径")
    
    @validator("name")
    def name_must_be_valid(cls, v):
        if not v or len(v) < 2:
            raise ValueError("机器名称不能少于2个字符")
        return v

# 更新机器时的请求模型
class MachineUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    key_file: Optional[str] = None
    description: Optional[str] = None

# 机器状态信息
class MachineStatus(BaseModel):
    is_online: bool = Field(False, description="是否在线")
    backend_running: bool = Field(False, description="后端是否运行")
    frontend_running: bool = Field(False, description="前端是否运行")
    cpu_usage: Optional[str] = Field(None, description="CPU使用情况")
    memory_usage: Optional[str] = Field(None, description="内存使用情况")
    disk_usage: Optional[str] = Field(None, description="磁盘使用情况")
    last_check: Optional[datetime] = Field(None, description="最后检查时间")

# 机器详情响应模型
class MachineInDB(MachineBase):
    id: int
    is_online: bool = False
    backend_running: bool = False
    frontend_running: bool = False
    cpu_usage: Optional[str] = None
    memory_usage: Optional[str] = None
    disk_usage: Optional[str] = None
    key_file: Optional[str] = None
    last_check: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# 机器列表响应模型
class Machine(MachineInDB):
    pass

# 日志响应模型
class MachineLog(BaseModel):
    id: int
    machine_id: int
    log_type: str
    content: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

# 部署请求模型
class DeployRequest(BaseModel):
    show_logs: bool = False

# 日志请求模型
class LogRequest(BaseModel):
    log_type: str = "backend"  # backend, frontend, all

# 操作响应模型
class OperationResponse(BaseModel):
    success: bool
    message: str 

# 机器监控指标模型
class MachineMetrics(BaseModel):
    timestamp: datetime = Field(..., description="监控数据时间戳")
    cpu: Dict = Field(..., description="CPU指标", example={
        "cores": 4,
        "usage_percent": 25.5,
        "load_avg": [1.2, 1.0, 0.8]
    })
    memory: Dict = Field(..., description="内存指标", example={
        "total": 8589934592,
        "used": 4294967296,
        "free": 4294967296,
        "usage_percent": 50.0
    })
    disk: Dict = Field(..., description="磁盘指标", example={
        "total": 107374182400,
        "used": 42949672960,
        "free": 64424509440,
        "usage_percent": 40.0
    })
    network: Dict = Field(..., description="网络指标", example={
        "rx_bytes": 1024000,
        "tx_bytes": 512000,
        "rx_packets": 1000,
        "tx_packets": 800
    })
    processes: Dict = Field(..., description="进程指标", example={
        "total": 120,
        "running": 5,
        "sleeping": 115
    }) 