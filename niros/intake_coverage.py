"""Intake Coverage — deterministic contracts for adaptive intake readiness."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

REQUIRED_COVERAGE_DIMENSIONS: tuple[str, ...] = (
    "initial_statement",
    "emotional_pattern",
    "coping_or_avoidance",
    "self_talk",
    "needs",
    "risks",
)

EMOTIONAL_PATTERN_SIGNALS: frozenset[str] = frozenset(
    {
        "shame_sensitivity",
        "anxiety_reactivity",
        "anxiety_sensitivity",
        "panic_reactivity",
        "existential_emptiness",
        "loss_of_meaning",
        "values_confusion",
        "identity_diffusion",
        "low_self_coherence",
        "low_mood",
        "grief_activation",
    }
)

COPING_OR_AVOIDANCE_SIGNALS: frozenset[str] = frozenset(
    {
        "emotional_avoidance",
        "people_pleasing",
        "emotional_suppression",
        "learned_helplessness",
        "behavioral_avoidance",
        "escape_coping",
        "numbing",
    }
)

SELF_TALK_SIGNALS: frozenset[str] = frozenset(
    {
        "harsh_self_criticism",
        "negative_self_talk",
        "inner_critic",
        "self_blame",
        "perfectionism_pressure",
    }
)

RISK_ACTIVE_SIGNALS: frozenset[str] = frozenset({"overwhelm_risk"})


@dataclass(frozen=True)
class IntakeCoverageState:
    initial_statement: bool = False
    emotional_pattern: bool = False
    coping_or_avoidance: bool = False
    self_talk: bool = False
    needs: bool = False
    risks: bool = False


@dataclass(frozen=True)
class IntakeCoverageReport:
    coverage_state: IntakeCoverageState
    missing_dimensions: tuple[str, ...]
    completed_dimensions: tuple[str, ...]
    is_ready_for_strategy: bool
    coverage_score: float


def evaluate_intake_coverage(coverage_state: IntakeCoverageState) -> IntakeCoverageReport:
    """Evaluate intake coverage against required strategy dimensions."""
    missing_dimensions = tuple(
        dimension
        for dimension in REQUIRED_COVERAGE_DIMENSIONS
        if not getattr(coverage_state, dimension)
    )
    completed_dimensions = tuple(
        dimension
        for dimension in REQUIRED_COVERAGE_DIMENSIONS
        if getattr(coverage_state, dimension)
    )
    total_count = len(REQUIRED_COVERAGE_DIMENSIONS)
    completed_count = len(completed_dimensions)
    coverage_score = round(completed_count / total_count, 4) if total_count else 0.0
    is_ready_for_strategy = len(missing_dimensions) == 0

    return IntakeCoverageReport(
        coverage_state=coverage_state,
        missing_dimensions=missing_dimensions,
        completed_dimensions=completed_dimensions,
        is_ready_for_strategy=is_ready_for_strategy,
        coverage_score=coverage_score,
    )


def _signal_hits(active_signals: Iterable[str], signal_group: frozenset[str]) -> bool:
    return any(signal in signal_group for signal in active_signals)


def update_coverage_from_signals(
    coverage_state: IntakeCoverageState,
    *,
    active_signals: Iterable[str] = (),
    needs: Iterable[str] = (),
    risk_signals: Iterable[str] = (),
    turn_text: str = "",
) -> IntakeCoverageState:
    """Update coverage flags from new turn signals without resetting prior progress."""
    active = tuple(active_signals)
    need_values = tuple(needs)
    risk_values = tuple(risk_signals)
    text = turn_text.strip()

    updates = {
        "initial_statement": coverage_state.initial_statement or bool(text),
        "emotional_pattern": coverage_state.emotional_pattern
        or _signal_hits(active, EMOTIONAL_PATTERN_SIGNALS),
        "coping_or_avoidance": coverage_state.coping_or_avoidance
        or _signal_hits(active, COPING_OR_AVOIDANCE_SIGNALS),
        "self_talk": coverage_state.self_talk or _signal_hits(active, SELF_TALK_SIGNALS),
        "needs": coverage_state.needs or bool(need_values),
        "risks": coverage_state.risks
        or bool(risk_values)
        or _signal_hits(active, RISK_ACTIVE_SIGNALS),
    }
    return replace(coverage_state, **updates)
