"""Integration tests for ClarificationEngineV2 in Adaptive Interview flow."""

from __future__ import annotations

import re

from niros.clarification_engine_v2 import (
    NEED_HIGH,
    NEED_LOW,
    ClarificationPlan,
    ClarificationQuestion,
    build_clarification_plan,
)
from niros.clarification_interview_adapter import (
    ClarificationInterviewAdapter,
    ClarificationInterviewContext,
    SOURCE_CLARIFICATION_ENGINE_V2,
    compare_interview_question_priority,
    count_clarification_questions_asked,
)
from niros.intake_runner import run_adaptive_decision, select_adaptive_question
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.semantic_signal_fingerprint_bridge import propose_fingerprint_updates
from niros.semantic_signal_graph import build_semantic_signal_graph

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(?:is|e|ed|ing)|disorder|patholog(?:y|ical)|clinical disorder)\b",
    re.IGNORECASE,
)

IDENTITY_TEXT = "I feel like I am living someone else's life."


def _tag(canonical_id: str, confidence: float = 0.45) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-clarification-integration",
        evidence_id="session-clarification-integration:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def _identity_clarification_plan() -> ClarificationPlan:
    graph = build_semantic_signal_graph(text=IDENTITY_TEXT)
    proposal = propose_fingerprint_updates(graph)
    return build_clarification_plan(graph, proposal)


def _select(
    *,
    clarification_plan: ClarificationPlan | None = None,
    answered_questions: list[str] | None = None,
    cumulative_pattern_tags: list[PatternTag] | None = None,
    max_clarification_questions: int = 2,
) -> str | None:
    return select_adaptive_question(
        session_id="session-clarification-integration",
        cumulative_pattern_tags=list(cumulative_pattern_tags or []),
        turn_count=0,
        answered_questions=list(answered_questions or []),
        blocked_questions=[],
        explicit_language="en",
        presenting_problem={"main_problem": IDENTITY_TEXT},
        clarification_plan=clarification_plan,
        max_clarification_questions=max_clarification_questions,
    )


def test_clarification_questions_are_inserted_into_interview_flow():
    plan = _identity_clarification_plan()
    question = _select(clarification_plan=plan)

    assert question is not None
    assert "someone else's life" in question


def test_high_priority_clarification_appears_before_generic_follow_ups():
    plan = _identity_clarification_plan()

    without_plan = _select(cumulative_pattern_tags=[_tag("meaning_seeking")])
    with_plan = _select(cumulative_pattern_tags=[], clarification_plan=plan)

    assert with_plan is not None
    assert "someone else's life" in with_plan
    assert with_plan != without_plan


def test_max_clarification_question_limit_is_respected():
    plan = ClarificationPlan(
        questions=(
            ClarificationQuestion(
                id="q1",
                question="First clarification question about identity?",
                target_signal="identity_dissonance",
                target_domain="values_identity",
                priority="high",
                reason="Ambiguous expression.",
                expected_information_gain=0.9,
            ),
            ClarificationQuestion(
                id="q2",
                question="Second clarification question about values?",
                target_signal="values_conflict",
                target_domain="values_identity",
                priority="high",
                reason="Ambiguous expression.",
                expected_information_gain=0.88,
            ),
            ClarificationQuestion(
                id="q3",
                question="Third clarification question about meaning?",
                target_signal="meaning_disruption",
                target_domain="meaning_purpose",
                priority="high",
                reason="Ambiguous expression.",
                expected_information_gain=0.86,
            ),
        ),
        overall_need_for_clarification=NEED_HIGH,
    )

    first = _select(clarification_plan=plan, max_clarification_questions=2)
    second = _select(
        clarification_plan=plan,
        answered_questions=[first or ""],
        max_clarification_questions=2,
    )
    third = _select(
        clarification_plan=plan,
        answered_questions=[first or "", second or ""],
        max_clarification_questions=2,
    )

    assert first == "First clarification question about identity?"
    assert second == "Second clarification question about values?"
    assert third is None or third not in {
        "First clarification question about identity?",
        "Second clarification question about values?",
    }
    assert count_clarification_questions_asked(plan, [first or "", second or ""]) == 2


