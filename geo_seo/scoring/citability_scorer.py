"""Citability Scorer -- 6 evidence-based GEO 2026 metrics.

Scores content passages on their likelihood of being cited by LLMs,
based on research from GEO (Generative Engine Optimization) studies.

Metrics and their evidence base:
1. Extractability (+400% citation rate for structured content)
2. Q&A Detection (+23% citation boost)
3. Quantitative Data Density (+40% citation boost)
4. Answer-First Pattern (top citation factor)
5. Self-Contained Passages (optimal 134-167 words)
6. E-E-A-T Signals (+15-25% citation boost)
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from typing import Optional

from geo_seo.core.config import GeoSeoConfig, ScoringConfig, get_config
from geo_seo.core.exceptions import EmptyContentError, ScoringError
from geo_seo.core.models import (
    ContentFormat,
    MetricScore,
    PageScore,
    PassageScore,
)

logger = logging.getLogger(__name__)


# -- Pattern constants --

# Q&A patterns in multiple languages
QA_PATTERNS = [
    r"(?:^|\n)\s*(?:Q|P|Pregunta|Question)\s*[:.]",
    r"(?:^|\n)\s*(?:A|R|Respuesta|Answer)\s*[:.]",
    r"\?\s*\n+\s*[A-Z\u00c0-\u00dc]",  # Question mark followed by answer
    r"(?:^|\n)#{1,3}\s+.+\?\s*$",  # Heading as question
    r"(?:^|\n)\*\*.+\?\*\*",  # Bold question
]

# Structured content patterns
LIST_PATTERN = r"(?:^|\n)\s*(?:[-*\u2022]|\d+[.)]\s)"
TABLE_PATTERN = r"(?:\|.+\|[\s\n]+\|[-:]+\|)|(?:<table)"
DEFINITION_PATTERN = r"(?:^|\n)\s*\*\*[^*]+\*\*\s*[:.\u2013\u2014-]\s+"

# Data/number patterns
NUMBER_PATTERN = r"\b\d+(?:[.,]\d+)?(?:\s*%|\s*(?:USD|EUR|MXN|\$|€)|\s*(?:veces|times|x))\b"
STAT_PATTERN = r"(?:seg[uú]n|according to|study|estudio|research|investigaci[oó]n|data|datos)\b"
YEAR_PATTERN = r"\b20[12]\d\b"

# E-E-A-T signal patterns
AUTHOR_PATTERN = r"(?:por|by|author|autor|escrito por|written by)\s+[A-Z\u00c0-\u00dc][a-z\u00e0-\u00fc]+"
DATE_PATTERN = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b"
SOURCE_PATTERN = r"(?:fuente|source|referencia|reference|citado en|cited in|seg[uú]n|according to)\s*[:.]?\s*[A-Z]"


class CitabilityScorer:
    """Scores content passages using 6 GEO 2026 metrics.

    Usage:
        scorer = CitabilityScorer()
        passage_score = scorer.score_passage("Some text content...")
        page_score = scorer.score_page(passages=["text1", "text2", ...], url="https://...")
    """

    def __init__(self, config: GeoSeoConfig | None = None) -> None:
        self._config = config or get_config()
        self._scoring: ScoringConfig = self._config.scoring

    # -- Public API --

    def score_passage(self, text: str, passage_id: int = 0) -> PassageScore:
        """Score a single text passage on all 6 metrics.

        Args:
            text: The passage text to score.
            passage_id: Optional ID for tracking.

        Returns:
            PassageScore with all metric breakdowns.

        Raises:
            EmptyContentError: If text is empty or too short.
        """
        text = text.strip()
        if not text or len(text.split()) < 10:
            raise EmptyContentError()

        word_count = len(text.split())
        content_format = self._detect_format(text)

        metrics = [
            self._score_extractability(text),
            self._score_qa_detection(text),
            self._score_data_density(text),
            self._score_answer_first(text),
            self._score_self_contained(text, word_count),
            self._score_eeat_signals(text),
        ]

        composite = sum(m.weighted_score for m in metrics)
        composite = min(1.0, max(0.0, composite))

        return PassageScore(
            passage_id=passage_id,
            text=text,
            word_count=word_count,
            content_format=content_format,
            metrics=metrics,
            composite_score=round(composite, 4),
            is_citable=composite >= 0.6,
        )

    def score_page(
        self,
        passages: list[str],
        url: str = "",
        title: str = "",
    ) -> PageScore:
        """Score an entire page by scoring its individual passages.

        The page score is the average of the top-N passage scores.

        Args:
            passages: List of text passages from the page.
            url: Page URL for tracking.
            title: Page title.

        Returns:
            PageScore with aggregate metrics and passage details.
        """
        if not passages:
            raise EmptyContentError(url)

        scored: list[PassageScore] = []
        for i, passage_text in enumerate(passages):
            try:
                scored.append(self.score_passage(passage_text, passage_id=i))
            except EmptyContentError:
                logger.debug(f"Skipping empty passage {i} in {url}")
                continue

        if not scored:
            raise EmptyContentError(url)

        # Sort by composite score descending
        scored_sorted = sorted(scored, key=lambda p: p.composite_score, reverse=True)
        top_n = scored_sorted[: self._scoring.top_passages_count]

        page_score_val = sum(p.composite_score for p in top_n) / len(top_n)

        # Per-metric averages across all passages
        metric_names = {m.name for p in scored for m in p.metrics}
        metric_avgs: dict[str, float] = {}
        for name in metric_names:
            values = [
                m.weighted_score
                for p in scored
                for m in p.metrics
                if m.name == name
            ]
            if values:
                metric_avgs[name] = round(sum(values) / len(values), 4)

        return PageScore(
            url=url,
            title=title,
            total_words=sum(p.word_count for p in scored),
            total_passages=len(scored),
            citable_passages=sum(1 for p in scored if p.is_citable),
            page_score=round(page_score_val, 4),
            best_passage_score=scored_sorted[0].composite_score if scored_sorted else 0.0,
            worst_passage_score=scored_sorted[-1].composite_score if scored_sorted else 0.0,
            metric_averages=metric_avgs,
            passages=scored,
            top_passages=top_n,
        )

    # -- Metric scorers (private) --

    def _score_extractability(self, text: str) -> MetricScore:
        """Metric 1: Structured content extractability (+400% citation).

        Checks for lists, tables, definitions, and structured formatting.
        """
        score = 0.0
        signals = []

        # Lists
        list_matches = len(re.findall(LIST_PATTERN, text))
        if list_matches >= 3:
            score += 0.4
            signals.append(f"{list_matches} list items")
        elif list_matches >= 1:
            score += 0.2

        # Tables
        if re.search(TABLE_PATTERN, text, re.IGNORECASE):
            score += 0.35
            signals.append("table detected")

        # Definitions
        def_matches = len(re.findall(DEFINITION_PATTERN, text))
        if def_matches >= 1:
            score += 0.25
            signals.append(f"{def_matches} definitions")

        score = min(1.0, score)
        weight = self._scoring.weight_extractability
        return MetricScore(
            name="extractability",
            score=round(score, 4),
            weight=weight,
            weighted_score=round(score * weight, 4),
            explanation=f"Structured elements: {', '.join(signals) if signals else 'none detected'}",
        )

    def _score_qa_detection(self, text: str) -> MetricScore:
        """Metric 2: Q&A format detection (+23% citation)."""
        score = 0.0
        qa_hits = 0

        for pattern in QA_PATTERNS:
            matches = len(re.findall(pattern, text, re.MULTILINE | re.IGNORECASE))
            qa_hits += matches

        if qa_hits >= 3:
            score = 1.0
        elif qa_hits == 2:
            score = 0.7
        elif qa_hits == 1:
            score = 0.4

        weight = self._scoring.weight_qa_detection
        return MetricScore(
            name="qa_detection",
            score=round(score, 4),
            weight=weight,
            weighted_score=round(score * weight, 4),
            explanation=f"{qa_hits} Q&A pattern(s) found",
        )

    def _score_data_density(self, text: str) -> MetricScore:
        """Metric 3: Quantitative data density (+40% citation)."""
        word_count = len(text.split())
        if word_count == 0:
            weight = self._scoring.weight_data_density
            return MetricScore(name="data_density", score=0.0, weight=weight, weighted_score=0.0)

        numbers = len(re.findall(NUMBER_PATTERN, text, re.IGNORECASE))
        stats = len(re.findall(STAT_PATTERN, text, re.IGNORECASE))
        years = len(re.findall(YEAR_PATTERN, text))

        data_points = numbers + stats + years
        density = data_points / max(word_count / 50, 1)  # per 50 words

        if density >= 3:
            score = 1.0
        elif density >= 2:
            score = 0.8
        elif density >= 1:
            score = 0.5
        elif density >= 0.5:
            score = 0.3
        else:
            score = 0.1

        weight = self._scoring.weight_data_density
        return MetricScore(
            name="data_density",
            score=round(score, 4),
            weight=weight,
            weighted_score=round(score * weight, 4),
            explanation=f"{data_points} data points in {word_count} words (density: {density:.1f}/50w)",
        )

    def _score_answer_first(self, text: str) -> MetricScore:
        """Metric 4: Answer-first pattern (top factor for citation).

        Checks if the first 40-80 words contain a direct, assertive answer.
        """
        words = text.split()
        window = self._scoring.answer_first_window_words
        first_window = " ".join(words[:window])

        score = 0.0
        signals = []

        # Check for assertive openers
        assertive_patterns = [
            r"^(?:La respuesta|The answer|En resumen|In summary|S[ií]|Yes|No)\b",
            r"^[A-Z\u00c0-\u00dc][^.!?]{10,60}(?:es|is|son|are|significa|means)\b",
            r"^\d+",  # starts with a number/stat
        ]
        for pat in assertive_patterns:
            if re.search(pat, first_window, re.IGNORECASE):
                score += 0.35
                signals.append("assertive opener")
                break

        # Check if first sentence is short and declarative (< 25 words)
        first_sentence = re.split(r"[.!?]", first_window)
        if first_sentence and len(first_sentence[0].split()) <= 25:
            score += 0.35
            signals.append("concise first sentence")

        # Penalize if starts with filler/hedging
        filler_patterns = r"^(?:Bueno|Well|Es importante|It is important|Cabe mencionar|B[aá]sicamente|Basically)"
        if re.search(filler_patterns, first_window, re.IGNORECASE):
            score -= 0.3
            signals.append("filler opener (penalty)")

        score = min(1.0, max(0.0, score))
        weight = self._scoring.weight_answer_first
        return MetricScore(
            name="answer_first",
            score=round(score, 4),
            weight=weight,
            weighted_score=round(score * weight, 4),
            explanation=f"First {window}w analysis: {', '.join(signals) if signals else 'no strong pattern'}",
        )

    def _score_self_contained(self, text: str, word_count: int) -> MetricScore:
        """Metric 5: Self-contained passage (optimal 134-167 words)."""
        min_w = self._scoring.optimal_passage_min_words
        max_w = self._scoring.optimal_passage_max_words

        if min_w <= word_count <= max_w:
            length_score = 1.0
        elif word_count < min_w:
            length_score = max(0.0, word_count / min_w)
        else:
            # Gradual penalty for being too long
            excess = word_count - max_w
            length_score = max(0.0, 1.0 - (excess / 200))

        # Check for self-containment signals
        containment_score = 0.0

        # Has a topic sentence (capitalized, ends with period)
        if re.match(r"[A-Z\u00c0-\u00dc].+\.", text):
            containment_score += 0.3

        # Doesn't rely heavily on pronouns without antecedents at start
        first_words = " ".join(text.split()[:5])
        if re.match(r"^(?:(?:Esto|This|It|Eso|These|Estos)\s)", first_words, re.IGNORECASE):
            containment_score -= 0.2  # starts with pronoun = likely not self-contained

        # Contains a concluding signal
        if re.search(r"(?:por lo tanto|therefore|en conclusi[oó]n|in conclusion|as[ií] que|thus)\b", text, re.IGNORECASE):
            containment_score += 0.2

        final_score = 0.6 * length_score + 0.4 * max(0.0, min(1.0, containment_score + 0.5))
        final_score = min(1.0, max(0.0, final_score))

        weight = self._scoring.weight_self_contained
        return MetricScore(
            name="self_contained",
            score=round(final_score, 4),
            weight=weight,
            weighted_score=round(final_score * weight, 4),
            explanation=f"{word_count}w (optimal: {min_w}-{max_w}), length_score={length_score:.2f}",
        )

    def _score_eeat_signals(self, text: str) -> MetricScore:
        """Metric 6: E-E-A-T signals (+15-25% citation boost).

        Checks for author attribution, dates, sources, and expertise markers.
        """
        score = 0.0
        signals = []

        if re.search(AUTHOR_PATTERN, text, re.IGNORECASE):
            score += 0.3
            signals.append("author attribution")

        if re.search(DATE_PATTERN, text, re.IGNORECASE):
            score += 0.25
            signals.append("date reference")

        if re.search(SOURCE_PATTERN, text, re.IGNORECASE):
            score += 0.3
            signals.append("source citation")

        # Experience/expertise markers
        expertise_pattern = r"(?:en mi experiencia|in my experience|como experto|as an expert|a[nñ]os de experiencia|years of experience|certificad[oa]|certified)\b"
        if re.search(expertise_pattern, text, re.IGNORECASE):
            score += 0.15
            signals.append("expertise marker")

        score = min(1.0, score)
        weight = self._scoring.weight_eeat_signals
        return MetricScore(
            name="eeat_signals",
            score=round(score, 4),
            weight=weight,
            weighted_score=round(score * weight, 4),
            explanation=f"E-E-A-T: {', '.join(signals) if signals else 'no signals detected'}",
        )

    # -- Helpers --

    @staticmethod
    def _detect_format(text: str) -> ContentFormat:
        """Detect the primary content format of a passage."""
        if re.search(TABLE_PATTERN, text, re.IGNORECASE):
            return ContentFormat.TABLE
        if len(re.findall(LIST_PATTERN, text)) >= 2:
            return ContentFormat.LIST
        for pat in QA_PATTERNS:
            if re.search(pat, text, re.MULTILINE | re.IGNORECASE):
                return ContentFormat.QA
        if re.search(DEFINITION_PATTERN, text):
            return ContentFormat.DEFINITION
        if re.search(r"```|<code>|<pre>", text):
            return ContentFormat.CODE
        return ContentFormat.PARAGRAPH
