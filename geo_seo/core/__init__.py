"""Core module: configuration, models, and exceptions."""

from geo_seo.core.config import GeoSeoConfig, get_config
from geo_seo.core.exceptions import (
    ConfigError,
    EmptyContentError,
    FetchError,
    GeoSeoError,
    LLMProviderError,
    LLMValidationError,
    MissingAPIKeyError,
    RateLimitError,
    ScoringError,
)
from geo_seo.core.models import (
    AnalysisReport,
    ContentFormat,
    MultiPersonaResult,
    PageScore,
    PassageScore,
    PersonaType,
)

__all__ = [
    "GeoSeoConfig",
    "get_config",
    "ConfigError",
    "EmptyContentError",
    "FetchError",
    "GeoSeoError",
    "LLMProviderError",
    "LLMValidationError",
    "MissingAPIKeyError",
    "RateLimitError",
    "ScoringError",
    "AnalysisReport",
    "ContentFormat",
    "MultiPersonaResult",
    "PageScore",
    "PassageScore",
    "PersonaType",
]
