from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.database import Base

settings = get_settings()

# Convert sync URL to async
#DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

#engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)

# Для SQLite
if settings.DEBUG:
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
else:
    DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG, connect_args={"check_same_thread": False})

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
