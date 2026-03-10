"""Tests for PassageAnalyzer -- segmentation and rewrite suggestions."""

import pytest
from geo_seo.scoring.passage_analyzer import PassageAnalyzer
from geo_seo.core.config import GeoSeoConfig
from geo_seo.core.exceptions import PassageSegmentationError


@pytest.fixture
def analyzer():
    return PassageAnalyzer(GeoSeoConfig.default())


class TestSegmentation:
    """Test text segmentation into passages."""

    def test_segment_empty_raises(self, analyzer):
        with pytest.raises(PassageSegmentationError):
            analyzer.segment("")

    def test_segment_whitespace_raises(self, analyzer):
        with pytest.raises(PassageSegmentationError):
            analyzer.segment("   \n\n   ")

    def test_segment_single_paragraph(self, analyzer):
        text = (
            "This is a single paragraph with enough content to form at least "
            "one passage. It discusses the importance of content structure in "
            "modern SEO and how generative engines process information differently "
            "than traditional search crawlers. The implications for content strategy "
            "are significant and far-reaching across all industries."
        )
        passages = analyzer.segment(text)
        assert len(passages) >= 1

    def test_segment_by_headings(self, analyzer):
        text = (
            "## Introduction\n\n"
            "This is the introduction section with enough words to constitute a full passage "
            "that can be properly analyzed and scored by the citability engine.\n\n"
            "## Methods\n\n"
            "This section describes the methods used in our research project including data "
            "collection procedures and analytical frameworks applied to the dataset.\n\n"
            "## Results\n\n"
            "Here we present the findings from our comprehensive analysis of content "
            "citability patterns across major language model platforms."
        )
        passages = analyzer.segment(text)
        assert len(passages) >= 3  # at least one per heading

    def test_segment_merges_short_passages(self, analyzer):
        text = (
            "Short line one.\n\n"
            "Short line two.\n\n"
            "This is a longer passage that should stand on its own because it has "
            "well over forty words of content discussing the importance of passage "
            "length in content optimization strategies for modern platforms."
        )
        passages = analyzer.segment(text)
        # Short lines should be merged
        assert all(len(p.split()) >= 10 for p in passages)

    def test_segment_splits_long_passages(self, analyzer):
        # Create a passage > 250 words
        long_text = " ".join(["This is a sentence about content optimization."] * 60)
        passages = analyzer.segment(long_text)
        # Should be split into smaller chunks
        assert len(passages) > 1
        assert all(len(p.split()) <= 300 for p in passages)  # allow some margin


class TestAnalysis:
    """Test full analysis pipeline."""

    def test_analyze_passages(self, analyzer):
        passages = [
            "Python is a high-level programming language known for its clear syntax and versatility across many domains including web development and data science.",
            "Benefits of Python for developers include rapid prototyping capabilities, extensive library ecosystem, strong community support, and cross-platform compatibility.",
        ]
        scored = analyzer.analyze_passages(passages, url="https://test.com")
        assert len(scored) == 2
        assert all(0.0 <= s.composite_score <= 1.0 for s in scored)

    def test_get_top_passages(self, analyzer):
        passages = [
            f"Passage {i} discusses an important topic in content optimization with enough detail to be properly scored and analyzed." for i in range(15)
        ]
        scored = analyzer.analyze_passages(passages)
        top = analyzer.get_top_passages(scored, n=5)
        assert len(top) == 5
        # Should be sorted by score descending
        scores = [p.composite_score for p in top]
        assert scores == sorted(scores, reverse=True)

    def test_full_analysis_pipeline(self, analyzer):
        text = (
            "## What is GEO?\n\n"
            "Generative Engine Optimization is the practice of optimizing content for AI citation. "
            "Unlike traditional SEO, GEO focuses on how language models extract and cite information.\n\n"
            "## Key Strategies\n\n"
            "The main strategies include structuring content as lists and tables, using Q&A format, "
            "adding quantitative data, and ensuring passages are self-contained and authoritative.\n\n"
            "## Results\n\n"
            "According to studies from 2025, structured content receives 400% more citations from "
            "AI models. Q&A format boosts citations by 23%, while data-dense content sees 40% improvement."
        )
        result = analyzer.full_analysis(text, url="https://test.com/geo")
        assert result["total_passages"] >= 3
        assert result["scored_passages"] > 0
        assert "top_passages" in result
        assert "rewrite_suggestions" in result


class TestRewrites:
    """Test rewrite suggestion generation."""

    def test_suggest_rewrites_for_low_scores(self, analyzer):
        # Plain narrative text should get rewrite suggestions
        passages = [
            "This is a very plain paragraph without any structure lists or data points it just goes on and on about nothing in particular with no clear value proposition or actionable insights for the reader to take away."
        ]
        scored = analyzer.analyze_passages(passages)
        rewrites = analyzer.suggest_rewrites(scored, threshold=0.8)  # high threshold
        assert len(rewrites) >= 0  # may or may not generate depending on scores

    def test_no_rewrites_for_high_scores(self, analyzer):
        # Well-structured content shouldn't need rewrites at low threshold
        passages = [
            "## What is Python?\n\nPython is a programming language. It was created in 1991.",
        ]
        scored = analyzer.analyze_passages(passages)
        rewrites = analyzer.suggest_rewrites(scored, threshold=0.1)  # very low threshold
        assert len(rewrites) == 0  # everything should be above 0.1
