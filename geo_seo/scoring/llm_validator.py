"""LLM Validator -- validates citability against real LLM responses.

Generates niche queries, checks if a domain appears in LLM-generated responses,
and compares theoretical citability scores against actual citation rates.

Supports: OpenAI (ChatGPT), Anthropic (Claude), Perplexity.
Includes SQLite caching and rate limiting for cost control.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from geo_seo.core.config import GeoSeoConfig, LLMConfig, get_config
from geo_seo.core.exceptions import (
    LLMProviderError,
    LLMQuotaExceededError,
    LLMValidationError,
    MissingAPIKeyError,
)
from geo_seo.core.models import (
    CitationCheck,
    FidelityScore,
    LLMValidationResult,
)

logger = logging.getLogger(__name__)


class LLMValidator:
    """Validates content citability by querying real LLMs.

    Usage:
        validator = LLMValidator()
        queries = validator.generate_niche_queries("https://example.com/seo-guide", niche="SEO")
        result = validator.validate(
            url="https://example.com/seo-guide",
            queries=queries,
            theoretical_score=0.72,
        )
        print(f"Citation rate: {result.citation_rate:.0%}")
        print(f"Theory vs Real gap: {result.gap:+.2f}")
    """

    def __init__(self, config: GeoSeoConfig | None = None) -> None:
        self._config = config or get_config()
        self._llm_cfg: LLMConfig = self._config.llm
        self._cache = _ValidationCache(self._llm_cfg.cache_db_path, self._llm_cfg.cache_ttl_hours)
        self._providers: dict[str, _LLMProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        """Initialize available LLM providers based on configured API keys."""
        if self._llm_cfg.openai_api_key:
            self._providers["openai"] = _OpenAIProvider(self._llm_cfg.openai_api_key)
        if self._llm_cfg.anthropic_api_key:
            self._providers["anthropic"] = _AnthropicProvider(self._llm_cfg.anthropic_api_key)
        if self._llm_cfg.perplexity_api_key:
            self._providers["perplexity"] = _PerplexityProvider(self._llm_cfg.perplexity_api_key)

        if not self._providers and not self._llm_cfg.offline_mode:
            logger.warning(
                "No LLM API keys configured. Running in offline mode. "
                "Set keys in geo-seo.yaml or via environment variables."
            )

    @property
    def available_providers(self) -> list[str]:
        """List of configured provider names."""
        return list(self._providers.keys())

    def generate_niche_queries(
        self,
        url: str,
        niche: str = "",
        count: int = 5,
    ) -> list[str]:
        """Generate niche-specific queries that might cite the given URL.

        Args:
            url: The target URL.
            niche: Topic/niche keyword (e.g., "SEO", "Python", "marketing").
            count: Number of queries to generate (5-10).

        Returns:
            List of natural-language queries.
        """
        domain = urlparse(url).netloc
        path_parts = [p for p in urlparse(url).path.split("/") if p]
        topic = niche or " ".join(path_parts[-2:]) if path_parts else domain

        # Template-based query generation (no LLM needed)
        templates_es = [
            f"Que es {topic} y como funciona",
            f"Mejores herramientas de {topic} en 2026",
            f"Guia completa de {topic}",
            f"Como implementar {topic} paso a paso",
            f"{topic} vs alternativas comparacion",
            f"Beneficios y riesgos de {topic}",
            f"Estadisticas de {topic} actualizadas",
            f"Errores comunes en {topic}",
            f"Tendencias de {topic} para 2026",
            f"Mejores practicas de {topic} segun expertos",
        ]

        templates_en = [
            f"What is {topic} and how does it work",
            f"Best {topic} tools in 2026",
            f"Complete guide to {topic}",
            f"How to implement {topic} step by step",
            f"{topic} vs alternatives comparison",
            f"Benefits and risks of {topic}",
            f"Updated {topic} statistics",
            f"Common {topic} mistakes to avoid",
            f"{topic} trends for 2026",
            f"{topic} best practices according to experts",
        ]

        # Use locale to choose language
        if self._config.output.locale.startswith("es"):
            templates = templates_es
        else:
            templates = templates_en

        return templates[:count]

    def check_citation_presence(
        self,
        query: str,
        domain: str,
        providers: list[str] | None = None,
    ) -> list[CitationCheck]:
        """Check if a domain appears in LLM responses for a query.

        Args:
            query: The search query to send to LLMs.
            domain: Domain to look for (e.g., "example.com").
            providers: Specific providers to use (default: all configured).

        Returns:
            List of CitationCheck results, one per provider queried.
        """
        target_providers = providers or list(self._providers.keys())
        results: list[CitationCheck] = []

        for provider_name in target_providers:
            # Check cache first
            cached = self._cache.get(query, provider_name)
            if cached:
                results.append(cached)
                continue

            provider = self._providers.get(provider_name)
            if not provider:
                logger.warning(f"Provider {provider_name} not configured, skipping")
                continue

            try:
                response_text = provider.query(query)
                domain_lower = domain.lower()
                resp_lower = response_text.lower()
                cited = domain_lower in resp_lower

                # Find citation context
                context = ""
                if cited:
                    idx = resp_lower.find(domain_lower)
                    start = max(0, idx - 100)
                    end = min(len(response_text), idx + len(domain) + 100)
                    context = response_text[start:end]

                check = CitationCheck(
                    query=query,
                    provider=provider_name,
                    response_text=response_text[:1000],  # truncate
                    domain_cited=cited,
                    citation_context=context,
                    confidence=0.9 if cited else 0.1,
                    cached=False,
                )
                results.append(check)
                self._cache.put(query, provider_name, check)

            except Exception as exc:
                logger.error(f"Error querying {provider_name}: {exc}")
                results.append(CitationCheck(
                    query=query,
                    provider=provider_name,
                    domain_cited=False,
                    confidence=0.0,
                ))

        return results

    def validate(
        self,
        url: str,
        queries: list[str],
        theoretical_score: float = 0.0,
    ) -> LLMValidationResult:
        """Run full validation: check citations and compute gap.

        Args:
            url: Target URL being validated.
            queries: List of queries to test.
            theoretical_score: Citability score from the scorer.

        Returns:
            LLMValidationResult with citation rate, fidelity, and gap analysis.
        """
        domain = urlparse(url).netloc

        if self._llm_cfg.offline_mode or not self._providers:
            logger.info("Running in offline mode -- returning cached/empty results")
            return LLMValidationResult(
                url=url,
                domain=domain,
                queries_tested=queries,
                citation_rate=0.0,
                avg_fidelity=0.0,
                theoretical_score=theoretical_score,
                real_score=0.0,
                gap=theoretical_score,
            )

        all_checks: list[CitationCheck] = []
        for query in queries[: self._llm_cfg.max_queries_per_run]:
            checks = self.check_citation_presence(query, domain)
            all_checks.extend(checks)

        # Compute citation rate
        if all_checks:
            citation_rate = sum(1 for c in all_checks if c.domain_cited) / len(all_checks)
        else:
            citation_rate = 0.0

        real_score = citation_rate
        gap = theoretical_score - real_score

        return LLMValidationResult(
            url=url,
            domain=domain,
            queries_tested=queries,
            citation_checks=all_checks,
            citation_rate=round(citation_rate, 4),
            avg_fidelity=0.0,  # TODO: implement fidelity scoring
            theoretical_score=theoretical_score,
            real_score=round(real_score, 4),
            gap=round(gap, 4),
        )


# -- Cache --

class _ValidationCache:
    """SQLite-based cache for LLM validation results."""

    def __init__(self, db_path: str, ttl_hours: int = 24) -> None:
        self._db_path = Path(db_path)
        self._ttl = timedelta(hours=ttl_hours)
        self._init_db()

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    cache_key TEXT PRIMARY KEY,
                    provider TEXT,
                    result_json TEXT,
                    created_at TEXT
                )
            """)

    def _key(self, query: str, provider: str) -> str:
        raw = f"{provider}:{query}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, query: str, provider: str) -> Optional[CitationCheck]:
        key = self._key(query, provider)
        with sqlite3.connect(str(self._db_path)) as conn:
            row = conn.execute(
                "SELECT result_json, created_at FROM llm_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
        if not row:
            return None

        created = datetime.fromisoformat(row[1])
        if datetime.utcnow() - created > self._ttl:
            return None  # expired

        data = json.loads(row[0])
        check = CitationCheck(**data)
        check.cached = True
        return check

    def put(self, query: str, provider: str, result: CitationCheck) -> None:
        key = self._key(query, provider)
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO llm_cache (cache_key, provider, result_json, created_at) VALUES (?, ?, ?, ?)",
                (key, provider, result.model_dump_json(), datetime.utcnow().isoformat()),
            )


