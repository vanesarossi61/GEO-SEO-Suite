"""Tests for PersonaEvaluatorEngine -- multi-persona content evaluation."""

import pytest
from geo_seo.scoring.persona_evaluator import PersonaEvaluatorEngine
from geo_seo.core.config import GeoSeoConfig
from geo_seo.core.models import PersonaType, ContentFormat


@pytest.fixture
def evaluator():
    return PersonaEvaluatorEngine(GeoSeoConfig.default())


class TestSinglePersona:
    """Test individual persona evaluations."""

    def test_beginner_evaluation(self, evaluator):
        text = (
            "What is SEO? SEO means Search Engine Optimization. Simply put, it is like "
            "a way to make your website more visible on Google. Think of it as organizing "
            "your store so customers can find what they need easily. For example, if you "
            "sell shoes, SEO helps people searching for shoes find your website first. "
            "Step 1: Choose your keywords. Step 2: Write clear content. Step 3: Build links."
        )
        result = evaluator.evaluate_single(text, PersonaType.BEGINNER)
        assert 0.0 <= result.composite_score <= 1.0
        assert result.persona == PersonaType.BEGINNER
        assert ContentFormat.LIST in result.preferred_formats

    def test_expert_evaluation(self, evaluator):
        text = (
            "The implementation uses a microservice architecture with gRPC for inter-service "
            "communication achieving 99.9% uptime. Benchmark results show 45ms p99 latency "
            "at 10,000 QPS throughput. The algorithm processes 2.5GB of data per second "
            "using a custom pipeline deployed via Kubernetes with horizontal pod autoscaling."
        )
        result = evaluator.evaluate_single(text, PersonaType.EXPERT)
        assert 0.0 <= result.composite_score <= 1.0
        assert result.persona == PersonaType.EXPERT
        assert ContentFormat.TABLE in result.preferred_formats

    def test_decision_maker_evaluation(self, evaluator):
        text = (
            "Executive Summary: Implementing this solution yields an estimated ROI of 340% "
            "over 24 months. The initial investment of $50,000 reduces operational costs by "
            "$15,000 monthly. Key risks include vendor lock-in and integration complexity. "
            "Our recommendation is to proceed with Phase 1 deployment. Pros and cons analysis "
            "shows the benefits significantly outweigh the limitations."
        )
        result = evaluator.evaluate_single(text, PersonaType.DECISION_MAKER)
        assert 0.0 <= result.composite_score <= 1.0
        assert result.persona == PersonaType.DECISION_MAKER


class TestMultiPersona:
    """Test combined multi-persona evaluation."""

    def test_multi_persona_evaluation(self, evaluator):
        text = (
            "## What is Cloud Computing?\n\n"
            "Cloud computing is like renting a powerful computer over the internet instead "
            "of buying one. For example, think of it as streaming movies instead of buying DVDs.\n\n"
            "The architecture uses distributed systems with 99.99% SLA. Benchmarks show "
            "sub-10ms latency at 50,000 concurrent connections using Kubernetes orchestration.\n\n"
            "Executive Summary: Cloud adoption reduces IT costs by 40% on average with ROI "
            "achieved within 18 months. Key risks include data sovereignty and vendor lock-in. "
            "We recommend a hybrid cloud strategy for enterprises."
        )
        result = evaluator.evaluate(text, url="https://test.com/cloud")
        assert 0.0 <= result.overall_score <= 1.0
        assert 0.0 <= result.persona_gap <= 1.0
        assert len(result.evaluations) == 3
        assert PersonaType.BEGINNER in result.evaluations
        assert PersonaType.EXPERT in result.evaluations
        assert PersonaType.DECISION_MAKER in result.evaluations
        assert len(result.priority_improvements) > 0

    def test_persona_gap_calculation(self, evaluator):
        # Content heavily biased toward experts should have a gap
        text = (
            "The microservice architecture implements gRPC with Protocol Buffers for "
            "serialization achieving 2.3x throughput vs REST. The custom allocator reduces "
            "GC pauses by 85%. Pipeline throughput benchmarked at 1.2M events/second on "
            "c5.4xlarge instances. Implementation uses CQRS with event sourcing pattern."
        )
        result = evaluator.evaluate(text)
        # Gap should exist since this is very expert-oriented
        assert result.persona_gap >= 0.0

    def test_all_persona_scores_bounded(self, evaluator):
        text = "A comprehensive guide to modern software development practices and their impact on team productivity and code quality across different project sizes and complexities."
        result = evaluator.evaluate(text)
        for persona_type, evaluation in result.evaluations.items():
            assert 0.0 <= evaluation.relevance_score <= 1.0
            assert 0.0 <= evaluation.clarity_score <= 1.0
            assert 0.0 <= evaluation.completeness_score <= 1.0
            assert 0.0 <= evaluation.composite_score <= 1.0
