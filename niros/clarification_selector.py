"""Clarification Question Selector — deterministic next-question targeting for intake."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from niros.information_gain import select_highest_information_gain
from niros.intake_coverage import IntakeCoverageReport

QUESTION_STATUS_PENDING = "pending"

QUESTION_PRIORITY_ORDER: tuple[str, ...] = (
    "initial_statement",
    "emotional_pattern",
    "coping_or_avoidance",
    "self_talk",
    "needs",
    "risks",
)

QUESTION_TEMPLATES: dict[str, str] = {
    "initial_statement": "What brings you here today?",
    "emotional_pattern": (
        "What emotion or inner state feels hardest to stay with right now?"
    ),
    "coping_or_avoidance": (
        "When this happens, what do you usually do internally or externally?"
    ),
    "self_talk": "How do you usually talk to yourself in those moments?",
    "needs": (
        "What do you most need from this session: stabilization, self-compassion, "
        "clarity, emotional tolerance, or direction?"
    ),
    "risks": "Is there any risk of feeling overwhelmed if we go too deep too fast?",
}

ADAPTIVE_SELF_TALK_QUESTION = (
    "When shame or self-criticism appears, what does your inner voice usually say?"
)

ADAPTIVE_COPING_QUESTION = (
    "When difficult emotions appear, do you tend to avoid, suppress, distract, "
    "or stay with them?"
)

SELF_TALK_ADAPTIVE_SIGNALS: frozenset[str] = frozenset(
    {"shame_sensitivity", "harsh_self_criticism"}
)


@dataclass(frozen=True)
class ClarificationQuestion:
    question_id: str
    target_dimension: str
    question_text: str
    priority: int
    status: str = QUESTION_STATUS_PENDING


def _select_target_dimension(
    coverage_report: IntakeCoverageReport,
    active_signals: Iterable[str] = (),
) -> str | None:
    if coverage_report.is_ready_for_strategy:
        return None
    return select_highest_information_gain(coverage_report, active_signals=active_signals)


def _priority_for_dimension(dimension: str) -> int:
    return QUESTION_PRIORITY_ORDER.index(dimension) + 1


def _build_clarification_question(
    dimension: str,
    question_text: str,
) -> ClarificationQuestion:
    return ClarificationQuestion(
        question_id=f"clarify_{dimension}",
        target_dimension=dimension,
        question_text=question_text,
        priority=_priority_for_dimension(dimension),
    )


def _adaptive_question_text(
    dimension: str,
    active_signals: Iterable[str],
) -> str:
    active = set(active_signals)
    if dimension == "self_talk" and active.intersection(SELF_TALK_ADAPTIVE_SIGNALS):
        return ADAPTIVE_SELF_TALK_QUESTION
    if dimension == "coping_or_avoidance" and "emotional_avoidance" in active:
        return ADAPTIVE_COPING_QUESTION
    return QUESTION_TEMPLATES[dimension]


def select_next_clarification_question(
    coverage_report: IntakeCoverageReport,
) -> ClarificationQuestion | None:
    """Select the next clarification question from missing coverage dimensions."""
    dimension = _select_target_dimension(coverage_report)
    if dimension is None:
        return None
    return _build_clarification_question(dimension, QUESTION_TEMPLATES[dimension])


def select_adaptive_question(
    coverage_report: IntakeCoverageReport,
    active_signals: Iterable[str] = (),
) -> ClarificationQuestion | None:
    """Select the next clarification question with signal-aware wording when applicable."""
    dimension = _select_target_dimension(coverage_report, active_signals=active_signals)
    if dimension is None:
        return None
    question_text = _adaptive_question_text(dimension, active_signals)
    return _build_clarification_question(dimension, question_text)
