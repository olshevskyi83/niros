"""Tests for Strategy Explanation."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import (
    NOT_RECOMMENDED,
    RECOMMENDED,
    USE_WITH_CAUTION,
    PatternFitReport,
    PatternFitScore,
)
from niros.strategy_candidate_builder import StrategyCandidate, build_strategy_candidate
from niros.strategy_explanation import (
    StrategyExplanation,
    StrategyExplanationItem,
    build_strategy_explanation,
)


def _score(
    *,
    pattern_id: str,
    canonical_name: str,
    fit_score: float,
    recommendation_status: str = RECOMMENDED,
    matched_signals: tuple[str, ...] = (),
    matched_domains: tuple[str, ...] = (),
    matched_needs: tuple[str, ...] = (),
    contraindication_hits: tuple[str, ...] = (),
    confidence: float = 0.85,
) -> PatternFitScore:
    return PatternFitScore(
        pattern_id=pattern_id,
        canonical_name=canonical_name,
        fit_score=fit_score,
        confidence=confidence,
        matched_signals=matched_signals,
        matched_domains=matched_domains,
        matched_needs=matched_needs,
        contraindication_hits=contraindication_hits,
        recommendation_status=recommendation_status,
    )


def _empty_candidate() -> StrategyCandidate:
    return build_strategy_candidate(PatternFitReport(profile_id="profile_001"))


def _mixed_candidate() -> StrategyCandidate:
    report = PatternFitReport(
        profile_id="profile_001",
        recommended_patterns=(
            _score(
                pattern_id="canonical_pattern_001",
                canonical_name="accept painful emotions",
                fit_score=0.9850,
                matched_signals=("emotional_avoidance", "shame"),
                matched_domains=("emotion_regulation",),
                matched_needs=("acceptance",),
            ),
        ),
        caution_patterns=(
            _score(
                pattern_id="canonical_pattern_002",
                canonical_name="accept with caution",
                fit_score=0.7420,
                recommendation_status=USE_WITH_CAUTION,
                matched_signals=("emotional_avoidance", "shame"),
                matched_domains=("emotion_regulation",),
                contraindication_hits=("psychosis_risk",),
            ),
        ),
        excluded_patterns=(
            _score(
                pattern_id="canonical_pattern_003",
                canonical_name="clarify personal values",
                fit_score=0.1500,
                recommendation_status=NOT_RECOMMENDED,
                confidence=0.10,
            ),
        ),
    )
    return build_strategy_candidate(report)


def test_empty_strategy_produces_empty_explanation():
    explanation = build_strategy_explanation(_empty_candidate())
    assert isinstance(explanation, StrategyExplanation)
    assert explanation.explanation_items == ()
    assert explanation.summary == "selected=0; caution=0; excluded=0"


def test_explanation_item_created():
    explanation = build_strategy_explanation(_mixed_candidate())
    assert len(explanation.explanation_items) == 3
    assert all(isinstance(item, StrategyExplanationItem) for item in explanation.explanation_items)


def test_summary_is_deterministic():
    explanation = build_strategy_explanation(_mixed_candidate())
    assert explanation.summary == "selected=1; caution=1; excluded=1"


def test_explanation_is_deterministic():
    item = build_strategy_explanation(_mixed_candidate()).explanation_items[1]
    assert item.explanation == "fit=0.7420; signals=2; domains=1; needs=0; contraindications=1"


def test_explanation_preserves_fit_score():
    item = build_strategy_explanation(_mixed_candidate()).explanation_items[0]
    assert item.fit_score == 0.9850


def test_explanation_preserves_matched_signals():
    item = build_strategy_explanation(_mixed_candidate()).explanation_items[0]
    assert item.matched_signals == ("emotional_avoidance", "shame")


def test_explanation_preserves_domains():
    item = build_strategy_explanation(_mixed_candidate()).explanation_items[0]
    assert item.matched_domains == ("emotion_regulation",)


def test_explanation_preserves_needs():
    item = build_strategy_explanation(_mixed_candidate()).explanation_items[0]
    assert item.matched_needs == ("acceptance",)


def test_explanation_preserves_contraindications():
    item = build_strategy_explanation(_mixed_candidate()).explanation_items[1]
    assert item.contraindication_hits == ("psychosis_risk",)


def test_output_is_deterministic():
    candidate = _mixed_candidate()
    first = build_strategy_explanation(candidate)
    second = build_strategy_explanation(candidate)
    assert first == second
