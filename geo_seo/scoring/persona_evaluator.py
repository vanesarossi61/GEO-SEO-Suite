"""Multi-Persona Content Evaluator.

Evaluates content from 3 distinct user perspectives:
- Beginner: Seeks definitions, analogies, "what is X" answers
- Expert: Seeks technical data, benchmarks, statistics
- Decision-Maker: Seeks ROI, risks, recommendations, comparisons
"""

from __future__ import annotations

import re
import logging
from typing import Optional

from geo_seo.core.config import GeoSeoConfig, get_config
from geo_seo.core.models import (
    ContentFormat,
    MultiPersonaResult,
    PersonaEvaluation,
    PersonaType,
)

logger = logging.getLogger(__name__)


# -- Persona signal patterns --

BEGINNER_SIGNALS = {
    "definitions": r"(?:se define como|is defined as|significa|means|se refiere a|refers to|es decir|i\.e\.|o sea)\b",
    "analogies": r"(?:es como|is like|similar a|similar to|imagina que|imagine|por ejemplo|for example|piensa en|think of)\b",
    "explanations": r"(?:en otras palabras|in other words|esto quiere decir|this means|simplemente|simply|b[aá]sicamente|basically)\b",
    "questions": r"(?:\u00bfqu[eé] es|\u00bfc[oó]mo|what is|how does|how to|por qu[eé]|why)\b",
    "lists": r"(?:^|\n)\s*(?:\d+[.)]\s|[-*\u2022]\s)(?:Paso|Step|Primero|First)",
}

EXPERT_SIGNALS = {
    "technical_terms": r"(?:API|SDK|framework|algoritmo|algorithm|latencia|latency|throughput|benchmark|runtime|deploy)\b",
    "data_heavy": r"\b\d+(?:\.\d+)?(?:\s*%|\s*ms|\s*GB|\s*MB|\s*req/s|\s*QPS)\b",
    "comparisons": r"(?:vs\.?|versus|comparado con|compared to|frente a|outperforms|supera)\b",
    "code_refs": r"(?:```|`[^`]+`|<code>|import\s|function\s|def\s|class\s)\b",
    "methodology": r"(?:metodolog[ií]a|methodology|implementaci[oó]n|implementation|arquitectura|architecture|pipeline)\b",
}

DECISION_MAKER_SIGNALS = {
    "roi": r"(?:ROI|retorno|return on|costo-beneficio|cost-benefit|ahorro|savings|inversi[oó]n|investment)\b",
    "risks": r"(?:riesgo|risk|desventaja|disadvantage|limitaci[oó]n|limitation|caveat|trade-?off)\b",
    "recommendations": r"(?:recomendamos|we recommend|sugerimos|se sugiere|nuestra recomendaci[oó]n|best practice|mejor pr[aá]ctica)\b",
    "comparisons": r"(?:pros y contras|pros and cons|ventajas y desventajas|advantages|tabla comparativa|comparison table)\b",
    "executive": r"(?:resumen ejecutivo|executive summary|en resumen|in summary|conclusi[oó]n|bottom line|key takeaway)\b",
}


