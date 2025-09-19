.PHONY: help install test lint format clean docker-build docker-up docker-down migrate

help:
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync

test:  ## Run tests
	uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term

lint:  ## Run linting
	uv run flake8 app tests
	uv run mypy app

format:  ## Format code
	uv run black app tests
	uv run isort app tests

clean:  ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache

docker-build:  ## Build Docker images
	docker compose build

docker-up:  ## Start services with Docker Compose
	docker compose up -d

docker-down:  ## Stop services with Docker Compose
	docker compose down

docker-logs:  ## Show Docker logs
	docker compose logs -f

migrate:  ## Run database migrations
	uv run alembic upgrade head

migrate-create:  ## Create new migration
	uv run alembic revision --autogenerate -m "$(MSG)"

dev-setup:  ## Setup development environment
	docker compose up -d postgres rabbitmq
	sleep 10
	uv run alembic upgrade head

dev-api:  ## Run API in development mode
	uv run python -m app.api.main

dev-worker:  ## Run worker in development mode
	uv run python -m app.worker.main

ci:  ## Run CI pipeline locally
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) docker-build
