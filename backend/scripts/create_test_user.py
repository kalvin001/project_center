#!/usr/bin/env python
"""
创建测试用户脚本

这个脚本创建一个用于测试的用户账号
"""

import os
import sys
import asyncio
from datetime import datetime

# 导入应用模块
from app.database import async_engine, Base, get_async_session
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def create_test_user():
    """创建测试用户"""
    print("开始创建测试用户...")
    
    # 创建数据库会话
    async with async_engine.begin() as conn:
        # 确保表已创建
        await conn.run_sync(Base.metadata.create_all)
    
    # 用户信息
    username = "testuser"
    password = "testpassword"
    email = "testuser@example.com"
    
    # 创建会话并检查用户是否已存在
    async with AsyncSession(async_engine) as session:
        result = await session.execute(select(User).where(User.username == username))
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"测试用户 '{username}' 已存在，无需创建")
            return
        
        # 创建新用户
        test_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_admin=True
        )
        
        session.add(test_user)
        await session.commit()
        
        print(f"成功创建测试用户 '{username}'")
        print(f"用户名: {username}")
        print(f"密码: {password}")
        print(f"电子邮件: {email}")

if __name__ == "__main__":
    asyncio.run(create_test_user()) 