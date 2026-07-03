from niros.adaptive_question_targeting import (
    collect_answered_topics,
    extended_blocked_questions,
    is_question_already_asked,
    is_topic_already_asked,
    select_intake_targeted_question,
    topic_id_for_question,
)
from niros.patterns import PatternTag
from niros.models import SupportedLanguage


def _tag(canonical_id: str, confidence: float = 1.0) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-topic-memory",
        evidence_id="session-topic-memory:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.UKRAINIAN,
    )


def _full_intake_context() -> dict[str, str]:
    return {
        "main_problem": "мені здається у мене депресія",
        "duration": "приблизно два роки",
        "perceived_causes": "наслідок автокатастрофи",
        "current_impact": "майже не сплю, їсти не хочеться, не спілкуюсь з людьми",
        "previous_attempts": "мені призначили антидепресанти, від них стало гірше",
        "desired_outcome": "хочу почуватися як до автокатастрофи",
    }


def test_same_question_not_repeated():
    presenting_problem = _full_intake_context()
    pattern_tags = [
        _tag("accident_context"),
        _tag("insomnia_signal"),
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

    assert first is not None
    assert second is not None
    assert first != second
    assert is_question_already_asked(first, [first])


def test_same_topic_not_repeated_even_from_pattern_follow_up():
    presenting_problem = _full_intake_context()
    pattern_tags = [
        _tag("accident_context"),
        _tag("trauma_context_signal"),
        _tag("insomnia_signal"),
        _tag("social_withdrawal"),
    ]

    first = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=[],
        blocked_questions=[],
    )
    assert first is not None
    assert topic_id_for_question(first) == "post_accident_changes"

    answered_topics = collect_answered_topics([first])
    assert is_topic_already_asked("post_accident_changes", answered_topics)

    second = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=[first],
        blocked_questions=[],
        answered_topics=answered_topics,
    )

    assert second is not None
    assert topic_id_for_question(second) != "post_accident_changes"
    assert "автокатастроф" not in second


def test_duration_not_asked_when_intake_duration_exists():
    presenting_problem = _full_intake_context()
    blocked = extended_blocked_questions(
        presenting_problem=presenting_problem,
        pattern_tags=[_tag("low_mood_signal")],
        language="uk",
        blocked_questions=[],
    )

    assert any("Як довго" in question for question in blocked)

    question = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=[_tag("low_mood_signal"), _tag("accident_context")],
        language="uk",
        answered_questions=[],
        blocked_questions=blocked,
    )

    assert question is not None
    assert "Як довго" not in question


def test_post_accident_question_not_repeated_after_answered():
    presenting_problem = _full_intake_context()
    pattern_tags = [
        _tag("accident_context"),
        _tag("insomnia_signal"),
        _tag("negative_medication_experience"),
        _tag("social_withdrawal"),
    ]

    accident_question = "Що змінилося у вашому стані після автокатастрофи?"
    answered = [accident_question]
    answered_topics = collect_answered_topics(answered)

    next_question = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=answered,
        blocked_questions=[],
        answered_topics=answered_topics,
    )

    assert next_question is not None
    assert "автокатастроф" not in next_question
    assert topic_id_for_question(next_question) != "post_accident_changes"


def test_treatment_history_follow_up_when_medication_negative_experience_exists():
    presenting_problem = _full_intake_context()
    pattern_tags = [
        _tag("accident_context"),
        _tag("insomnia_signal"),
        _tag("social_withdrawal"),
        _tag("negative_medication_experience"),
        _tag("medication_history"),
    ]

    answered = [
        "Що змінилося у вашому стані після автокатастрофи?",
        "Як саме порушення сну впливає на ваш день?",
        "Що відбувається всередині, коли ви уникаєте спілкування?",
    ]
    answered_topics = collect_answered_topics(answered)

    next_question = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=answered,
        blocked_questions=[],
        answered_topics=answered_topics,
    )

    assert next_question is not None
    assert topic_id_for_question(next_question) == "treatment_experience_detail"
    assert "антидепресант" in next_question or "ліки" in next_question.lower()
