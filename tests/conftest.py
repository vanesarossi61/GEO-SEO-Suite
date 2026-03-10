"""Shared pytest fixtures for the GEO-SEO Suite test suite."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture()
def sample_html() -> str:
    """Return a realistic HTML page for testing extraction and scoring."""
    return """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Best Practices for Generative Engine Optimization in 2026</title>
    <meta name="description" content="A comprehensive guide to GEO and SEO best practices for optimising content visibility in AI-powered search engines.">
    <link rel="canonical" href="https://example.com/test-page">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Best Practices for Generative Engine Optimization in 2026",
        "author": {
            "@type": "Person",
            "name": "Vane Rossi"
        },
        "datePublished": "2026-03-01",
        "dateModified": "2026-03-10",
        "description": "A comprehensive guide to GEO and SEO best practices.",
        "publisher": {
            "@type": "Organization",
            "name": "GEO-SEO Suite"
        }
    }
    </script>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
        <a href="/blog">Blog</a>
        <a href="/contact">Contact</a>
    </nav>
    <main>
        <article>
            <h1>Best Practices for Generative Engine Optimization in 2026</h1>
            <p>Generative Engine Optimization (GEO) is the practice of making web
            content more discoverable and accurately represented by AI-powered
            search engines and large language models.</p>

            <h2>Understanding GEO vs Traditional SEO</h2>
            <p>While traditional SEO focuses on keyword placement and backlinks,
            GEO emphasises structured data, content clarity, and machine-readable
            markup that LLMs can parse reliably.</p>

            <h2>Key Strategies</h2>
            <p>Implement schema.org JSON-LD, provide an llms.txt file, and ensure
            your content structure follows clear hierarchical headings.</p>

            <h3>Structured Data</h3>
            <p>Use JSON-LD to describe your pages with Article, FAQ, HowTo, and
            Organization schemas.</p>

            <h3>Content Quality</h3>
            <p>Write clear, factual content with proper citations and authoritative
            sourcing to improve trustworthiness signals.</p>
        </article>
    </main>
</body>
</html>
"""


@pytest.fixture()
def sample_url() -> str:
    """Return a canonical test URL."""
    return "https://example.com/test-page"


@pytest.fixture()
def tmp_config_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for configuration files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary path for a SQLite database."""
    return tmp_path / "test_geo_seo.db"