class PersonaEvaluatorEngine:
    """Evaluates content from multiple persona perspectives.

    Usage:
        evaluator = PersonaEvaluatorEngine()
        result = evaluator.evaluate("Full page content...", url="https://...")
        beginner = result.evaluations[PersonaType.BEGINNER]
    """

    def __init__(self, config: GeoSeoConfig | None = None) -> None:
        self._config = config or get_config()

    def evaluate(self, text: str, url: str = "") -> MultiPersonaResult:
        """Evaluate content from all 3 persona perspectives.

        Args:
            text: Full page content to evaluate.
            url: Source URL for tracking.

        Returns:
            MultiPersonaResult with per-persona scores and recommendations.
        """
        evaluations: dict[PersonaType, PersonaEvaluation] = {}

        for persona in PersonaType:
            evaluations[persona] = self._evaluate_persona(text, persona)

        scores = [e.composite_score for e in evaluations.values()]
        overall = sum(scores) / len(scores) if scores else 0.0
        persona_gap = max(scores) - min(scores) if scores else 0.0

        # Priority improvements: focus on weakest persona
        priority = self._prioritize_improvements(evaluations)

        return MultiPersonaResult(
            url=url,
            evaluations=evaluations,
            overall_score=round(overall, 4),
            persona_gap=round(persona_gap, 4),
            priority_improvements=priority,
        )

    def evaluate_single(self, text: str, persona: PersonaType) -> PersonaEvaluation:
        """Evaluate content from a single persona perspective.

        Args:
            text: Content to evaluate.
            persona: Which persona to evaluate as.

        Returns:
            PersonaEvaluation with scores and recommendations.
        """
        return self._evaluate_persona(text, persona)

    # -- Private evaluation methods --

    def _evaluate_persona(self, text: str, persona: PersonaType) -> PersonaEvaluation:
        """Score content for a specific persona."""
        signals = self._get_signals(persona)
        signal_counts = self._count_signals(text, signals)
        total_signals = sum(signal_counts.values())
        word_count = len(text.split())

        # Signal density (per 100 words)
        density = (total_signals / max(word_count / 100, 1)) if word_count else 0

        # Relevance: how many signal categories are covered
        categories_hit = sum(1 for v in signal_counts.values() if v > 0)
        relevance = min(1.0, categories_hit / len(signals))

        # Clarity: based on format preferences per persona
        clarity = self._score_clarity(text, persona)

        # Completeness: based on signal density
        if density >= 3:
            completeness = 1.0
        elif density >= 2:
            completeness = 0.8
        elif density >= 1:
            completeness = 0.6
        elif density >= 0.5:
            completeness = 0.4
        else:
            completeness = 0.2

        composite = 0.35 * relevance + 0.30 * clarity + 0.35 * completeness
        strengths, weaknesses, recs = self._analyze_gaps(
            signal_counts, persona, relevance, clarity, completeness
        )

        return PersonaEvaluation(
            persona=persona,
            relevance_score=round(relevance, 4),
            clarity_score=round(clarity, 4),
            completeness_score=round(completeness, 4),
            composite_score=round(composite, 4),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recs,
            preferred_formats=self._preferred_formats(persona),
        )

    @staticmethod
    def _get_signals(persona: PersonaType) -> dict[str, str]:
        """Get signal patterns for a persona."""
        mapping = {
            PersonaType.BEGINNER: BEGINNER_SIGNALS,
            PersonaType.EXPERT: EXPERT_SIGNALS,
            PersonaType.DECISION_MAKER: DECISION_MAKER_SIGNALS,
        }
        return mapping[persona]

    @staticmethod
    def _count_signals(text: str, signals: dict[str, str]) -> dict[str, int]:
        """Count occurrences of each signal pattern in text."""
        counts: dict[str, int] = {}
        for name, pattern in signals.items():
            counts[name] = len(re.findall(pattern, text, re.IGNORECASE | re.MULTILINE))
        return counts

    @staticmethod
    def _score_clarity(text: str, persona: PersonaType) -> float:
        """Score content clarity for a specific persona."""
        score = 0.5  # baseline

        if persona == PersonaType.BEGINNER:
            # Short sentences and simple structure preferred
            sentences = re.split(r"[.!?]+", text)
            avg_len = sum(len(s.split()) for s in sentences if s.strip()) / max(len(sentences), 1)
            if avg_len <= 15:
                score += 0.3
            elif avg_len <= 25:
                score += 0.15
            # Lists and step-by-step are good
            if re.findall(r"(?:^|\n)\s*\d+[.)]\s", text, re.MULTILINE):
                score += 0.2

        elif persona == PersonaType.EXPERT:
            # Technical depth and precision valued
            if re.search(r"```|<code>", text):
                score += 0.25
            if re.search(r"\b\d+\.\d+\b", text):  # precise numbers
                score += 0.15
            if re.search(r"(?:tabla|table|benchmark|spec)", text, re.IGNORECASE):
                score += 0.1

        elif persona == PersonaType.DECISION_MAKER:
            # Scannable structure with summaries
            if re.search(r"(?:^|\n)#{1,3}\s+", text):
                score += 0.15
            if re.search(r"(?:\*\*[^*]+\*\*)", text):  # bold highlights
                score += 0.1
            if re.search(r"(?:resumen|summary|conclusi[oó]n|bottom line|key takeaway)", text, re.IGNORECASE):
                score += 0.25

        return min(1.0, score)

    @staticmethod
    def _preferred_formats(persona: PersonaType) -> list[ContentFormat]:
        """Return preferred content formats for each persona."""
        mapping = {
            PersonaType.BEGINNER: [ContentFormat.LIST, ContentFormat.QA, ContentFormat.DEFINITION],
            PersonaType.EXPERT: [ContentFormat.TABLE, ContentFormat.CODE, ContentFormat.PARAGRAPH],
            PersonaType.DECISION_MAKER: [ContentFormat.TABLE, ContentFormat.LIST, ContentFormat.PARAGRAPH],
        }
        return mapping[persona]

    @staticmethod
    def _analyze_gaps(
        signal_counts: dict[str, int],
        persona: PersonaType,
        relevance: float,
        clarity: float,
        completeness: float,
    ) -> tuple[list[str], list[str], list[str]]:
        """Analyze strengths, weaknesses, and generate recommendations."""
        strengths: list[str] = []
        weaknesses: list[str] = []
        recommendations: list[str] = []

        # Identify present and missing signal categories
        present = [k for k, v in signal_counts.items() if v > 0]
        missing = [k for k, v in signal_counts.items() if v == 0]

        if present:
            strengths.append(f"Good coverage of: {', '.join(present)}")
        if missing:
            weaknesses.append(f"Missing signals for: {', '.join(missing)}")

        if relevance < 0.5:
            recommendations.append(
                f"Add more {persona.value}-oriented content signals"
            )
        if clarity < 0.5:
            recommendations.append(
                f"Improve content structure for {persona.value} readability"
            )
        if completeness < 0.5:
            recommendations.append(
                f"Increase signal density -- currently too sparse for {persona.value}"
            )

        # Persona-specific recs
        if persona == PersonaType.BEGINNER and "definitions" in missing:
            recommendations.append("Add clear definitions for technical terms")
        if persona == PersonaType.EXPERT and "data_heavy" in missing:
            recommendations.append("Include specific benchmarks, metrics, or performance data")
        if persona == PersonaType.DECISION_MAKER and "roi" in missing:
            recommendations.append("Add ROI analysis, cost-benefit comparison, or business impact data")

        return strengths, weaknesses, recommendations

    @staticmethod
    def _prioritize_improvements(
        evaluations: dict[PersonaType, PersonaEvaluation],
    ) -> list[str]:
        """Generate priority improvements focusing on weakest persona."""
        if not evaluations:
            return []

        sorted_personas = sorted(
            evaluations.items(),
            key=lambda x: x[1].composite_score,
        )

        priority: list[str] = []
        weakest_persona, weakest_eval = sorted_personas[0]

        priority.append(
            f"Priority: Improve content for {weakest_persona.value} "
            f"(score: {weakest_eval.composite_score:.2f})"
        )
        priority.extend(weakest_eval.recommendations[:3])

        return priority