# -- LLM Provider Abstractions --

class _LLMProvider:
    """Base class for LLM providers."""

    def query(self, prompt: str) -> str:
        raise NotImplementedError


class _OpenAIProvider(_LLMProvider):
    """OpenAI/ChatGPT provider."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def query(self, prompt: str) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except ImportError:
            raise LLMProviderError("openai", "openai package not installed. Run: pip install openai")
        except Exception as exc:
            raise LLMProviderError("openai", str(exc))


class _AnthropicProvider(_LLMProvider):
    """Anthropic/Claude provider."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def query(self, prompt: str) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text if response.content else ""
        except ImportError:
            raise LLMProviderError("anthropic", "anthropic package not installed. Run: pip install anthropic")
        except Exception as exc:
            raise LLMProviderError("anthropic", str(exc))


class _PerplexityProvider(_LLMProvider):
    """Perplexity provider (OpenAI-compatible API)."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def query(self, prompt: str) -> str:
        try:
            import openai
            client = openai.OpenAI(
                api_key=self._api_key,
                base_url="https://api.perplexity.ai",
            )
            response = client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
            )
            return response.choices[0].message.content or ""
        except ImportError:
            raise LLMProviderError("perplexity", "openai package not installed. Run: pip install openai")
        except Exception as exc:
            raise LLMProviderError("perplexity", str(exc))
