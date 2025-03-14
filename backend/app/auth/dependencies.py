from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="账户已禁用")
    return current_user 