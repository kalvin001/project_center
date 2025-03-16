#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import asyncio

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from app.db.session import engine
from app.models.machine import Machine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

async def check_machine_password():
    """检查机器密码并更新"""
    async with AsyncSession(engine) as session:
        # 查询机器信息
        result = await session.execute(select(Machine).filter(Machine.id == 1))
        machine = result.scalars().first()
        
        if not machine:
            print("未找到ID为1的机器")
            return
        
        print(f"机器ID: {machine.id}")
        print(f"机器名称: {machine.name}")
        print(f"主机地址: {machine.host}")
        print(f"SSH端口: {machine.port}")
        print(f"用户名: {machine.username}")
        print(f"密码: {machine.password}")
        print(f"密钥文件: {machine.key_file}")
        
        # 如果密码为空或者不正确，更新密码
        if not machine.password:
            new_password = "your_secure_password"  # 替换为实际密码
            print(f"密码为空，更新为: {new_password}")
            
            # 更新密码
            await session.execute(
                update(Machine)
                .where(Machine.id == 1)
                .values(password=new_password)
            )
            await session.commit()
            print("密码已更新")
        else:
            print("密码已存在，是否需要更新? (y/n)")
            choice = input().strip().lower()
            if choice == 'y':
                new_password = input("请输入新密码: ").strip()
                if new_password:
                    # 更新密码
                    await session.execute(
                        update(Machine)
                        .where(Machine.id == 1)
                        .values(password=new_password)
                    )
                    await session.commit()
                    print("密码已更新")

if __name__ == "__main__":
    asyncio.run(check_machine_password()) 