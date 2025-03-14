# 添加一个测试用户，确保能够登录
async def add_test_user(db):
    """添加一个测试用户，如果不存在的话"""
    from sqlalchemy.future import select
    from app.models.user import User
    from app.core.security import get_password_hash
    
    # 检查是否已存在用户
    result = await db.execute(select(User).limit(1))
    user = result.scalars().first()
    
    if not user:
        # 创建一个测试用户
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            is_active=True,
            is_admin=True
        )
        db.add(test_user)
        await db.commit()
        print("已创建测试用户: testuser / testpassword") 