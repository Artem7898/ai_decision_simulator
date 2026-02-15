# AI Decision Simulator

Интеллектуальный симулятор принятия решений с использованием AI и Monte Carlo моделирования.

## Возможности

- **Переезд**: Сравнение городов (стоимость жизни, налоги, качество жизни)
- **Покупки**: Анализ вариантов покупки (авто, недвижимость)
- **Работа**: Сравнение предложений работы (зарплата, рост, баланс)
- **Инвестиции**: Анализ инвестиционных опций (доходность, риски)

## Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   User      │────▶│   FastAPI    │────▶│  LLM Service    │
│   Query     │     │   Backend    │     │  (Structuring)  │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Data Layer  │
                    │ (APIs/Cache) │
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Simulation  │
                    │   Engine     │
                    │ (Monte Carlo)│
                    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  AI Report   │
                    │  Generation  │
                    └──────────────┘
```

## Быстрый старт

### Требования

- Docker & Docker Compose
- OpenAI API key (опционально)

### Запуск

1. Клонируйте репозиторий и перейдите в папку:
```bash
cd ai-decision-simulator
```

2. Создайте `.env` файл:
```bash
cp .env.example .env
# Отредактируйте .env и добавьте ваш OPENAI_API_KEY
```

3. Запустите все сервисы:
```bash
docker compose up -d
```

4. Проверьте статус:
```bash
docker compose ps
```

5. Откройте API документацию:
```
http://localhost:8000/docs
```

## API Endpoints

### Scenarios (Сценарии)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/scenarios` | Создать сценарий |
| GET | `/api/v1/scenarios` | Список сценариев |
| GET | `/api/v1/scenarios/{id}` | Получить сценарий |
| DELETE | `/api/v1/scenarios/{id}` | Удалить сценарий |

### Simulations (Симуляции)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/simulations` | Запустить симуляцию |
| GET | `/api/v1/simulations/{id}` | Получить результаты |
| GET | `/api/v1/scenarios/{id}/simulations` | Симуляции сценария |
| POST | `/api/v1/simulate` | Быстрая симуляция |

## Примеры использования

### Создание сценария переезда

```bash
curl -X POST "http://localhost:8000/api/v1/scenarios" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Переезд в Европу",
    "decision_type": "relocation",
    "description": "Выбор между Берлином и Амстердамом"
  }'
```

### Запуск симуляции

```bash
curl -X POST "http://localhost:8000/api/v1/simulations" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": 1,
    "input_data": {
      "query": "Move to Berlin vs Amsterdam as a software engineer with 80k salary",
      "time_horizon_years": 5,
      "monte_carlo_runs": 1000
    }
  }'
```

### Быстрая симуляция (без создания сценария)

```bash
curl -X POST "http://localhost:8000/api/v1/simulate?query=Should%20I%20invest%20in%20stocks%20or%20bonds&decision_type=investment&time_horizon_years=10"
```

## Структура проекта

```
ai-decision-simulator/
├── app/
│   ├── api/
│   │   └── endpoints.py      # API маршруты
│   ├── core/
│   │   ├── config.py         # Конфигурация
│   │   └── exceptions.py     # Обработка ошибок
│   ├── db/
│   │   └── session.py        # Подключение к БД
│   ├── models/
│   │   └── database.py       # SQLAlchemy модели
│   ├── schemas/
│   │   └── schemas.py        # Pydantic схемы
│   ├── services/
│   │   ├── llm_service.py    # LLM интеграция
│   │   ├── simulation_engine.py  # Движок симуляции
│   │   └── celery_worker.py  # Фоновые задачи
│   └── main.py               # Точка входа
├── tests/
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.celery
├── pyproject.toml
└── README.md
```

## Модели базы данных

### Users
- `id`: Primary key
- `email`: Уникальный email
- `hashed_password`: Хэш пароля
- `created_at`: Дата создания

### Scenarios
- `id`: Primary key
- `user_id`: FK на Users
- `name`: Название сценария
- `decision_type`: Тип решения (relocation/purchase/job/investment)
- `description`: Описание
- `created_at`, `updated_at`: Timestamps

### Simulations
- `id`: Primary key
- `scenario_id`: FK на Scenarios
- `input_data`: JSON с входными данными
- `result_json`: JSON с результатами
- `status`: pending/running/completed/failed
- `error_message`: Сообщение об ошибке
- `created_at`, `completed_at`: Timestamps

### CachedData
- `id`: Primary key
- `cache_key`: Уникальный ключ кэша
- `data`: JSON данные
- `source`: Источник данных
- `expires_at`: Время истечения

## Масштабирование

### Celery Workers

Для тяжёлых симуляций (Monte Carlo с большим количеством итераций):

```bash
# Увеличить количество воркеров
docker compose up -d --scale celery_worker=4
```

### Кэширование

Часто запрашиваемые данные (стоимость жизни, налоги) кэшируются в PostgreSQL с настраиваемым TTL.

### Асинхронность

- Все внешние API вызовы асинхронны
- FastAPI + asyncpg для неблокирующей работы с БД
- Celery для фоновых задач

## Deployment (Production)

### Рекомендации

1. **Используйте managed PostgreSQL** (RDS, Cloud SQL)
2. **Используйте managed Redis** (ElastiCache, Memorystore)
3. **Настройте HTTPS** через reverse proxy (nginx, traefik)
4. **Добавьте мониторинг** (Prometheus + Grafana)
5. **Настройте логирование** (ELK stack, CloudWatch)

### Переменные окружения для production

```env
DEBUG=false
SECRET_KEY=<сгенерируйте-безопасный-ключ-min-32-chars>
DATABASE_URL=postgresql://user:pass@managed-db:5432/decision_simulator
REDIS_URL=redis://managed-redis:6379/0
OPENAI_API_KEY=sk-...
```

### Docker Compose для production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Расширение функциональности

### Добавление нового типа решения

1. Добавьте новый тип в `DecisionType` enum
2. Добавьте схему факторов в `schemas.py`
3. Добавьте метод симуляции в `SimulationEngine`
4. Обновите промпты в `LLMService`

### Добавление внешнего API

1. Добавьте API key в конфигурацию
2. Реализуйте метод в `DataService`
3. Добавьте кэширование результатов

## Лицензия

MIT
