"""Information Gain — deterministic next-question scoring for adaptive intake."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from niros.intake_coverage import EMOTIONAL_PATTERN_SIGNALS, IntakeCoverageReport

BASE_INFORMATION_GAIN_PRIORITIES: dict[str, float] = {
    "initial_statement": 1.00,
    "emotional_pattern": 0.95,
    "coping_or_avoidance": 0.90,
    "self_talk": 0.90,
    "needs": 0.80,
    "risks": 0.75,
}

DIMENSION_PRIORITY_ORDER: tuple[str, ...] = tuple(BASE_INFORMATION_GAIN_PRIORITIES.keys())

SHAME_SENSITIVITY_SIGNAL = "shame_sensitivity"
HARSH_SELF_CRITICISM_SIGNAL = "harsh_self_criticism"
EMOTIONAL_AVOIDANCE_SIGNAL = "emotional_avoidance"
OVERWHELM_RISK_SIGNAL = "overwhelm_risk"

SELF_TALK_BOOST = 0.10
COPING_BOOST = 0.10
RISKS_BOOST = 0.15
EMOTIONAL_PATTERN_BOOST = 0.10


@dataclass(frozen=True)
class InformationGainCandidate:
    target_dimension: str
    gain_score: float
    explanation: str


def _has_emotional_signal(active_signals: set[str]) -> bool:
    return any(signal in EMOTIONAL_PATTERN_SIGNALS for signal in active_signals)


def _priority_index(dimension: str) -> int:
    return DIMENSION_PRIORITY_ORDER.index(dimension)


def _format_explanation(boosts: tuple[str, ...]) -> str:
    if not boosts:
        return "default priority"
    return "; ".join(boosts)


def calculate_information_gain_scores(
    coverage_report: IntakeCoverageReport,
    active_signals: Iterable[str] = (),
) -> tuple[InformationGainCandidate, ...]:
    """Score missing intake dimensions by expected information gain."""
    if coverage_report.is_ready_for_strategy:
        return ()

    active = set(active_signals)
    missing_dimensions = coverage_report.missing_dimensions
    candidates: list[InformationGainCandidate] = []

    for dimension in missing_dimensions:
        gain_score = BASE_INFORMATION_GAIN_PRIORITIES[dimension]
        boosts: list[str] = []

        if dimension == "self_talk":
            if SHAME_SENSITIVITY_SIGNAL in active:
                gain_score += SELF_TALK_BOOST
                boosts.append("boosted by shame_sensitivity")
            if HARSH_SELF_CRITICISM_SIGNAL in active:
                gain_score += SELF_TALK_BOOST
                boosts.append("boosted by harsh_self_criticism")

        if dimension == "coping_or_avoidance" and EMOTIONAL_AVOIDANCE_SIGNAL in active:
            gain_score += COPING_BOOST
            boosts.append("boosted by emotional_avoidance")

        if dimension == "risks" and OVERWHELM_RISK_SIGNAL in active:
            gain_score += RISKS_BOOST
            boosts.append("boosted by overwhelm_risk")

        if (
            dimension == "emotional_pattern"
            and not _has_emotional_signal(active)
            and "initial_statement" not in missing_dimensions
        ):
            gain_score += EMOTIONAL_PATTERN_BOOST
            boosts.append("boosted by missing emotional signal")

        candidates.append(
            InformationGainCandidate(
                target_dimension=dimension,
                gain_score=round(gain_score, 4),
                explanation=_format_explanation(tuple(boosts)),
            )
        )

    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                -candidate.gain_score,
                _priority_index(candidate.target_dimension),
            ),
        )
    )


def select_highest_information_gain(
    coverage_report: IntakeCoverageReport,
    active_signals: Iterable[str] = (),
) -> str | None:
    """Return the missing dimension with the highest information gain score."""
    candidates = calculate_information_gain_scores(coverage_report, active_signals=active_signals)
    if not candidates:
        return None
    return candidates[0].target_dimension
