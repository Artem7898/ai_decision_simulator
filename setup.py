#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="ai-decision-simulator",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "sqlalchemy>=2.0.25",
        "asyncpg>=0.29.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "httpx>=0.26.0",
        "numpy>=1.26.0",
        "celery>=5.3.0",
        "redis>=5.0.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "alembic>=1.13.0",
        "aiosqlite>=0.20.0",
        "yfinance>=0.2.28",
        "pandas>=2.0.0",
        "jinja2>=3.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
            "pytest-httpx>=0.27.0",
            "pytest-mock>=3.12.0",
            "pytest-xdist>=3.5.0",
            "black>=24.1.0",
            "isort>=5.13.0",
            "mypy>=1.8.0",
            "freezegun>=1.2.2",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
            "pytest-httpx>=0.27.0",
            "pytest-mock>=3.12.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "run-app=app.main:app",
            "run-tests=run_tests:run_tests",
        ],
    },
)