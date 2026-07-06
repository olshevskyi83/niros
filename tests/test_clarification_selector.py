"""Tests for clarification question selector."""

from __future__ import annotations

from niros.clarification_selector import (
    ADAPTIVE_COPING_QUESTION,
    ADAPTIVE_SELF_TALK_QUESTION,
    QUESTION_TEMPLATES,
    ClarificationQuestion,
    select_adaptive_question,
    select_next_clarification_question,
)
from niros.intake_coverage import IntakeCoverageState, evaluate_intake_coverage


def _report_for(**kwargs: bool):
    return evaluate_intake_coverage(IntakeCoverageState(**kwargs))


def test_returns_initial_statement_question_first_when_all_coverage_missing() -> None:
    question = select_next_clarification_question(_report_for())
    assert question is not None
    assert question.target_dimension == "initial_statement"
    assert question.question_text == QUESTION_TEMPLATES["initial_statement"]
    assert question.priority == 1


def test_returns_emotional_pattern_when_initial_statement_complete() -> None:
    question = select_next_clarification_question(_report_for(initial_statement=True))
    assert question is not None
    assert question.target_dimension == "emotional_pattern"
    assert question.priority == 2


def test_returns_coping_or_avoidance_when_previous_dimensions_complete() -> None:
    question = select_next_clarification_question(
        _report_for(
            initial_statement=True,
            emotional_pattern=True,
        )
    )
    assert question is not None
    assert question.target_dimension == "coping_or_avoidance"
    assert question.priority == 3


def test_returns_self_talk_when_previous_dimensions_complete() -> None:
    question = select_next_clarification_question(
        _report_for(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
        )
    )
    assert question is not None
    assert question.target_dimension == "self_talk"
    assert question.priority == 4


def test_returns_needs_when_previous_dimensions_complete() -> None:
    question = select_next_clarification_question(
        _report_for(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
        )
    )
    assert question is not None
    assert question.target_dimension == "needs"
    assert question.priority == 5


def test_returns_risks_when_previous_dimensions_complete() -> None:
    question = select_next_clarification_question(
        _report_for(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
        )
    )
    assert question is not None
    assert question.target_dimension == "risks"
    assert question.priority == 6


def test_returns_none_when_ready_for_strategy() -> None:
    question = select_next_clarification_question(
        _report_for(
            initial_statement=True,
            emotional_pattern=True,
            coping_or_avoidance=True,
            self_talk=True,
            needs=True,
            risks=True,
        )
    )
    assert question is None


def test_question_id_deterministic() -> None:
    report = _report_for(initial_statement=True)
    question = select_next_clarification_question(report)
    assert question is not None
    assert question.question_id == "clarify_emotional_pattern"


def test_priority_deterministic() -> None:
    report = _report_for(
        initial_statement=True,
        emotional_pattern=True,
        coping_or_avoidance=True,
    )
    question = select_next_clarification_question(report)
    assert question is not None
    assert question.priority == 4


def test_adaptive_self_talk_question_for_shame_self_criticism() -> None:
    report = _report_for(
        initial_statement=True,
        emotional_pattern=True,
        coping_or_avoidance=True,
    )
    question = select_adaptive_question(report, active_signals=("shame_sensitivity",))
    assert question is not None
    assert question.target_dimension == "self_talk"
    assert question.question_text == ADAPTIVE_SELF_TALK_QUESTION

    question_criticism = select_adaptive_question(
        report,
        active_signals=("harsh_self_criticism",),
    )
    assert question_criticism is not None
    assert question_criticism.question_text == ADAPTIVE_SELF_TALK_QUESTION


def test_adaptive_coping_question_for_emotional_avoidance() -> None:
    report = _report_for(initial_statement=True, emotional_pattern=True)
    question = select_adaptive_question(report, active_signals=("emotional_avoidance",))
    assert question is not None
    assert question.target_dimension == "coping_or_avoidance"
    assert question.question_text == ADAPTIVE_COPING_QUESTION


def test_default_question_used_when_no_adaptive_rule_applies() -> None:
    report = _report_for(initial_statement=True, emotional_pattern=True)
    question = select_adaptive_question(report, active_signals=())
    assert question is not None
    assert question.target_dimension == "coping_or_avoidance"
    assert question.question_text == QUESTION_TEMPLATES["coping_or_avoidance"]


def test_output_deterministic() -> None:
    report = _report_for(initial_statement=True, emotional_pattern=True)
    first = select_next_clarification_question(report)
    second = select_next_clarification_question(report)
    assert first == second
    assert isinstance(first, ClarificationQuestion)

    adaptive_first = select_adaptive_question(report, active_signals=("emotional_avoidance",))
    adaptive_second = select_adaptive_question(report, active_signals=("emotional_avoidance",))
    assert adaptive_first == adaptive_second
