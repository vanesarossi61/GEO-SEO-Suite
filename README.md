# GEO-SEO Suite v2.0

[![CI](https://github.com/vanesarossi61/geo-seo-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/vanesarossi61/geo-seo-suite/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](https://github.com/vanesarossi61/geo-seo-suite)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Professional GEO/SEO analysis toolkit** for optimising web content visibility
in AI-powered search engines and large language models.

GEO-SEO Suite analyses your web pages across multiple dimensions -- content
quality, structured data, LLM readability, brand consistency, and technical
SEO -- providing actionable scores and generating machine-readable artefacts
like `llms.txt` and enhanced Schema.org markup.

---

## Features

| Phase | Feature | Status |
|-------|---------|--------|
| 0 | Project scaffolding, CLI, config system | Done |
| 0 | Core web extraction (fetcher, parser) | In progress |
| 0 | SQLite persistence layer | Planned |
| 1 | Multi-dimensional scoring engine | Planned |
| 1 | `llms.txt` & Schema.org generation | Planned |
| 1 | Competitive comparison engine | Planned |
| 2 | Temporal monitoring & change detection | Planned |
| 2 | Brand consistency analysis | Planned |
| 3 | REST API server (FastAPI) | Planned |
| 3 | HTML/PDF report generation | Planned |
| 3 | Multi-platform crawlers (Google, Bing AI) | Planned |
| 4 | Internationalisation (i18n) | Planned |
| 4 | Plugin system | Planned |

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/vanesarossi61/geo-seo-suite.git
cd geo-seo-suite

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### CLI Commands

```bash
# Show version
geo-seo --version

# Show all available commands
geo-seo --help

# Generate a configuration template
geo-seo config-init --output geo-seo.yaml

# Analyse a URL
geo-seo analyze https://example.com --format json

# Monitor changes over time
geo-seo monitor https://example.com --days 30

# Generate llms.txt and Schema.org markup
geo-seo generate https://example.com --output-dir ./output

# Compare multiple URLs
geo-seo compare https://example.com https://competitor.com

# Start API server
geo-seo serve --host 0.0.0.0 --port 8000
```

---

## Project Structure

```
geo-seo-suite/
|-- geo_seo/                  # Main package
|   |-- __init__.py           # Package metadata & version
|   |-- cli.py                # Typer CLI application
|   |-- config/               # Configuration (Pydantic schemas, YAML loader)
|   |-- core/                 # Core extraction (fetcher, parser, models)
|   |-- scoring/              # Multi-dimensional scoring engine
|   |   |-- metrics/          # Individual metric calculators
|   |-- brand/                # Brand consistency analysis
|   |-- generation/           # llms.txt & Schema.org generation
|   |   |-- templates/        # Jinja2 templates for generation
|   |-- crawlers/             # Platform-specific crawlers
|   |-- monitoring/           # Temporal change monitoring
|   |-- platforms/            # Platform integrations
|   |-- reports/              # Report generation (HTML, PDF, CSV)
|   |   |-- templates/        # Report templates
|   |-- api/                  # FastAPI REST server
|   |   |-- routes/           # API route handlers
|   |-- i18n/                 # Internationalisation
|       |-- locales/          # Translation files
|-- tests/                    # Test suite
|   |-- unit/                 # Unit tests
|   |-- integration/          # Integration tests
|   |-- fixtures/             # Shared test fixtures
|   |-- conftest.py           # Pytest configuration & shared fixtures
|-- .github/workflows/ci.yml  # GitHub Actions CI pipeline
|-- pyproject.toml            # Package config (deps, ruff, mypy, pytest)
|-- Dockerfile                # Multi-stage Docker build
|-- docker-compose.yml        # Docker Compose (app + PostgreSQL)
|-- Makefile                  # Dev workflow shortcuts
|-- .pre-commit-config.yaml   # Pre-commit hooks (ruff, mypy)
|-- .gitignore
|-- LICENSE                   # MIT License
|-- README.md                 # This file
```

---

## Development Setup

```bash
# Install dev dependencies
make dev

# Run linter
make lint

# Auto-format code
make format

# Type checking
make typecheck

# Run all tests
make test

# Run tests with coverage
make test-cov

# Run everything (lint + typecheck + test)
make all

# Clean build artefacts
make clean
```

### Docker

```bash
# Build Docker image
make docker

# Start services (app + database)
make docker-up

# Stop services
make docker-down
```

---

## Configuration

Generate a default configuration file:

```bash
geo-seo config-init --output geo-seo.yaml
```

The YAML file includes sections for:

- **general** -- language, output format, log level
- **scoring** -- dimension weights (content quality, structured data, etc.)
- **crawling** -- timeout, retries, user agent, robots.txt compliance
- **monitoring** -- check interval, data retention
- **database** -- storage path

---

## License

This project is licensed under the MIT License -- see the [LICENSE](LICENSE) file for details.

Copyright 2026 Vane Rossi.
