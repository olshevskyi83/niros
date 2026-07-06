"""Tests for intake coverage contracts."""

from __future__ import annotations

from niros.intake_coverage import (
    REQUIRED_COVERAGE_DIMENSIONS,
    IntakeCoverageReport,
    IntakeCoverageState,
    evaluate_intake_coverage,
    update_coverage_from_signals,
)


def _complete_state() -> IntakeCoverageState:
    return IntakeCoverageState(
        initial_statement=True,
        emotional_pattern=True,
        coping_or_avoidance=True,
        self_talk=True,
        needs=True,
        risks=True,
    )


def test_default_coverage_state_all_false() -> None:
    state = IntakeCoverageState()
    assert state.initial_statement is False
    assert state.emotional_pattern is False
    assert state.coping_or_avoidance is False
    assert state.self_talk is False
    assert state.needs is False
    assert state.risks is False


def test_empty_state_not_ready() -> None:
    report = evaluate_intake_coverage(IntakeCoverageState())
    assert report.is_ready_for_strategy is False


def test_all_true_state_ready() -> None:
    report = evaluate_intake_coverage(_complete_state())
    assert report.is_ready_for_strategy is True
    assert report.missing_dimensions == ()


def test_missing_dimensions_correct() -> None:
    state = IntakeCoverageState(initial_statement=True, needs=True)
    report = evaluate_intake_coverage(state)
    assert report.missing_dimensions == (
        "emotional_pattern",
        "coping_or_avoidance",
        "self_talk",
        "risks",
    )


def test_completed_dimensions_correct() -> None:
    state = IntakeCoverageState(initial_statement=True, needs=True)
    report = evaluate_intake_coverage(state)
    assert report.completed_dimensions == ("initial_statement", "needs")


def test_coverage_score_correct() -> None:
    state = IntakeCoverageState(initial_statement=True, needs=True)
    report = evaluate_intake_coverage(state)
    assert report.coverage_score == round(2 / len(REQUIRED_COVERAGE_DIMENSIONS), 4)

    complete_report = evaluate_intake_coverage(_complete_state())
    assert complete_report.coverage_score == 1.0


def test_turn_text_sets_initial_statement() -> None:
    updated = update_coverage_from_signals(
        IntakeCoverageState(),
        turn_text="I need help with shame.",
    )
    assert updated.initial_statement is True


def test_shame_signal_sets_emotional_pattern() -> None:
    updated = update_coverage_from_signals(
        IntakeCoverageState(),
        active_signals=("shame_sensitivity",),
    )
    assert updated.emotional_pattern is True


def test_emotional_avoidance_sets_coping_or_avoidance() -> None:
    updated = update_coverage_from_signals(
        IntakeCoverageState(),
        active_signals=("emotional_avoidance",),
    )
    assert updated.coping_or_avoidance is True


def test_harsh_self_criticism_sets_self_talk() -> None:
    updated = update_coverage_from_signals(
        IntakeCoverageState(),
        active_signals=("harsh_self_criticism",),
    )
    assert updated.self_talk is True


def test_needs_set_needs_coverage() -> None:
    updated = update_coverage_from_signals(
        IntakeCoverageState(),
        needs=("self_compassion",),
    )
    assert updated.needs is True


def test_risk_signals_set_risks_coverage() -> None:
    updated = update_coverage_from_signals(
        IntakeCoverageState(),
        risk_signals=("overwhelm_risk",),
    )
    assert updated.risks is True


def test_overwhelm_risk_sets_risks_coverage() -> None:
    updated = update_coverage_from_signals(
        IntakeCoverageState(),
        active_signals=("overwhelm_risk",),
    )
    assert updated.risks is True


def test_update_preserves_previous_true_values() -> None:
    state = IntakeCoverageState(initial_statement=True, emotional_pattern=True)
    updated = update_coverage_from_signals(
        state,
        active_signals=(),
        needs=(),
        risk_signals=(),
        turn_text="",
    )
    assert updated.initial_statement is True
    assert updated.emotional_pattern is True


def test_output_deterministic() -> None:
    state = IntakeCoverageState(initial_statement=True)
    first = evaluate_intake_coverage(state)
    second = evaluate_intake_coverage(state)
    assert first == second
    assert isinstance(first, IntakeCoverageReport)

    updated_once = update_coverage_from_signals(
        state,
        active_signals=("shame_sensitivity",),
        needs=("self_compassion",),
    )
    updated_twice = update_coverage_from_signals(
        state,
        active_signals=("shame_sensitivity",),
        needs=("self_compassion",),
    )
    assert updated_once == updated_twice
