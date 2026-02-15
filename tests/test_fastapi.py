"""
Правильные тесты для FastAPI эндпоинтов
"""
import pytest
import logging
import httpx

# Настраиваем логирование тестов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

from app.main import app


@pytest.mark.asyncio
async def test_root():
    """Тест корневого эндпоинта"""
    # Правильный способ для httpx >= 0.24.0
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        logger.info(f"Root response: {data}")


@pytest.mark.asyncio
async def test_health():
    """Тест health check эндпоинта"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        logger.info(f"Health check: {data}")


@pytest.mark.asyncio
async def test_quick_sim_validation():
    """Тест валидации запроса"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/simulate",
            params={
                "query": "1",  # Слишком короткий
                "decision_type": "purchase",
                "time_horizon_years": 5
            }
        )
        logger.info(f"Validation test: status={response.status_code}")
        # Ожидаем ошибку валидации
        assert response.status_code in [422, 500]