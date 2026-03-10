.DEFAULT_GOAL := help
.PHONY: help install dev lint format typecheck test test-cov build docker docker-up docker-down clean all

PACKAGE   := geo_seo
TESTS     := tests
PYTHON    := python

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install the package (production)
	pip install -e .

dev: ## Install the package with dev dependencies
	pip install -e ".[dev]"
	pre-commit install

lint: ## Run ruff linter
	ruff check $(PACKAGE) $(TESTS)

format: ## Run ruff formatter
	ruff format $(PACKAGE) $(TESTS)

typecheck: ## Run mypy type checker
	mypy $(PACKAGE)

test: ## Run tests
	pytest $(TESTS) -v

test-cov: ## Run tests with coverage report
	pytest $(TESTS) --cov=$(PACKAGE) --cov-report=term-missing --cov-report=html --cov-report=xml

build: ## Build the Python package (sdist + wheel)
	$(PYTHON) -m build

docker: ## Build the Docker image
	docker build -t geo-seo-suite:latest .

docker-up: ## Start all services with Docker Compose
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

clean: ## Remove build artefacts and caches
	rm -rf dist/ build/ *.egg-info
	rm -rf .mypy_cache .ruff_cache .pytest_cache
	rm -rf htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

all: lint typecheck test ## Run lint + typecheck + test
