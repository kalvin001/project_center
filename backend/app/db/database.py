from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///"),
    echo=settings.DEBUG,
    future=True,
)

# 创建会话工厂
async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False, autocommit=False
)

# 创建基础模型类
Base = declarative_base()


# 获取数据库会话的异步上下文管理器
async def get_db() -> AsyncSession:
    """异步数据库会话依赖"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 初始化数据库
async def init_db():
    """创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 