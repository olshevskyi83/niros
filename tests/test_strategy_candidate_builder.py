"""Tests for Strategy Candidate Builder."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import (
    NOT_RECOMMENDED,
    RECOMMENDED,
    USE_WITH_CAUTION,
    PatternFitReport,
    PatternFitScore,
)
from niros.strategy_candidate_builder import (
    DEFAULT_STRATEGY_ID,
    DRAFT_STRATEGY_STATUS,
    StrategyCandidate,
    build_strategy_candidate,
)


def _score(
    *,
    pattern_id: str,
    canonical_name: str,
    fit_score: float,
    recommendation_status: str = RECOMMENDED,
    confidence: float = 0.85,
) -> PatternFitScore:
    return PatternFitScore(
        pattern_id=pattern_id,
        canonical_name=canonical_name,
        fit_score=fit_score,
        confidence=confidence,
        recommendation_status=recommendation_status,
    )


def _empty_report(*, profile_id: str = "profile_001") -> PatternFitReport:
    return PatternFitReport(profile_id=profile_id)


def _mixed_report() -> PatternFitReport:
    recommended = (
        _score(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            fit_score=0.95,
        ),
        _score(
            pattern_id="canonical_pattern_002",
            canonical_name="agency restoration",
            fit_score=0.88,
        ),
        _score(
            pattern_id="canonical_pattern_003",
            canonical_name="values clarification",
            fit_score=0.80,
        ),
    )
    caution = (
        _score(
            pattern_id="canonical_pattern_004",
            canonical_name="accept with caution",
            fit_score=0.72,
            recommendation_status=USE_WITH_CAUTION,
        ),
    )
    excluded = (
        _score(
            pattern_id="canonical_pattern_005",
            canonical_name="clarify personal values",
            fit_score=0.20,
            recommendation_status=NOT_RECOMMENDED,
            confidence=0.10,
        ),
    )
    ranked_matches = recommended + caution + excluded
    return PatternFitReport(
        profile_id="profile_001",
        ranked_matches=ranked_matches,
        recommended_patterns=recommended,
        caution_patterns=caution,
        excluded_patterns=excluded,
    )


def test_empty_report_creates_draft_strategy():
    candidate = build_strategy_candidate(_empty_report())
    assert isinstance(candidate, StrategyCandidate)
    assert candidate.selected_patterns == ()
    assert candidate.strategy_status == DRAFT_STRATEGY_STATUS


def test_profile_id_is_preserved():
    report = _empty_report(profile_id="profile_007")
    candidate = build_strategy_candidate(report)
    assert candidate.profile_id == "profile_007"


def test_selected_patterns_come_from_recommended_patterns():
    report = _mixed_report()
    candidate = build_strategy_candidate(report)
    assert candidate.selected_patterns == report.recommended_patterns


def test_selected_patterns_preserve_order():
    report = _mixed_report()
    candidate = build_strategy_candidate(report, max_patterns=2)
    assert [score.pattern_id for score in candidate.selected_patterns] == [
        "canonical_pattern_001",
        "canonical_pattern_002",
    ]


def test_max_patterns_limits_selected_patterns():
    report = _mixed_report()
    candidate = build_strategy_candidate(report, max_patterns=1)
    assert len(candidate.selected_patterns) == 1
    assert candidate.selected_patterns[0].pattern_id == "canonical_pattern_001"


def test_caution_patterns_preserved():
    report = _mixed_report()
    candidate = build_strategy_candidate(report)
    assert candidate.caution_patterns == report.caution_patterns


def test_excluded_patterns_preserved():
    report = _mixed_report()
    candidate = build_strategy_candidate(report)
    assert candidate.excluded_patterns == report.excluded_patterns


def test_strategy_status_defaults_to_draft():
    candidate = build_strategy_candidate(_mixed_report())
    assert candidate.strategy_status == DRAFT_STRATEGY_STATUS
    assert candidate.strategy_status == "draft"


def test_strategy_id_defaults_to_strategy_candidate_001():
    candidate = build_strategy_candidate(_mixed_report())
    assert candidate.strategy_id == DEFAULT_STRATEGY_ID
    assert candidate.strategy_id == "strategy_candidate_001"


def test_rationale_is_deterministic():
    candidate = build_strategy_candidate(_mixed_report())
    assert candidate.rationale == "selected=3; caution=1; excluded=1"


def test_output_is_deterministic():
    report = _mixed_report()
    first = build_strategy_candidate(report)
    second = build_strategy_candidate(report)
    assert first == second


def test_no_recommended_patterns_leaves_selected_empty():
    report = PatternFitReport(
        profile_id="profile_001",
        caution_patterns=(
            _score(
                pattern_id="canonical_pattern_004",
                canonical_name="accept with caution",
                fit_score=0.55,
                recommendation_status=USE_WITH_CAUTION,
            ),
        ),
    )
    candidate = build_strategy_candidate(report)
    assert candidate.selected_patterns == ()
    assert candidate.rationale == "selected=0; caution=1; excluded=0"
