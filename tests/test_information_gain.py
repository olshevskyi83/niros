"""Tests for information gain question selection."""

from __future__ import annotations

from niros.information_gain import (
    BASE_INFORMATION_GAIN_PRIORITIES,
    InformationGainCandidate,
    calculate_information_gain_scores,
    select_highest_information_gain,
)
from niros.intake_coverage import IntakeCoverageState, evaluate_intake_coverage


def _report_for(**kwargs: bool):
    return evaluate_intake_coverage(IntakeCoverageState(**kwargs))


def _score_for_dimension(
    coverage_report,
    dimension: str,
    active_signals: tuple[str, ...] = (),
) -> InformationGainCandidate | None:
    candidates = calculate_information_gain_scores(
        coverage_report,
        active_signals=active_signals,
    )
    for candidate in candidates:
        if candidate.target_dimension == dimension:
            return candidate
    return None


def test_default_priorities() -> None:
    report = _report_for(initial_statement=True)
    candidates = calculate_information_gain_scores(report)
    scores = {candidate.target_dimension: candidate.gain_score for candidate in candidates}
    assert scores["emotional_pattern"] == BASE_INFORMATION_GAIN_PRIORITIES["emotional_pattern"] + 0.10
    assert scores["coping_or_avoidance"] == BASE_INFORMATION_GAIN_PRIORITIES["coping_or_avoidance"]
    assert scores["self_talk"] == BASE_INFORMATION_GAIN_PRIORITIES["self_talk"]
    assert scores["needs"] == BASE_INFORMATION_GAIN_PRIORITIES["needs"]
    assert scores["risks"] == BASE_INFORMATION_GAIN_PRIORITIES["risks"]


def test_shame_boosts_self_talk() -> None:
    report = _report_for(
        initial_statement=True,
        emotional_pattern=True,
        coping_or_avoidance=True,
    )
    candidate = _score_for_dimension(report, "self_talk", active_signals=("shame_sensitivity",))
    assert candidate is not None
    assert candidate.gain_score == 1.0
    assert "boosted by shame_sensitivity" in candidate.explanation


def test_avoidance_boosts_coping() -> None:
    report = _report_for(initial_statement=True, emotional_pattern=True)
    candidate = _score_for_dimension(
        report,
        "coping_or_avoidance",
        active_signals=("emotional_avoidance",),
    )
    assert candidate is not None
    assert candidate.gain_score == 1.0
    assert candidate.explanation == "boosted by emotional_avoidance"


def test_overwhelm_boosts_risks() -> None:
    report = _report_for(
        initial_statement=True,
        emotional_pattern=True,
        coping_or_avoidance=True,
        self_talk=True,
        needs=True,
    )
    candidate = _score_for_dimension(report, "risks", active_signals=("overwhelm_risk",))
    assert candidate is not None
    assert candidate.gain_score == 0.9
    assert candidate.explanation == "boosted by overwhelm_risk"


def test_completed_dimensions_ignored() -> None:
    report = _report_for(initial_statement=True, emotional_pattern=True)
    candidates = calculate_information_gain_scores(report)
    dimensions = {candidate.target_dimension for candidate in candidates}
    assert "initial_statement" not in dimensions
    assert "emotional_pattern" not in dimensions


def test_highest_score_selected() -> None:
    report = _report_for(
        initial_statement=True,
        emotional_pattern=True,
        coping_or_avoidance=True,
    )
    selected = select_highest_information_gain(
        report,
        active_signals=("shame_sensitivity",),
    )
    assert selected == "self_talk"


def test_tie_uses_priority_order() -> None:
    report = _report_for(initial_statement=True)
    selected = select_highest_information_gain(report)
    assert selected == "emotional_pattern"

    tied_report = _report_for(
        initial_statement=True,
        emotional_pattern=True,
        needs=True,
        risks=True,
    )
    tied_selected = select_highest_information_gain(tied_report)
    assert tied_selected == "coping_or_avoidance"


def test_deterministic_output() -> None:
    report = _report_for(initial_statement=True, emotional_pattern=True)
    active = ("emotional_avoidance", "shame_sensitivity")
    first = calculate_information_gain_scores(report, active_signals=active)
    second = calculate_information_gain_scores(report, active_signals=active)
    assert first == second
    assert isinstance(first[0], InformationGainCandidate)
    assert select_highest_information_gain(report, active_signals=active) == first[0].target_dimension
