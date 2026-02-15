"""
Конфигурация логирования для приложения
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Создаем папку для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging():
    """Настройка логирования для приложения"""

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Файловый обработчик (ротация по 10MB, максимум 5 файлов)
    file_handler = RotatingFileHandler(
        LOG_DIR / 'app.log',
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Обработчик ошибок
    error_handler = RotatingFileHandler(
        LOG_DIR / 'errors.log',
        maxBytes=10_000_000,
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(error_handler)

    # Настраиваем логгеры для наших модулей
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.DEBUG)

    # SQLAlchemy логирование
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.WARNING)

    # FastAPI логирование
    uvicorn_logger = logging.getLogger('uvicorn')
    uvicorn_logger.setLevel(logging.INFO)

    return root_logger


# Создаем функцию для получения логгера
def get_logger(name: str) -> logging.Logger:
    """Получить логгер по имени"""
    return logging.getLogger(name)