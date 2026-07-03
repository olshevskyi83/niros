from niros.adaptive_question_targeting import (
    is_generic_fear_panic_question,
    select_intake_targeted_question,
)
from niros.intake_runner import select_adaptive_question
from niros.models import SupportedLanguage
from niros.patterns import PatternTag


def _tag(canonical_id: str, confidence: float = 1.0) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-targeting-001",
        evidence_id="session-targeting-001:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.UKRAINIAN,
    )


def test_sleep_presenting_problem_prioritizes_sleep_follow_up():
    presenting_problem = {
        "main_problem": "я не можу спати",
        "perceived_causes": "через смерть близької людини",
    }
    pattern_tags = [
        _tag("sleep_disruption"),
        _tag("nightmare_disturbance"),
        _tag("grief_signal"),
    ]

    question = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=[],
        blocked_questions=[],
    )

    assert question is not None
    assert "сну" in question or "заснути" in question or "прокида" in question
    assert not is_generic_fear_panic_question(question)


def test_bereavement_causes_prioritize_grief_follow_up_after_sleep():
    presenting_problem = {
        "main_problem": "я не можу спати",
        "perceived_causes": "через смерть близької людини",
    }
    pattern_tags = [
        _tag("sleep_disruption"),
        _tag("nightmare_disturbance"),
        _tag("grief_signal"),
    ]
    sleep_question = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=[],
        blocked_questions=[],
    )

    grief_question = select_intake_targeted_question(
        presenting_problem=presenting_problem,
        pattern_tags=pattern_tags,
        language="uk",
        answered_questions=[sleep_question],
        blocked_questions=[],
    )

    assert grief_question is not None
    assert "втрати" in grief_question
    assert not is_generic_fear_panic_question(grief_question)


def test_adaptive_selection_avoids_generic_panic_when_fear_not_central():
    presenting_problem = {
        "main_problem": "я не можу спати",
        "perceived_causes": "через смерть близької людини",
    }
    pattern_tags = [
        _tag("sleep_disruption"),
        _tag("nightmare_disturbance"),
        _tag("grief_signal"),
        _tag("emotional_distress_signal"),
    ]

    question = select_adaptive_question(
        session_id="session-targeting-001",
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


def test_fear_central_profile_may_use_fear_follow_up():
    presenting_problem = {
        "main_problem": "я постійно відчуваю страх і паніку",
        "perceived_causes": "",
    }
    pattern_tags = [
        _tag("panic_reactivity"),
        _tag("generalized_fear"),
    ]

    question = select_adaptive_question(
        session_id="session-targeting-fear",
        cumulative_pattern_tags=pattern_tags,
        turn_count=0,
        answered_questions=[],
        blocked_questions=[],
        explicit_language="uk",
        presenting_problem=presenting_problem,
    )

    assert question is not None
