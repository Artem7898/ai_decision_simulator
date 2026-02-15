from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pydantic import ConfigDict

class Settings(BaseSettings):


    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    # App
    APP_NAME: str = "AI Decision Simulator"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    # DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/decision_simulator"
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"  # <-- Добавьте :str

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # LLM
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"

    # External APIs
    NUMBEO_API_KEY: Optional[str] = None  # Cost of living data

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Cache
    CACHE_TTL_SECONDS: int = 86400  # 24 hours



@lru_cache()
def get_settings() -> Settings:
    return Settings()