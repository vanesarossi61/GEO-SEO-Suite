"""GEO-SEO Suite custom exceptions."""

from __future__ import annotations


class GeoSeoError(Exception):
    """Base exception for GEO-SEO Suite."""


# -- Crawling / Fetching --
class FetchError(GeoSeoError):
    """Raised when a URL cannot be fetched."""

    def __init__(self, url: str, reason: str = "") -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch {url}: {reason}" if reason else f"Failed to fetch {url}")


class RateLimitError(FetchError):
    """Raised when rate-limited by a remote server or API."""

    def __init__(self, url: str, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        msg = f"Rate-limited by {url}"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(url, msg)


# -- Scoring / Analysis --
class ScoringError(GeoSeoError):
    """Raised when scoring a page or passage fails."""


class EmptyContentError(ScoringError):
    """Raised when extracted content is empty or too short to score."""

    def __init__(self, url: str = "") -> None:
        self.url = url
        msg = f"No usable content extracted from {url}" if url else "No usable content extracted"
        super().__init__(msg)


class PassageSegmentationError(ScoringError):
    """Raised when passage segmentation fails."""


# -- LLM Validation --
class LLMValidationError(GeoSeoError):
    """Raised when LLM validation encounters an error."""


class LLMProviderError(LLMValidationError):
    """Raised when a specific LLM provider returns an error."""

    def __init__(self, provider: str, reason: str = "") -> None:
        self.provider = provider
        super().__init__(f"[{provider}] {reason}")


class LLMQuotaExceededError(LLMProviderError):
    """Raised when LLM API quota is exhausted."""


# -- Configuration --
class ConfigError(GeoSeoError):
    """Raised when configuration is invalid or missing."""


class MissingAPIKeyError(ConfigError):
    """Raised when a required API key is not configured."""

    def __init__(self, key_name: str) -> None:
        self.key_name = key_name
        super().__init__(
            f"Missing API key: {key_name}. "
            f"Set it in geo-seo.yaml or via environment variable."
        )
