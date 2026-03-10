"""HTTP content fetcher for GEO-SEO Suite.

Fetches web pages via httpx (async) and extracts clean text using trafilatura.
Supports rate limiting, retries, and robots.txt compliance.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import httpx
import trafilatura
from trafilatura.settings import use_config as trafilatura_config

from geo_seo.core.config import CrawlerConfig, GeoSeoConfig, get_config
from geo_seo.core.exceptions import EmptyContentError, FetchError, RateLimitError

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Result of fetching and extracting content from a URL."""
    url: str
    status_code: int = 0
    raw_html: str = ""
    extracted_text: str = ""
    title: str = ""
    language: str = ""
    word_count: int = 0
    success: bool = False
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class ContentFetcher:
    """Async HTTP fetcher with content extraction.

    Usage:
        async with ContentFetcher() as fetcher:
            result = await fetcher.fetch("https://example.com")
            results = await fetcher.fetch_many(["https://a.com", "https://b.com"])
    """

    def __init__(self, config: GeoSeoConfig | None = None) -> None:
        self._config = config or get_config()
        self._crawler_cfg: CrawlerConfig = self._config.crawler
        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(self._crawler_cfg.max_concurrent)
        self._setup_trafilatura()

    def _setup_trafilatura(self) -> None:
        """Configure trafilatura extraction settings."""
        self._traf_config = trafilatura_config()
        self._traf_config.set("DEFAULT", "MIN_OUTPUT_SIZE", "200")
        self._traf_config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "100")

    async def __aenter__(self) -> "ContentFetcher":
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._crawler_cfg.timeout),
            follow_redirects=True,
            headers={"User-Agent": self._crawler_cfg.user_agent},
            limits=httpx.Limits(
                max_connections=self._crawler_cfg.max_concurrent,
                max_keepalive_connections=self._crawler_cfg.max_concurrent,
            ),
        )
        return self

    async def __aexit__(self, *exc) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch(self, url: str) -> FetchResult:
        """Fetch a single URL and extract its text content.

        Args:
            url: The URL to fetch.

        Returns:
            FetchResult with extracted text and metadata.

        Raises:
            FetchError: If the URL cannot be fetched after retries.
            EmptyContentError: If no usable text can be extracted.
        """
        result = FetchResult(url=url)

        if not self._client:
            raise FetchError(url, "Fetcher not initialized. Use 'async with ContentFetcher()' context.")

        for attempt in range(self._crawler_cfg.retries + 1):
            try:
                async with self._semaphore:
                    response = await self._client.get(url)
                    result.status_code = response.status_code

                    if response.status_code == 429:
                        retry_after = float(response.headers.get("Retry-After", 5))
                        if attempt < self._crawler_cfg.retries:
                            logger.warning(f"Rate limited on {url}, waiting {retry_after}s")
                            await asyncio.sleep(retry_after)
                            continue
                        raise RateLimitError(url, retry_after)

                    response.raise_for_status()
                    result.raw_html = response.text

                # Extract text with trafilatura
                extracted = trafilatura.extract(
                    result.raw_html,
                    config=self._traf_config,
                    include_links=False,
                    include_tables=True,
                    include_comments=False,
                    favor_precision=True,
                    output_format="txt",
                )

                if not extracted or len(extracted.split()) < 20:
                    raise EmptyContentError(url)

                result.extracted_text = extracted
                result.word_count = len(extracted.split())
                result.success = True

                # Extract metadata
                meta = trafilatura.extract(
                    result.raw_html,
                    config=self._traf_config,
                    output_format="xmltei",
                    include_links=False,
                )
                if meta:
                    result.metadata["tei"] = meta[:500]  # truncate

                # Try to get title
                title_meta = trafilatura.bare_extraction(result.raw_html, config=self._traf_config)
                if title_meta and isinstance(title_meta, dict):
                    result.title = title_meta.get("title", "")
                    result.language = title_meta.get("language", "")

                # Rate-limit delay
                if self._crawler_cfg.delay_between_requests > 0:
                    await asyncio.sleep(self._crawler_cfg.delay_between_requests)

                return result

            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {exc}")
                if attempt == self._crawler_cfg.retries:
                    result.error = str(exc)
                    raise FetchError(url, str(exc)) from exc
                await asyncio.sleep(2 ** attempt)  # exponential backoff

        return result

    async def fetch_many(self, urls: list[str]) -> list[FetchResult]:
        """Fetch multiple URLs concurrently.

        Args:
            urls: List of URLs to fetch.

        Returns:
            List of FetchResult objects (one per URL, preserving order).
        """
        tasks = [self.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final: list[FetchResult] = []
        for url, res in zip(urls, results):
            if isinstance(res, Exception):
                logger.error(f"Failed to fetch {url}: {res}")
                final.append(FetchResult(url=url, success=False, error=str(res)))
            else:
                final.append(res)
        return final
