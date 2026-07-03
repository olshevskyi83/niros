from niros.adaptive_question_targeting import (
    extended_blocked_questions,
    is_generic_fear_panic_question,
    is_question_already_asked,
    select_intake_targeted_question,
)
from niros.evidence import statement_to_evidence
from niros.intake_runner import select_adaptive_question
from niros.models import SupportedLanguage
from niros.patterns import PatternTag, PatternTagger
from niros.statements import Statement


def _tag(canonical_id: str, confidence: float = 1.0) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-intelligence-001",
        evidence_id="session-intelligence-001:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.UKRAINIAN,
    )


def _detect(raw_text: str) -> set[str]:
    statement = Statement(
        session_id="session-intelligence-001",
        text=raw_text,
        sequence=0,
        language=SupportedLanguage.UKRAINIAN,
    )
    tags = PatternTagger().tag(statement_to_evidence(statement))
    return {tag.canonical_id for tag in tags}


def _depression_intake_context() -> dict[str, str]:
    return {
        "main_problem": "депресія і постійний низький настрій",
        "duration": "2 роки",
        "perceived_causes": "після автокатастрофи",
        "current_impact": "я майже не сплю, їсти не хочеться, не спілкуюсь з людьми",
        "previous_attempts": "пробував терапію",
        "desired_outcome": "хочу відновити сон і спокій",
    }


def test_duration_question_blocked_when_intake_duration_exists():
    presenting_problem = _depression_intake_context()
    blocked = extended_blocked_questions(
        presenting_problem=presenting_problem,
        pattern_tags=[_tag("depressed_mood_signal")],
        language="uk",
        blocked_questions=[],
    )

    assert any("Як довго" in question for question in blocked)

    question = select_adaptive_question(
        session_id="session-intelligence-duration",
        cumulative_pattern_tags=[_tag("depressed_mood_signal"), _tag("low_mood_signal")],
        turn_count=0,
        answered_questions=[],
        blocked_questions=[],
        explicit_language="uk",
        presenting_problem=presenting_problem,
    )

    assert question is not None
    assert "Як довго" not in question


def test_exact_duplicate_questions_are_not_repeated():
    presenting_problem = _depression_intake_context()
    first = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=[
            _tag("accident_context"),
            _tag("insomnia_signal"),
            _tag("social_withdrawal"),
        ],
        language="uk",
        answered_questions=[],
        blocked_questions=[],
    )
    second = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=[
            _tag("accident_context"),
            _tag("insomnia_signal"),
            _tag("social_withdrawal"),
        ],
        language="uk",
        answered_questions=[first],
        blocked_questions=[],
    )

    assert first is not None
    assert second is not None
    assert first != second
    assert is_question_already_asked(first, [first])


def test_accident_context_detects_accident_and_trauma_patterns():
    detected = _detect("після автокатастрофи")

    assert detected.intersection({"accident_context", "trauma_context_signal", "post_event_distress"})


def test_sleep_appetite_and_social_withdrawal_are_detected():
    assert _detect("я майже не сплю").intersection({"insomnia_signal", "sleep_disruption"})
    assert _detect("їсти не хочеться").intersection({"appetite_loss_signal", "depressed_mood_signal"})
    assert _detect("не спілкуюсь з людьми").intersection({"social_withdrawal", "communication_avoidance"})


def test_adaptive_question_prioritizes_accident_sleep_and_social_withdrawal():
    presenting_problem = _depression_intake_context()
    pattern_tags = [
        _tag("depressed_mood_signal"),
        _tag("accident_context"),
        _tag("insomnia_signal"),
        _tag("appetite_loss_signal"),
        _tag("social_withdrawal"),
    ]

    first = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=[],
        blocked_questions=[],
    )
    second = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=[first],
        blocked_questions=[],
    )
    third = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=[first, second],
        blocked_questions=[],
    )

    assert first is not None
    assert "автокатастроф" in first
    assert second is not None
    assert "сну" in second
    assert third is not None
    assert "спілкування" in third or "уникаєте" in third


def test_generic_panic_question_not_selected_without_fear_patterns():
    presenting_problem = _depression_intake_context()
    pattern_tags = [
        _tag("depressed_mood_signal"),
        _tag("insomnia_signal"),
        _tag("social_withdrawal"),
        _tag("emotional_distress_signal"),
    ]

    question = select_adaptive_question(
        session_id="session-intelligence-no-panic",
        cumulative_pattern_tags=pattern_tags,
        turn_count=0,
        answered_questions=[],
        blocked_questions=[],
        explicit_language="uk",
        presenting_problem=presenting_problem,
    )

    assert question is not None
    assert question != "Коли страх або паніка стають найважчими?"
    assert not is_generic_fear_panic_question(question)


def test_generic_say_more_not_selected_as_first_targeted_question():
    presenting_problem = _depression_intake_context()
    question = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=[_tag("depressed_mood_signal")],
        language="uk",
        answered_questions=[],
        blocked_questions=[],
    )

    assert question is not None
    assert "своими словами" not in question.lower()
    assert "своїми словами" not in question.lower()
