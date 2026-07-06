"""Intake Readiness — deterministic stop condition for adaptive intake."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from niros.intake_coverage import IntakeCoverageReport, evaluate_intake_coverage

DEFAULT_MINIMUM_REQUIRED_SCORE = 0.80
MINIMUM_ACTIVE_SIGNALS = 2
MINIMUM_NEEDS = 1

READINESS_DIMENSIONS: tuple[str, ...] = (
    "emotional_pattern",
    "needs",
    "risks",
)


@dataclass(frozen=True)
class IntakeReadinessReport:
    is_ready: bool
    readiness_score: float
    reason: str
    blocking_dimensions: tuple[str, ...]
    satisfied_dimensions: tuple[str, ...]
    minimum_required_score: float = DEFAULT_MINIMUM_REQUIRED_SCORE


def _risks_satisfied(
    coverage_report: IntakeCoverageReport,
    risk_signals: tuple[str, ...],
    *,
    risks_question_answered: bool,
) -> bool:
    if coverage_report.coverage_state.risks:
        return True
    return risks_question_answered and not risk_signals


def _needs_satisfied(
    coverage_report: IntakeCoverageReport,
    needs: tuple[str, ...],
) -> bool:
    return coverage_report.coverage_state.needs and len(needs) >= MINIMUM_NEEDS


def _build_reason(
    *,
    coverage_score: float,
    active_signal_count: int,
    need_count: int,
    blocking_dimensions: tuple[str, ...],
) -> str:
    blocking = "none" if not blocking_dimensions else ",".join(blocking_dimensions)
    return (
        f"coverage={coverage_score:.4f}; "
        f"signals={active_signal_count}; "
        f"needs={need_count}; "
        f"blocking={blocking}"
    )


def evaluate_intake_readiness(
    coverage_report: IntakeCoverageReport,
    active_signals: Iterable[str] = (),
    needs: Iterable[str] = (),
    risk_signals: Iterable[str] = (),
    *,
    minimum_required_score: float = DEFAULT_MINIMUM_REQUIRED_SCORE,
    risks_question_answered: bool = False,
) -> IntakeReadinessReport:
    """Evaluate whether intake has enough information to stop and generate strategy."""
    signal_values = tuple(active_signals)
    need_values = tuple(needs)
    risk_values = tuple(risk_signals)
    coverage_score = coverage_report.coverage_score

    blocking: list[str] = []
    satisfied: list[str] = []

    if coverage_score >= minimum_required_score:
        satisfied.append("coverage_score")
    else:
        blocking.append("coverage_score")

    if coverage_report.coverage_state.emotional_pattern:
        satisfied.append("emotional_pattern")
    else:
        blocking.append("emotional_pattern")

    if _needs_satisfied(coverage_report, need_values):
        satisfied.append("needs")
    else:
        blocking.append("needs")

    if _risks_satisfied(
        coverage_report,
        risk_values,
        risks_question_answered=risks_question_answered,
    ):
        satisfied.append("risks")
    else:
        blocking.append("risks")

    if len(signal_values) >= MINIMUM_ACTIVE_SIGNALS:
        satisfied.append("active_signals")
    else:
        blocking.append("active_signals")

    is_ready = not blocking
    return IntakeReadinessReport(
        is_ready=is_ready,
        readiness_score=coverage_score,
        reason=_build_reason(
            coverage_score=coverage_score,
            active_signal_count=len(signal_values),
            need_count=len(need_values),
            blocking_dimensions=tuple(blocking),
        ),
        blocking_dimensions=tuple(blocking),
        satisfied_dimensions=tuple(satisfied),
        minimum_required_score=minimum_required_score,
    )


def _risks_question_answered(turns) -> bool:
    return any(
        turn.target_dimension == "risks" and turn.text.strip()
        for turn in turns
    )


def build_readiness_report_from_session(
    session_state,
    minimum_required_score: float = DEFAULT_MINIMUM_REQUIRED_SCORE,
) -> IntakeReadinessReport:
    """Build a readiness report from accumulated intake session state."""
    coverage_report = evaluate_intake_coverage(session_state.coverage_state)
    return evaluate_intake_readiness(
        coverage_report,
        active_signals=session_state.active_signals,
        needs=session_state.needs,
        risk_signals=session_state.risk_signals,
        minimum_required_score=minimum_required_score,
        risks_question_answered=_risks_question_answered(session_state.turns),
    )
