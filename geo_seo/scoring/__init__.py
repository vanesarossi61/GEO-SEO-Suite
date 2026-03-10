"""Scoring engine for GEO-SEO Suite.

Provides the core scoring, analysis, and validation tools:
- CitabilityScorer: 6 evidence-based GEO 2026 metrics
- PassageAnalyzer: Passage segmentation and top-10 identification
- PersonaEvaluatorEngine: Multi-persona content evaluation
- LLMValidator: Real LLM citation validation
"""

from geo_seo.scoring.citability_scorer import CitabilityScorer
from geo_seo.scoring.passage_analyzer import PassageAnalyzer
from geo_seo.scoring.persona_evaluator import PersonaEvaluatorEngine
from geo_seo.scoring.llm_validator import LLMValidator

__all__ = [
    "CitabilityScorer",
    "PassageAnalyzer",
    "PersonaEvaluatorEngine",
    "LLMValidator",
]
