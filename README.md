# Image Processing Service

Асинхронный сервис для обработки изображений с использованием FastAPI, RabbitMQ и PostgreSQL.

## Функциональность

- Загрузка изображений через REST API
- Асинхронная обработка через RabbitMQ
- Создание миниатюр (100x100, 300x300, 1200x1200)
- Хранение метаданных в PostgreSQL
- Мониторинг состояния сервиса

## Архитектура

- **API**: FastAPI приложение
- **Worker**: RabbitMQ потребитель для обработки изображений
- **Database**: PostgreSQL для хранения метаданных
- **Queue**: RabbitMQ для асинхронной обработки
- **Storage**: Локальная файловая система

## Быстрый старт

1. Убедитесь, что у вас установлены Docker и Docker Compose
2. Клонируйте репозиторий
3. Запустите сервис:

```bash
docker compose up --build
```

## API Endpoints

- `POST /images` - Загрузка изображения
- `GET /images/{id}` - Получение информации об изображении
- `GET /health` - Проверка состояния сервиса
- `GET /docs` - Swagger документация
- `GET /redoc` - ReDoc документация

## Разработка

### Установка зависимостей

```bash
# Установка uv (если не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установка зависимостей
uv sync
```

### Запуск в режиме разработки

```bash
# Запуск только инфраструктуры
docker compose up -d postgres rabbitmq

# Запуск API
uv run python -m app.api.main

# Запуск Worker (в отдельном терминале)
uv run python -m app.worker.main
```

### Тестирование

```bash
# Запуск тестов
uv run pytest

# Запуск с покрытием
uv run pytest --cov=app

# Линтинг
uv run flake8 app tests
uv run mypy app
```
├── uploads/              # Хранилище файлов
├── docker/               # Docker конфигурации
└── docker-compose.yml    # Docker Compose
```
