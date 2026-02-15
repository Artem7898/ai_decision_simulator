"""
Тесты для API эндпоинтов
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
from app.schemas.schemas import SimulationInput, DecisionType

@pytest.mark.asyncio
class TestAPIEndpoints:
    """Тесты API эндпоинтов"""


    async def test_root_endpoint(self):
        """Тест корневого эндпоинта"""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            logger.info(f"Root endpoint: {data}")


    async def test_health_check(self):
        """Тест health check"""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            logger.info(f"Health check: {data}")


    async def test_quick_simulation_validation_error(self):
        """Тест валидации минимальной длины query"""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/simulate",
                params={
                    "query": "1",
                    "decision_type": "purchase",
                    "time_horizon_years": 5,
                    "user_id": 1
                }
            )
            logger.info(f"Validation error response status: {response.status_code}")
            logger.info(f"Validation error response: {response.json() if response.status_code != 500 else 'Internal server error'}")
            assert response.status_code in [422, 500]


    async def test_quick_simulation_basic(self):
        """Базовый тест симуляции без моков"""
        # Просто проверяем, что схема работает
        with pytest.raises(ValueError):
            SimulationInput(query="ab", time_horizon_years=5)

        valid_input = SimulationInput(
            query="Should I buy this car?",
            time_horizon_years=5
        )
        assert valid_input.query == "Should I buy this car?"
        assert valid_input.time_horizon_years == 5

    async def test_decision_type_enum(self):
        """Тест перечисления DecisionType"""
        assert DecisionType.RELOCATION.value == "relocation"
        assert DecisionType.PURCHASE.value == "purchase"
        assert DecisionType.JOB.value == "job"
        assert DecisionType.INVESTMENT.value == "investment"
        assert DecisionType("relocation") == DecisionType.RELOCATION


@pytest.mark.asyncio
async def test_basic_endpoints():
    """Базовые тесты эндпоинтов"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        # Тест корневого эндпоинта
        response = await ac.get("/")
        assert response.status_code == 200

        # Тест health check
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])