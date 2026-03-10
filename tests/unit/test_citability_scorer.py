"""Tests for CitabilityScorer -- 6 GEO 2026 metrics."""

import pytest
from geo_seo.scoring.citability_scorer import CitabilityScorer
from geo_seo.core.config import GeoSeoConfig
from geo_seo.core.exceptions import EmptyContentError
from geo_seo.core.models import ContentFormat


@pytest.fixture
def scorer():
    """Create a scorer with default config."""
    return CitabilityScorer(GeoSeoConfig.default())


# -- Basic scoring --

class TestPassageScoring:
    """Test individual passage scoring."""

    def test_score_empty_raises(self, scorer):
        with pytest.raises(EmptyContentError):
            scorer.score_passage("")

    def test_score_too_short_raises(self, scorer):
        with pytest.raises(EmptyContentError):
            scorer.score_passage("Just five words here only.")

    def test_score_basic_paragraph(self, scorer):
        text = (
            "Python is a high-level programming language known for its readability. "
            "It was created by Guido van Rossum and first released in 1991. "
            "Python supports multiple programming paradigms including procedural, "
            "object-oriented, and functional programming approaches. "
            "The language has become one of the most popular choices for web development, "
            "data science, artificial intelligence, and automation tasks."
        )
        result = scorer.score_passage(text)
        assert 0.0 <= result.composite_score <= 1.0
        assert result.word_count > 10
        assert len(result.metrics) == 6
        assert result.content_format == ContentFormat.PARAGRAPH

    def test_score_list_content_higher_extractability(self, scorer):
        text = (
            "Benefits of Python for web development:\n"
            "- Easy to learn and readable syntax\n"
            "- Large standard library and ecosystem\n"
            "- Strong community support\n"
            "- Frameworks like Django and Flask\n"
            "- Excellent for rapid prototyping\n"
            "These factors make Python a top choice for modern web development."
        )
        result = scorer.score_passage(text)
        extractability = next(m for m in result.metrics if m.name == "extractability")
        assert extractability.score >= 0.3  # lists should boost extractability
        assert result.content_format == ContentFormat.LIST

    def test_score_qa_format(self, scorer):
        text = (
            "## What is GEO (Generative Engine Optimization)?\n\n"
            "GEO is the practice of optimizing web content so that AI language models "
            "like ChatGPT, Claude, and Perplexity are more likely to cite it in their "
            "responses. Unlike traditional SEO which focuses on search engine rankings, "
            "GEO focuses on content citability by large language models."
        )
        result = scorer.score_passage(text)
        qa_metric = next(m for m in result.metrics if m.name == "qa_detection")
        assert qa_metric.score > 0  # should detect Q&A pattern

    def test_score_data_dense_content(self, scorer):
        text = (
            "According to a 2025 study by Gartner, 65% of web traffic will come from "
            "AI-generated answers by 2026. The average CTR for traditional search results "
            "dropped 23% year-over-year. Companies investing in GEO saw a 40% increase "
            "in brand mentions across ChatGPT and Perplexity responses."
        )
        result = scorer.score_passage(text)
        data_density = next(m for m in result.metrics if m.name == "data_density")
        assert data_density.score >= 0.3  # stats and percentages should register

    def test_score_with_eeat_signals(self, scorer):
        text = (
            "According to research published by Stanford University in March 2025, "
            "structured content receives significantly more citations from LLMs. "
            "By author Dr. Maria Rodriguez, certified SEO specialist with 10 years "
            "of experience in the field of search optimization."
        )
        result = scorer.score_passage(text)
        eeat = next(m for m in result.metrics if m.name == "eeat_signals")
        assert eeat.score > 0  # should detect E-E-A-T signals

    def test_all_metrics_have_weights(self, scorer):
        text = "This is a test passage with enough words to be scored properly by the system and analyzed for citability metrics across all six dimensions."
        result = scorer.score_passage(text)
        for metric in result.metrics:
            assert metric.weight > 0
            assert metric.weighted_score == round(metric.score * metric.weight, 4)

    def test_composite_score_bounded(self, scorer):
        text = "A comprehensive analysis shows that implementing these strategies leads to measurable improvements across all key performance indicators in the digital marketing landscape according to multiple studies."
        result = scorer.score_passage(text)
        assert 0.0 <= result.composite_score <= 1.0


class TestPageScoring:
    """Test page-level scoring."""

    def test_score_page_empty_raises(self, scorer):
        with pytest.raises(EmptyContentError):
            scorer.score_page([], url="https://example.com")

    def test_score_page_basic(self, scorer):
        passages = [
            "Python is a versatile programming language used in web development, data science, and AI. It features clean syntax and a large ecosystem of libraries.",
            "Benefits of Python include easy readability, strong community, extensive libraries, cross-platform support, and rapid development capabilities for modern applications.",
            "According to the 2025 Stack Overflow survey, Python remains the most popular programming language with 65% of developers using it regularly in their projects.",
        ]
        result = scorer.score_page(passages, url="https://example.com/python")
        assert 0.0 <= result.page_score <= 1.0
        assert result.total_passages == 3
        assert len(result.top_passages) <= 10
        assert result.best_passage_score >= result.worst_passage_score

    def test_top_passages_sorted_descending(self, scorer):
        passages = [
            f"Passage number {i} contains enough words to be properly scored by the citability engine and evaluated for quality." for i in range(15)
        ]
        result = scorer.score_page(passages, url="https://test.com")
        scores = [p.composite_score for p in result.top_passages]
        assert scores == sorted(scores, reverse=True)
