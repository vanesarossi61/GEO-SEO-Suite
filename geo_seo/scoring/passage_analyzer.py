"""Passage Analyzer -- segments pages into atomic citable blocks.

Breaks down full page content into individual passages, scores each one,
identifies the top-10 most citable passages, and generates rewrite suggestions
for underperforming content.
"""

from __future__ import annotations

import re
import logging
from typing import Optional

from geo_seo.core.config import GeoSeoConfig, get_config
from geo_seo.core.exceptions import EmptyContentError, PassageSegmentationError
from geo_seo.core.models import (
    ContentFormat,
    PassageScore,
    RewriteSuggestion,
    RewriteType,
)
from geo_seo.scoring.citability_scorer import CitabilityScorer

logger = logging.getLogger(__name__)

# Segmentation boundaries
HEADING_PATTERN = r"(?:^|\n)#{1,4}\s+.+"
DOUBLE_NEWLINE = r"\n\s*\n"
HR_PATTERN = r"\n\s*(?:---|\*\*\*|___)\s*\n"


class PassageAnalyzer:
    """Segments content into passages and analyzes citability.

    Usage:
        analyzer = PassageAnalyzer()
        passages = analyzer.segment("Full page text...")
        scored = analyzer.analyze_passages(passages, url="https://...")
        top_10 = analyzer.get_top_passages(scored, n=10)
        rewrites = analyzer.suggest_rewrites(scored)
    """

    def __init__(self, config: GeoSeoConfig | None = None) -> None:
        self._config = config or get_config()
        self._scorer = CitabilityScorer(self._config)

    def segment(self, text: str) -> list[str]:
        """Segment full text into atomic passages.

        Strategy:
        1. Split on headings (##, ###, etc.)
        2. Within each section, split on double newlines
        3. Merge very short blocks with their neighbors
        4. Split very long blocks at sentence boundaries

        Args:
            text: Full extracted text content.

        Returns:
            List of passage strings.

        Raises:
            PassageSegmentationError: If segmentation produces no usable passages.
        """
        if not text or not text.strip():
            raise PassageSegmentationError("Empty text provided for segmentation")

        # Step 1: Split on headings (keep heading with its section)
        sections = re.split(r"(?=(?:^|\n)#{1,4}\s+)", text)
        sections = [s.strip() for s in sections if s.strip()]

        # Step 2: Split each section on double newlines
        raw_passages: list[str] = []
        for section in sections:
            parts = re.split(DOUBLE_NEWLINE, section)
            for part in parts:
                part = part.strip()
                if part:
                    raw_passages.append(part)

        # Step 3: Merge short passages (< 40 words) with neighbors
        merged = self._merge_short_passages(raw_passages, min_words=40)

        # Step 4: Split long passages (> 250 words) at sentence boundaries
        final: list[str] = []
        for passage in merged:
            word_count = len(passage.split())
            if word_count > 250:
                sub_passages = self._split_long_passage(passage, target_words=150)
                final.extend(sub_passages)
            else:
                final.append(passage)

        if not final:
            raise PassageSegmentationError(
                f"Segmentation produced 0 passages from {len(text)} chars"
            )

        logger.info(f"Segmented text into {len(final)} passages")
        return final

    def analyze_passages(
        self,
        passages: list[str],
        url: str = "",
    ) -> list[PassageScore]:
        """Score each passage using the CitabilityScorer.

        Args:
            passages: List of text passages.
            url: Source URL for tracking.

        Returns:
            List of PassageScore objects with full metric breakdowns.
        """
        scored: list[PassageScore] = []
        for i, text in enumerate(passages):
            try:
                score = self._scorer.score_passage(text, passage_id=i)
                scored.append(score)
            except EmptyContentError:
                logger.debug(f"Passage {i} too short, skipping")
                continue

        logger.info(
            f"Scored {len(scored)}/{len(passages)} passages for {url or 'unknown'}"
        )
        return scored

    def get_top_passages(
        self,
        scored: list[PassageScore],
        n: int | None = None,
    ) -> list[PassageScore]:
        """Return the top N passages by composite score.

        Args:
            scored: List of scored passages.
            n: Number to return (defaults to config top_passages_count).

        Returns:
            Top N PassageScore objects, sorted by score descending.
        """
        n = n or self._config.scoring.top_passages_count
        return sorted(scored, key=lambda p: p.composite_score, reverse=True)[:n]

    def suggest_rewrites(
        self,
        scored: list[PassageScore],
        threshold: float = 0.6,
    ) -> list[RewriteSuggestion]:
        """Generate rewrite suggestions for underperforming passages.

        Analyzes each passage below the threshold and suggests specific
        transformations to improve citability.

        Args:
            scored: List of scored passages.
            threshold: Score below which suggestions are generated.

        Returns:
            List of RewriteSuggestion objects with before/after text.
        """
        suggestions: list[RewriteSuggestion] = []

        for passage in scored:
            if passage.composite_score >= threshold:
                continue

            # Find weakest metric
            weakest = min(passage.metrics, key=lambda m: m.score) if passage.metrics else None
            if not weakest:
                continue

            suggestion = self._generate_rewrite(passage, weakest.name)
            if suggestion:
                suggestions.append(suggestion)

        logger.info(f"Generated {len(suggestions)} rewrite suggestions")
        return suggestions

    def full_analysis(self, text: str, url: str = "") -> dict:
        """Run complete passage analysis pipeline.

        Args:
            text: Full page text.
            url: Source URL.

        Returns:
            Dict with passages, scores, top_passages, and suggestions.
        """
        passages = self.segment(text)
        scored = self.analyze_passages(passages, url)
        top = self.get_top_passages(scored)
        rewrites = self.suggest_rewrites(scored)

        return {
            "url": url,
            "total_passages": len(passages),
            "scored_passages": len(scored),
            "citable_count": sum(1 for s in scored if s.is_citable),
            "avg_score": round(
                sum(s.composite_score for s in scored) / len(scored), 4
            ) if scored else 0.0,
            "top_passages": top,
            "all_passages": scored,
            "rewrite_suggestions": rewrites,
        }

    # -- Private helpers --

    @staticmethod
    def _merge_short_passages(passages: list[str], min_words: int = 40) -> list[str]:
        """Merge passages shorter than min_words with their neighbors."""
        if not passages:
            return []

        merged: list[str] = []
        buffer = ""

        for passage in passages:
            if buffer:
                combined = buffer + "\n\n" + passage
                if len(passage.split()) >= min_words:
                    merged.append(combined)
                    buffer = ""
                else:
                    buffer = combined
            elif len(passage.split()) < min_words:
                buffer = passage
            else:
                merged.append(passage)

        if buffer:
            if merged:
                merged[-1] = merged[-1] + "\n\n" + buffer
            else:
                merged.append(buffer)

        return merged

    @staticmethod
    def _split_long_passage(text: str, target_words: int = 150) -> list[str]:
        """Split a long passage at sentence boundaries near target word count."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: list[str] = []
        current: list[str] = []
        current_words = 0

        for sentence in sentences:
            s_words = len(sentence.split())
            if current_words + s_words > target_words and current:
                chunks.append(" ".join(current))
                current = [sentence]
                current_words = s_words
            else:
                current.append(sentence)
                current_words += s_words

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _generate_rewrite(
        self,
        passage: PassageScore,
        weakest_metric: str,
    ) -> Optional[RewriteSuggestion]:
        """Generate a specific rewrite suggestion based on the weakest metric."""
        text = passage.text

        rewrite_map = {
            "extractability": (
                RewriteType.PROSE_TO_TABLE,
                "Convert narrative text to a structured list or table for +400% citation potential.",
            ),
            "qa_detection": (
                RewriteType.NARRATIVE_TO_QA,
                "Restructure as Q&A format. Add a clear question heading followed by a direct answer.",
            ),
            "data_density": (
                RewriteType.ADD_DATA,
                "Add specific numbers, percentages, dates, or study references to increase data density.",
            ),
            "answer_first": (
                RewriteType.RESTRUCTURE_ANSWER_FIRST,
                "Move the key answer/conclusion to the first sentence. Remove filler openers.",
            ),
            "self_contained": (
                RewriteType.SHORTEN_PASSAGE,
                f"Adjust passage length to 134-167 words (currently {passage.word_count}w). Ensure it reads standalone.",
            ),
            "eeat_signals": (
                RewriteType.ADD_EEAT,
                "Add author attribution, publication date, source citations, or expertise markers.",
            ),
        }

        if weakest_metric not in rewrite_map:
            return None

        rtype, rationale = rewrite_map[weakest_metric]

        return RewriteSuggestion(
            rewrite_type=rtype,
            original_text=text[:500],  # truncate for display
            suggested_text=f"[REWRITE NEEDED: {rationale}]",
            expected_improvement=0.15,
            rationale=rationale,
        )
