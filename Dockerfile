FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаём README.md для прохождения проверки (если его нет)
RUN touch README.md

# Copy application code
COPY app/ ./app/

# Copy templates (including index.html)
COPY templates/ ./templates/

# Создаём директорию для статических файлов (обязательно для app.mount)
RUN mkdir -p /app/static

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (для документации)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run application with uvicorn, listening on the dynamic Railway $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
