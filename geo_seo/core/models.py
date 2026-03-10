"""Pydantic models for GEO-SEO Suite scoring and analysis results.

These models define the data structures used throughout the pipeline:
- Passage-level analysis
- Page-level scoring
- Persona evaluations
- LLM validation results
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# -- Enums --

class PersonaType(str, Enum):
    """Content evaluation persona types."""
    BEGINNER = "beginner"
    EXPERT = "expert"
    DECISION_MAKER = "decision_maker"


class ContentFormat(str, Enum):
    """Detected content format of a passage."""
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    QA = "qa"
    DEFINITION = "definition"
    CODE = "code"
    HEADING = "heading"
    BLOCKQUOTE = "blockquote"


class RewriteType(str, Enum):
    """Types of suggested rewrites."""
    NARRATIVE_TO_QA = "narrative_to_qa"
    PROSE_TO_TABLE = "prose_to_table"
    SHORTEN_PASSAGE = "shorten_passage"
    ADD_DATA = "add_data"
    ADD_EEAT = "add_eeat"
    RESTRUCTURE_ANSWER_FIRST = "restructure_answer_first"


# -- Passage-level models --

class MetricScore(BaseModel):
    """Individual metric score with explanation."""
    name: str
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=1.0)
    explanation: str = ""


class RewriteSuggestion(BaseModel):
    """A suggested rewrite for a passage."""
    rewrite_type: RewriteType
    original_text: str
    suggested_text: str
    expected_improvement: float = Field(ge=0.0, le=1.0, description="Estimated score increase")
    rationale: str = ""


class PassageScore(BaseModel):
    """Scoring result for a single passage/content block."""
    passage_id: int
    text: str
    word_count: int
    content_format: ContentFormat
    metrics: list[MetricScore] = Field(default_factory=list)
    composite_score: float = Field(ge=0.0, le=1.0)
    is_citable: bool = Field(default=False, description="Score above citable threshold (0.6)")
    rewrites: list[RewriteSuggestion] = Field(default_factory=list)
    html_selector: Optional[str] = None  # CSS selector to locate in original page


# -- Page-level models --

class PageScore(BaseModel):
    """Scoring result for an entire page."""
    url: str
    title: str = ""
    fetch_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_words: int = 0
    total_passages: int = 0
    citable_passages: int = 0

    # Aggregate scores
    page_score: float = Field(ge=0.0, le=1.0, description="Avg of top-10 passage scores")
    best_passage_score: float = Field(ge=0.0, le=1.0)
    worst_passage_score: float = Field(ge=0.0, le=1.0)

    # Per-metric aggregates
    metric_averages: dict[str, float] = Field(default_factory=dict)

    # Detail
    passages: list[PassageScore] = Field(default_factory=list)
    top_passages: list[PassageScore] = Field(
        default_factory=list,
        description="Top N passages by composite score"
    )

    # Metadata
    language: str = "es"
    crawl_depth: int = 0


# -- Persona evaluation models --

class PersonaEvaluation(BaseModel):
    """Evaluation of content from a specific persona perspective."""
    persona: PersonaType
    relevance_score: float = Field(ge=0.0, le=1.0)
    clarity_score: float = Field(ge=0.0, le=1.0)
    completeness_score: float = Field(ge=0.0, le=1.0)
    composite_score: float = Field(ge=0.0, le=1.0)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    preferred_formats: list[ContentFormat] = Field(default_factory=list)


class MultiPersonaResult(BaseModel):
    """Combined multi-persona evaluation for a page."""
    url: str
    evaluations: dict[PersonaType, PersonaEvaluation] = Field(default_factory=dict)
    overall_score: float = Field(ge=0.0, le=1.0)
    persona_gap: float = Field(
        ge=0.0, le=1.0,
        description="Max difference between persona scores (lower = more balanced)"
    )
    priority_improvements: list[str] = Field(default_factory=list)


# -- LLM Validation models --

class CitationCheck(BaseModel):
    """Result of checking if a domain appears in LLM responses."""
    query: str
    provider: str  # openai | anthropic | perplexity
    response_text: str = ""
    domain_cited: bool = False
    citation_context: str = ""  # surrounding text where domain was found
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cached: bool = False


class FidelityScore(BaseModel):
    """Comparison between extracted content and LLM-generated response."""
    query: str
    original_passage: str
    llm_response: str
    semantic_similarity: float = Field(ge=0.0, le=1.0)
    factual_accuracy: float = Field(ge=0.0, le=1.0)
    attribution_present: bool = False


class LLMValidationResult(BaseModel):
    """Complete LLM validation result for a domain/page."""
    url: str
    domain: str
    queries_tested: list[str] = Field(default_factory=list)
    citation_checks: list[CitationCheck] = Field(default_factory=list)
    fidelity_scores: list[FidelityScore] = Field(default_factory=list)

    # Aggregate
    citation_rate: float = Field(ge=0.0, le=1.0, description="% of queries that cited the domain")
    avg_fidelity: float = Field(ge=0.0, le=1.0)
    theoretical_score: float = Field(ge=0.0, le=1.0, description="From citability scorer")
    real_score: float = Field(ge=0.0, le=1.0, description="From actual LLM checks")
    gap: float = Field(description="theoretical - real (positive = overestimated)")

    timestamp: datetime = Field(default_factory=datetime.utcnow)


# -- Analysis report --

class AnalysisReport(BaseModel):
    """Complete analysis report combining all results."""
    project_name: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    config_summary: dict[str, Any] = Field(default_factory=dict)

    pages: list[PageScore] = Field(default_factory=list)
    persona_results: list[MultiPersonaResult] = Field(default_factory=list)
    validation_results: list[LLMValidationResult] = Field(default_factory=list)

    # Summary stats
    total_pages: int = 0
    avg_page_score: float = Field(ge=0.0, le=1.0, default=0.0)
    total_citable_passages: int = 0
    top_recommendations: list[str] = Field(default_factory=list)
