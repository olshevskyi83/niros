from niros.hypotheses import Hypothesis, HypothesisType
from niros.interview_engine import (
    BlueprintPhase,
    InterviewDecisionEngine,
)
from niros.models import InterviewPhase, InterviewState, SupportedLanguage
from niros.patterns import PatternTag


def _interview_state(
    turn_count: int = 0,
    session_id: str = "session-001",
) -> InterviewState:
    return InterviewState(
        session_id=session_id,
        state=InterviewPhase.FREE_NARRATIVE,
        turn_count=turn_count,
        input_language=SupportedLanguage.ENGLISH,
    )


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str = "tag-1",
    sequence: int = 0,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-001",
        evidence_id=f"session-001:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text="example",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def test_decision_without_patterns_continues_free_narrative():
    engine = InterviewDecisionEngine()

    decision = engine.decide(
        _interview_state(),
        [],
        [],
        BlueprintPhase.FREE_NARRATIVE,
    )

    assert decision.next_phase == BlueprintPhase.FREE_NARRATIVE
    assert decision.selected_pattern is None
    assert decision.reason == "no_patterns_continue_narrative"
    assert decision.selected_question == "Tell me what brought you here today."


def test_decision_with_one_pattern_asks_direct_follow_up():
    engine = InterviewDecisionEngine()
    tag = _pattern_tag("fear_of_rejection")

    decision = engine.decide(
        _interview_state(),
        [tag],
        [],
        BlueprintPhase.FREE_NARRATIVE,
    )

    assert decision.selected_pattern == "fear_of_rejection"
    assert decision.reason == "single_pattern_direct_follow_up"
    assert decision.selected_question == (
        "What do you usually do when you feel someone may reject you?"
    )


def test_decision_with_high_confidence_moves_to_related_pattern():
    engine = InterviewDecisionEngine()
    tag = _pattern_tag("fear_of_rejection")
    hypotheses = [
        Hypothesis(
            id="session-001:hypothesis:people_pleasing_pattern",
            session_id="session-001",
            hypothesis_type=HypothesisType.RELATIONAL_PATTERN,
            canonical_id="people_pleasing_pattern",
            supporting_pattern_ids=[tag.id],
            confidence=0.65,
            language=SupportedLanguage.ENGLISH,
        )
    ]

    decision = engine.decide(
        _interview_state(turn_count=1),
        [tag],
        hypotheses,
        BlueprintPhase.FREE_NARRATIVE,
    )

    assert decision.reason == "high_confidence_related_pattern"
    assert decision.selected_pattern == "people_pleasing"
    assert decision.selected_question == (
        "What usually happens for you when you worry someone might be upset with you?"
    )


def test_decision_advances_blueprint_phase_when_enough_evidence():
    engine = InterviewDecisionEngine()
    tags = [
        _pattern_tag("avoidance_conflict", tag_id="tag-1", sequence=0),
        _pattern_tag("fear_of_disappointing_others", tag_id="tag-2", sequence=1),
    ]
    hypotheses = [
        Hypothesis(
            id="session-001:hypothesis:people_pleasing_pattern",
            session_id="session-001",
            hypothesis_type=HypothesisType.RELATIONAL_PATTERN,
            canonical_id="people_pleasing_pattern",
            supporting_pattern_ids=[tag.id for tag in tags],
            confidence=0.65,
            language=SupportedLanguage.ENGLISH,
        )
    ]

    decision = engine.decide(
        _interview_state(turn_count=2),
        tags,
        hypotheses,
        BlueprintPhase.FREE_NARRATIVE,
    )

    assert decision.next_phase == BlueprintPhase.LIFE_STORY
    assert decision.reason == "enough_evidence_advance_blueprint"
    assert decision.selected_question == (
        "What moments from your life feel most connected to what you are going through now?"
    )
