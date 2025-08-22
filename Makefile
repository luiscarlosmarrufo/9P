.PHONY: help setup format lint test test-unit test-integration clean build run compose-up compose-down docker-build

# Default target
help:
	@echo "Available targets:"
	@echo "  setup          - Install dependencies and setup development environment"
	@echo "  format         - Format code with black and ruff"
	@echo "  lint           - Lint code with ruff and mypy"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  clean          - Clean up build artifacts and cache"
	@echo "  build          - Build Docker images"
	@echo "  run            - Run the application locally"
	@echo "  compose-up     - Start all services with docker-compose"
	@echo "  compose-down   - Stop all services"
	@echo "  docker-build   - Build all Docker images"

# Development setup
setup:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"
	pre-commit install
	@echo "Setup complete! Copy .env.example to .env and configure your settings."

# Code formatting
format:
	black .
	ruff --fix .

# Code linting
lint:
	ruff check .
	mypy .
	@echo "Linting complete!"

# Testing
test:
	pytest -v --cov-report=term-missing

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v --tb=short

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/

# Docker operations
build: docker-build

docker-build:
	docker build -f docker/Dockerfile.control -t 9p-control .
	docker build -f docker/Dockerfile.worker -t 9p-worker .
	docker build -f docker/Dockerfile.web -t 9p-web .
	docker build -f docker/Dockerfile.inference -t 9p-inference .

# Local development
run:
	uvicorn control.main:app --host 0.0.0.0 --port 8000 --reload

run-worker:
	celery -A worker.main worker --loglevel=info

run-web:
	streamlit run web/main.py --server.port 8501

# Docker Compose operations
compose-up:
	docker-compose -f docker/docker-compose.yml up -d
	@echo "Services started! Check status with: docker-compose -f docker/docker-compose.yml ps"

compose-down:
	docker-compose -f docker/docker-compose.yml down

compose-logs:
	docker-compose -f docker/docker-compose.yml logs -f

# Database operations
db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-revision:
	alembic revision --autogenerate -m "$(MSG)"

db-reset:
	alembic downgrade base
	alembic upgrade head

# Development utilities
install-dev:
	pip install -e ".[dev]"

check-deps:
	pip-audit

security-check:
	bandit -r control/ worker/ ml/ web/

# CI/CD helpers
ci-test:
	pytest --cov=control --cov=worker --cov=ml --cov=web --cov-report=xml --cov-report=term

ci-lint:
	ruff check . --output-format=github
	mypy . --junit-xml=mypy-results.xml

# Monitoring
logs:
	docker-compose -f docker/docker-compose.yml logs -f

ps:
	docker-compose -f docker/docker-compose.yml ps

stats:
	docker stats
