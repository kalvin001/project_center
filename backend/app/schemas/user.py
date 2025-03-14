from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """基本用户信息"""
    username: str
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    """创建用户时需要的数据"""
    password: str


class UserUpdate(BaseModel):
    """更新用户时需要的数据"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserInDB(UserBase):
    """数据库中的用户数据"""
    id: int
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """返回给客户端的用户数据"""
    pass


class Token(BaseModel):
    """令牌"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """令牌中的数据"""
    sub: Optional[int] = None
    # 使用整数类型来表示到期时间戳（秒），符合 JWT 标准
    exp: Optional[int] = None
    
    class Config:
        # 允许使用别名，通常用于 snake_case 到 camelCase 的转换
        # 但在这里我们主要是为了确保 Pydantic 能正确解析日期时间
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        } 