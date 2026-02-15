#!/usr/bin/env python3
"""
Упрощенный скрипт запуска тестов
"""
import sys
import subprocess
import logging
from pathlib import Path

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_tests():
    """Запуск тестов"""
    logger.info("Запуск тестов AI Decision Simulator...")

    # Создаем папку logs если не существует
    Path("logs").mkdir(exist_ok=True)

    # Команды для запуска тестов
    commands = [
        ["pytest", "tests/", "-v", "--tb=short"],
    ]

    all_passed = True

    for cmd in commands:
        logger.info(f"Запуск команды: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                logger.info("✅ Тесты прошли успешно")
                if result.stdout.strip():
                    print(result.stdout)  # Выводим результаты в консоль
            else:
                logger.error("❌ Тесты завершились с ошибкой")
                if result.stdout:
                    logger.error(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    logger.error(f"STDERR:\n{result.stderr}")
                all_passed = False
                # Выводим ошибки в консоль
                print(result.stderr)

        except Exception as e:
            logger.error(f"Ошибка при запуске тестов: {e}")
            all_passed = False

    if all_passed:
        logger.info("🎉 Все тесты пройдены успешно!")
        return 0
    else:
        logger.error("🔥 Некоторые тесты провалились")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())