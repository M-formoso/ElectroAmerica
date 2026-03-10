# =================================
# Electro América - Makefile
# =================================

.PHONY: help install dev up down logs migrate test lint clean

# Default target
help:
	@echo "Electro América - Comandos disponibles:"
	@echo ""
	@echo "  make install    - Instalar dependencias"
	@echo "  make dev        - Iniciar entorno de desarrollo"
	@echo "  make up         - Levantar contenedores Docker"
	@echo "  make down       - Detener contenedores Docker"
	@echo "  make logs       - Ver logs de los contenedores"
	@echo "  make migrate    - Ejecutar migraciones de BD"
	@echo "  make test       - Ejecutar tests"
	@echo "  make lint       - Ejecutar linters"
	@echo "  make clean      - Limpiar archivos temporales"
	@echo ""

# Instalar dependencias
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Desarrollo local (sin Docker)
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Docker commands
up:
	docker-compose up -d

up-build:
	docker-compose up -d --build

down:
	docker-compose down

down-v:
	docker-compose down -v

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-celery:
	docker-compose logs -f celery_worker

# Database
migrate:
	cd backend && alembic upgrade head

migrate-docker:
	docker-compose exec backend alembic upgrade head

makemigrations:
	cd backend && alembic revision --autogenerate -m "$(msg)"

# Testing
test:
	cd backend && pytest -v

test-cov:
	cd backend && pytest --cov=app --cov-report=html

# Linting
lint:
	cd backend && ruff check .
	cd backend && mypy app

format:
	cd backend && ruff format .

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

# Production
prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

# Database backup
backup-db:
	docker-compose exec db pg_dump -U electroamerica electroamerica > backup_$$(date +%Y%m%d_%H%M%S).sql

restore-db:
	docker-compose exec -T db psql -U electroamerica electroamerica < $(file)

# Shell access
shell-backend:
	docker-compose exec backend /bin/sh

shell-db:
	docker-compose exec db psql -U electroamerica electroamerica

# Redis CLI
redis-cli:
	docker-compose exec redis redis-cli
