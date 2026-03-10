"""Configuration management for GEO-SEO Suite.

Reads settings from geo-seo.yaml, environment variables, and CLI overrides.
Uses pydantic-settings for validation and type coercion.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# -- Sub-models for nested config sections --

class CrawlerConfig(BaseModel):
    """Settings for the HTTP crawler/fetcher."""
    max_concurrent: int = Field(default=5, ge=1, le=50)
    timeout: float = Field(default=30.0, ge=1.0)
    retries: int = Field(default=3, ge=0, le=10)
    user_agent: str = "GEO-SEO-Suite/2.0"
    respect_robots: bool = True
    delay_between_requests: float = Field(default=1.0, ge=0.0)


class ScoringConfig(BaseModel):
    """Settings for the citability scoring engine."""
    # Weight distribution for the 6 GEO metrics (must sum to ~1.0)
    weight_extractability: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_qa_detection: float = Field(default=0.15, ge=0.0, le=1.0)
    weight_data_density: float = Field(default=0.15, ge=0.0, le=1.0)
    weight_answer_first: float = Field(default=0.20, ge=0.0, le=1.0)
    weight_self_contained: float = Field(default=0.15, ge=0.0, le=1.0)
    weight_eeat_signals: float = Field(default=0.10, ge=0.0, le=1.0)
    # Passage analysis
    optimal_passage_min_words: int = Field(default=134, ge=50)
    optimal_passage_max_words: int = Field(default=167, le=500)
    top_passages_count: int = Field(default=10, ge=1, le=50)
    answer_first_window_words: int = Field(default=60, ge=20, le=120)


class LLMConfig(BaseModel):
    """Settings for LLM validation."""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    default_provider: str = "openai"
    cache_ttl_hours: int = Field(default=24, ge=1)
    cache_db_path: str = ".geo-seo-cache/llm_cache.sqlite"
    max_queries_per_run: int = Field(default=10, ge=1, le=100)
    offline_mode: bool = False


class OutputConfig(BaseModel):
    """Settings for report output."""
    format: str = Field(default="json", pattern="^(json|html|markdown|csv)$")
    output_dir: str = "reports"
    include_passages: bool = True
    include_rewrites: bool = True
    locale: str = "es"


# -- Main config --

class GeoSeoConfig(BaseSettings):
    """Root configuration for GEO-SEO Suite.

    Priority (highest to lowest):
    1. CLI arguments (passed directly)
    2. Environment variables (GEO_SEO_ prefix)
    3. geo-seo.yaml config file
    4. Defaults defined here
    """

    model_config = SettingsConfigDict(
        env_prefix="GEO_SEO_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    # Top-level settings
    verbose: bool = False
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    project_name: str = "geo-seo-project"

    # Nested configs
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @classmethod
    def from_yaml(cls, path: str | Path = "geo-seo.yaml", **overrides: Any) -> "GeoSeoConfig":
        """Load configuration from a YAML file with optional overrides."""
        config_path = Path(path)
        yaml_data: dict[str, Any] = {}

        if config_path.exists():
            with open(config_path) as f:
                raw = yaml.safe_load(f)
                if isinstance(raw, dict):
                    yaml_data = raw

        # Merge: yaml < env vars < explicit overrides
        yaml_data.update(overrides)
        return cls(**yaml_data)

    @classmethod
    def default(cls) -> "GeoSeoConfig":
        """Return config with all defaults (no file, no env)."""
        return cls()


def get_config(config_path: str | Path | None = None, **overrides: Any) -> GeoSeoConfig:
    """Convenience function to load or create config.

    Args:
        config_path: Path to geo-seo.yaml. If None, tries CWD.
        **overrides: Direct overrides for any config key.

    Returns:
        Validated GeoSeoConfig instance.
    """
    if config_path:
        return GeoSeoConfig.from_yaml(config_path, **overrides)

    # Try to find geo-seo.yaml in CWD or parent dirs
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / "geo-seo.yaml"
        if candidate.exists():
            return GeoSeoConfig.from_yaml(candidate, **overrides)
        # Stop at home dir
        if parent == Path.home():
            break

    return GeoSeoConfig.default()
