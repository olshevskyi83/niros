from niros.adaptive_question_targeting import (
    collect_answered_topics,
    is_question_already_asked,
    merged_used_topics,
    register_adaptive_answer,
    select_intake_targeted_question,
    topic_id_for_question,
)
from niros.models import SupportedLanguage
from niros.patterns import PatternTag


def _tag(canonical_id: str) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-dedup",
        evidence_id="session-dedup:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.UKRAINIAN,
    )


SOCIAL_WITHDRAWAL_QUESTION = "Що відбувається всередині, коли ви уникаєте спілкування?"


def test_exact_adaptive_question_is_not_repeated():
    presenting_problem = {
        "main_problem": "не спілкуюсь з людьми",
        "current_impact": "уникаю спілкування",
        "duration": "",
        "perceived_causes": "",
        "previous_attempts": "",
        "desired_outcome": "",
    }
    pattern_tags = [_tag("social_withdrawal"), _tag("communication_avoidance")]
    answered_questions: list[str] = []
    completed_topics: list[str] = []

    first = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=answered_questions,
        blocked_questions=[],
    )
    assert first == SOCIAL_WITHDRAWAL_QUESTION

    register_adaptive_answer(
        first,
        "відчуваю тривогу",
        answered_questions=answered_questions,
        completed_topics=completed_topics,
    )

    second = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=answered_questions,
        blocked_questions=[],
        completed_topics=completed_topics,
    )

    assert second is not None
    assert second != first
    assert not is_question_already_asked(first, [second])
    assert SOCIAL_WITHDRAWAL_QUESTION not in {first, second} or second != SOCIAL_WITHDRAWAL_QUESTION


def test_same_topic_not_repeated_after_answered():
    presenting_problem = {
        "main_problem": "не спілкуюсь з людьми",
        "current_impact": "уникаю спілкування",
        "duration": "",
        "perceived_causes": "",
        "previous_attempts": "",
        "desired_outcome": "",
    }
    pattern_tags = [_tag("social_withdrawal"), _tag("communication_avoidance")]
    answered_questions: list[str] = []
    completed_topics: list[str] = []

    first = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=answered_questions,
        blocked_questions=[],
    )
    register_adaptive_answer(
        first,
        "відчуваю порожнечу",
        answered_questions=answered_questions,
        completed_topics=completed_topics,
    )

    used_topics = merged_used_topics(
        answered_questions,
        collect_answered_topics(answered_questions),
        completed_topics,
    )
    assert "social_withdrawal_inner_experience" in used_topics

    second = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=answered_questions,
        blocked_questions=[],
        completed_topics=completed_topics,
    )

    assert second is not None
    assert topic_id_for_question(second) != "social_withdrawal_inner_experience"


def test_social_withdrawal_inner_question_appears_only_once_in_sequence():
    presenting_problem = {
        "main_problem": "не спілкуюсь з людьми",
        "current_impact": "уникаю спілкування",
        "duration": "",
        "perceived_causes": "",
        "previous_attempts": "",
        "desired_outcome": "",
    }
    pattern_tags = [_tag("social_withdrawal"), _tag("communication_avoidance")]
    answered_questions: list[str] = []
    completed_topics: list[str] = []
    asked: list[str] = []

    for _ in range(4):
        question = select_intake_targeted_question(
            presenting_problem=presenting_problem,
            pattern_tags=pattern_tags,
            language="uk",
            answered_questions=answered_questions,
            blocked_questions=[],
            completed_topics=completed_topics,
        )
        if question is None:
            break
        asked.append(question)
        register_adaptive_answer(
            question,
            "відповідь",
            answered_questions=answered_questions,
            completed_topics=completed_topics,
        )

    assert asked.count(SOCIAL_WITHDRAWAL_QUESTION) == 1


def test_breakup_intake_targets_breakup_not_bereavement_wording():
    presenting_problem = {
        "main_problem": "я розійшовся з партнеркою",
        "perceived_causes": "після розриву стосунків",
        "current_impact": "важко після розставання",
        "duration": "",
        "previous_attempts": "",
        "desired_outcome": "",
    }
    pattern_tags = [
        _tag("relationship_breakup_context"),
        _tag("separation_distress"),
    ]

    question = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=[],
        blocked_questions=[],
    )

    assert question is not None
    assert "втрат" not in question.lower()
    assert topic_id_for_question(question) in {
        "breakup_impact",
        "separation_distress_context",
        "self_worth_after_rejection",
    }
