"""
Конфигурация pytest - исправленная версия для pytest 9.0+
"""
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import asyncio
import logging
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.session import Base

# Настраиваем тестовую базу данных
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Создаем движок для тестов
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# Создаем фабрику сессий
TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Настраиваем логирование тестов
logging.basicConfig(
    level=logging.INFO,  # Изменено с DEBUG на INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pytest.log'),
        logging.StreamHandler()
    ]
)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создаем event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Настройка тестовой базы данных - синхронная версия"""
    async def _create_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _drop_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    # Создаем таблицы
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_create_tables())

    yield

    # Удаляем таблицы после тестов
    loop.run_until_complete(_drop_tables())


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для тестовой сессии базы данных"""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def override_get_db(db_session: AsyncSession):
    """Переопределяем зависимость get_db"""
    async def _override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()
    return _override_get_db


@pytest.fixture
async def async_client():
    """Фикстура для асинхронного тестового клиента"""
    try:
        # Для httpx>=0.24+ используем ASGITransport
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
        ) as client:
            yield client
    except ImportError:
        # Для старых версий httpx
        from httpx import AsyncClient
        from app.main import app

        # Альтернативный способ для старых версий
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client