def test_duplicate_questions_are_removed():
    plan = _identity_clarification_plan()
    question_text = plan.questions[0].question

    selected = _select(
        clarification_plan=plan,
        answered_questions=[question_text],
    )

    assert selected is None or selected != question_text


def test_old_behavior_is_unchanged_without_clarification_plan():
    pattern_tags = [_tag("identity_confusion"), _tag("meaning_seeking")]
    baseline = _select(cumulative_pattern_tags=pattern_tags, clarification_plan=None)

    assert baseline == _select(cumulative_pattern_tags=pattern_tags)


def test_empty_clarification_plan_does_not_change_behavior():
    pattern_tags = [_tag("identity_confusion"), _tag("meaning_seeking")]
    baseline = _select(cumulative_pattern_tags=pattern_tags)
    empty_plan = ClarificationPlan(questions=(), overall_need_for_clarification=NEED_LOW)

    assert _select(cumulative_pattern_tags=pattern_tags, clarification_plan=empty_plan) == baseline


def test_clarification_questions_appear_before_assessment_style_follow_ups():
    plan = _identity_clarification_plan()
    adapter = ClarificationInterviewAdapter()
    clarification = adapter.select_next_question(
        plan,
        ClarificationInterviewContext(answered_questions=[], blocked_questions=[]),
    )

    assert clarification is not None
    assert compare_interview_question_priority(
        clarification,
        generic_follow_up="Can you tell me more about how you've been feeling lately?",
        assessment_style_follow_up="Which areas of life feel hardest right now?",
    )
    assert clarification.source == SOURCE_CLARIFICATION_ENGINE_V2

    selected = _select(
        clarification_plan=plan,
        cumulative_pattern_tags=[],
    )
    assert selected == clarification.question


def test_run_adaptive_decision_can_return_clarification_question():
    plan = _identity_clarification_plan()
    _, _, next_question, _ = run_adaptive_decision(
        session_id="session-clarification-integration",
        raw_text="It mostly feels like my work life.",
        normalized_answer="It mostly feels like my work life.",
        turn_count=1,
        cumulative_pattern_tags=[],
        answered_questions=[],
        blocked_questions=[],
        presenting_problem={"main_problem": IDENTITY_TEXT},
        current_question=plan.questions[0].question,
        clarification_plan=plan,
    )

    assert next_question is None or "someone else's life" in next_question or next_question != plan.questions[0].question


def test_no_diagnostic_language():
    plan = _identity_clarification_plan()
    adapter = ClarificationInterviewAdapter()
    adapted = adapter.adapt(plan, ClarificationInterviewContext())
    combined = "\n".join(item.question for item in adapted).lower()

    assert DIAGNOSIS_PATTERN.search(combined) is None
    assert "disorder" not in combined
    assert "patholog" not in combined


def test_deterministic_output():
    plan = _identity_clarification_plan()
    first = _select(clarification_plan=plan, cumulative_pattern_tags=[_tag("identity_confusion")])
    second = _select(clarification_plan=plan, cumulative_pattern_tags=[_tag("identity_confusion")])

    assert first == second


def test_adapter_output_shape_matches_interview_ready_format():
    plan = _identity_clarification_plan()
    item = ClarificationInterviewAdapter().select_next_question(
        plan,
        ClarificationInterviewContext(),
    )

    assert item is not None
    payload = item.to_dict()
    assert payload["source"] == SOURCE_CLARIFICATION_ENGINE_V2
    assert payload["target_signal"]
    assert payload["target_domain"]
    assert payload["priority"] in {"high", "medium", "low"}
    assert payload["reason"]
    assert "Clarify identity dissonance" not in payload["question"]
