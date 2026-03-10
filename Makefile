.PHONY: install dev lint format typecheck test test-cov build docker docker-up docker-down clean all

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check geo_seo/ tests/

format:
	ruff format geo_seo/ tests/

typecheck:
	mypy geo_seo/

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=geo_seo --cov-report=html --cov-report=term-missing

build:
	python -m build

docker:
	docker build -t geo-seo-suite .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf dist/ build/ *.egg-info .coverage htmlcov/ .mypy_cache/ .ruff_cache/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +

all: lint typecheck test
