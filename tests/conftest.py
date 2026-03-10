"""Shared pytest fixtures for the GEO-SEO Suite test suite."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def sample_html() -> str:
    """Return a realistic HTML page for testing extraction and scoring."""
    return """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Best Practices for GEO in 2026</title>
    <meta name="description" content="A guide to GEO and SEO best practices.">
    <link rel="canonical" href="https://example.com/test-page">
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Article","headline":"GEO in 2026"}
    </script>
</head>
<body>
    <main>
        <article>
            <h1>Best Practices for GEO in 2026</h1>
            <p>GEO makes web content discoverable by AI search engines.</p>
            <h2>Key Strategies</h2>
            <p>Use schema.org JSON-LD and provide an llms.txt file.</p>
        </article>
    </main>
</body>
</html>
"""


@pytest.fixture
def sample_url() -> str:
    """Return a canonical test URL."""
    return "https://example.com/test-page"


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for configuration files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary path for a SQLite database."""
    return tmp_path / "test_geo_seo.db"
