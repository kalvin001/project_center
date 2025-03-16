import asyncio
import sys
import os

# 将当前目录添加到路径，以便能够导入app模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User
from app.core.security import get_password_hash
from app.db.database import init_db, async_session_factory
from sqlalchemy.future import select


async def create_test_user():
    # 初始化数据库
    await init_db()
    
    # 创建测试用户
    async with async_session_factory() as db:
        # 查询是否已存在该用户
        result = await db.execute(
            select(User).where(User.username == "testuser")
        )
        user = result.scalars().first()
        
        if user:
            print(f"测试用户 'testuser' 已存在 (ID: {user.id})")
        else:
            # 创建新用户
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpassword"),
                is_active=True,
                is_admin=True
            )
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            print(f"已创建测试用户 'testuser' (ID: {test_user.id})")
        
        # 列出所有用户
        print("\n所有用户:")
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        for user in users:
            print(f"  - {user.username} (ID: {user.id}, 邮箱: {user.email}, 管理员: {user.is_admin})")


if __name__ == "__main__":
    asyncio.run(create_test_user()) 