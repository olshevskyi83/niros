"""Tests for intake readiness stop conditions."""

from __future__ import annotations

from niros.intake_coverage import IntakeCoverageState, evaluate_intake_coverage
from niros.intake_readiness import (
    DEFAULT_MINIMUM_REQUIRED_SCORE,
    IntakeReadinessReport,
    build_readiness_report_from_session,
    evaluate_intake_readiness,
)
from niros.intake_session_state import add_user_turn, create_intake_session


def _coverage_report(**kwargs: bool):
    return evaluate_intake_coverage(IntakeCoverageState(**kwargs))


def test_not_ready_when_coverage_low() -> None:
    report = evaluate_intake_readiness(_coverage_report(initial_statement=True))
    assert report.is_ready is False
    assert "coverage_score" in report.blocking_dimensions


def test_not_ready_when_emotional_pattern_missing() -> None:
    report = evaluate_intake_readiness(
        _coverage_report(
            initial_statement=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
            risks=True,
        ),
        active_signals=("shame_sensitivity", "emotional_avoidance"),
        needs=("self_compassion",),
        risk_signals=("overwhelm_risk",),
    )
    assert report.is_ready is False
    assert "emotional_pattern" in report.blocking_dimensions


def test_not_ready_when_needs_missing() -> None:
    report = evaluate_intake_readiness(
        _coverage_report(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            risks=True,
        ),
        active_signals=("shame_sensitivity", "emotional_avoidance"),
        needs=(),
        risk_signals=("overwhelm_risk",),
    )
    assert report.is_ready is False
    assert "needs" in report.blocking_dimensions


def test_not_ready_when_risks_missing() -> None:
    report = evaluate_intake_readiness(
        _coverage_report(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
        ),
        active_signals=("shame_sensitivity", "emotional_avoidance"),
        needs=("self_compassion",),
        risk_signals=(),
        risks_question_answered=False,
    )
    assert report.is_ready is False
    assert "risks" in report.blocking_dimensions


def test_not_ready_with_fewer_than_two_active_signals() -> None:
    report = evaluate_intake_readiness(
        _coverage_report(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
            risks=True,
        ),
        active_signals=("shame_sensitivity",),
        needs=("self_compassion",),
        risk_signals=("overwhelm_risk",),
    )
    assert report.is_ready is False
    assert "active_signals" in report.blocking_dimensions


def test_not_ready_with_no_needs() -> None:
    report = evaluate_intake_readiness(
        _coverage_report(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
            risks=True,
        ),
        active_signals=("shame_sensitivity", "emotional_avoidance"),
        needs=(),
        risk_signals=("overwhelm_risk",),
    )
    assert report.is_ready is False
    assert "needs" in report.blocking_dimensions


def test_ready_when_requirements_met() -> None:
    report = evaluate_intake_readiness(
        _coverage_report(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
            risks=True,
        ),
        active_signals=("shame_sensitivity", "emotional_avoidance"),
        needs=("self_compassion",),
        risk_signals=("overwhelm_risk",),
    )
    assert report.is_ready is True
    assert report.blocking_dimensions == ()
    assert report.readiness_score == 1.0


def test_risks_ready_with_empty_risk_signals_when_question_answered() -> None:
    report = evaluate_intake_readiness(
        _coverage_report(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
        ),
        active_signals=("shame_sensitivity", "emotional_avoidance"),
        needs=("self_compassion",),
        risk_signals=(),
        risks_question_answered=True,
    )
    assert "risks" in report.satisfied_dimensions
    assert "risks" not in report.blocking_dimensions


def test_blocking_dimensions_deterministic() -> None:
    report = evaluate_intake_readiness(_coverage_report())
    assert report.blocking_dimensions == (
        "coverage_score",
        "emotional_pattern",
        "needs",
        "risks",
        "active_signals",
    )


def test_satisfied_dimensions_deterministic() -> None:
    report = evaluate_intake_readiness(
        _coverage_report(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
            risks=True,
        ),
        active_signals=("shame_sensitivity", "emotional_avoidance"),
        needs=("self_compassion",),
        risk_signals=("overwhelm_risk",),
    )
    assert report.satisfied_dimensions == (
        "coverage_score",
        "emotional_pattern",
        "needs",
        "risks",
        "active_signals",
    )


def test_reason_deterministic() -> None:
    report = evaluate_intake_readiness(_coverage_report(initial_statement=True))
    assert (
        report.reason
        == "coverage=0.1667; signals=0; needs=0; blocking=coverage_score,emotional_pattern,needs,risks,active_signals"
    )

    ready = evaluate_intake_readiness(
        _coverage_report(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
            risks=True,
        ),
        active_signals=("shame_sensitivity", "emotional_avoidance"),
        needs=("self_compassion",),
        risk_signals=("overwhelm_risk",),
    )
    assert ready.reason == "coverage=1.0000; signals=2; needs=1; blocking=none"


def test_build_readiness_report_from_session_works() -> None:
    session = create_intake_session("readiness_session")
    session = add_user_turn(session, "I feel ashamed and avoid feelings.")
    report = build_readiness_report_from_session(session)
    assert isinstance(report, IntakeReadinessReport)
    assert report.is_ready is False
    assert report.minimum_required_score == DEFAULT_MINIMUM_REQUIRED_SCORE


def test_session_state_readiness_uses_readiness_report() -> None:
    session = create_intake_session()
    session = add_user_turn(
        session,
        "Initial statement about shame.",
        detected_signals=("shame_sensitivity",),
    )
    assert session.is_ready_for_strategy is False
    assert session.next_question is not None

    report = build_readiness_report_from_session(session)
    assert report.is_ready is False
    assert session.is_ready_for_strategy == report.is_ready
