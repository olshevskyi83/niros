from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from demo_interview import (
    FIRST_QUESTION,
    run_interview_session,
)
from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.human_profile_report import build_human_profile_report_from_tags, render_human_profile_report
from niros.intake_protocol import (
    DEFAULT_INTAKE_PROTOCOL,
    DURATION_ID,
    PRESENTING_PROBLEM_ID,
    build_presenting_problem,
    intake_state_from_answers,
)
from niros.intake_runner import (
    fingerprint_presenting_problem_is_specific,
    intake_blocked_questions,
    process_intake_answer,
    run_structured_intake,
    select_adaptive_question,
)
from niros.statement_normalizer import normalize_user_input

REGRESSION_INTAKE_ANSWERS = {
    PRESENTING_PROBLEM_ID: "Я прийшов, бо боюся жити і постійно відчуваю страх.",
    DURATION_ID: "Це триває вже кілька років.",
    "perceived_causes": "Мені здається, це почалося після стресу і болю в тілі.",
    "current_impact": "Я не можу нормально працювати і спати.",
    "previous_attempts": "Я пробував терапію і медикаменти, але мені мало що допомагає.",
    "desired_outcome": "Я хочу зрозуміти себе і знайти свою пісню.",
}


def test_intake_questions_exist_in_all_languages():
    for question in DEFAULT_INTAKE_PROTOCOL.questions:
        for language in ("en", "uk", "ru", "es"):
            text = question.text_by_language[language]
            assert text.strip()
            assert "?" in text or "¿" in text


def test_first_question_is_presenting_problem_not_generic_opener():
    first = DEFAULT_INTAKE_PROTOCOL.questions[0]
    assert first.id == PRESENTING_PROBLEM_ID
    assert FIRST_QUESTION == first.text_by_language["en"]
    assert "about yourself" not in FIRST_QUESTION.lower()
    assert "головною проблемою" in first.text_by_language["uk"]


def test_intake_stores_answers_by_id():
    state = intake_state_from_answers(
        {
            PRESENTING_PROBLEM_ID: "I feel overwhelmed.",
            DURATION_ID: "About two years.",
        },
        language="en",
    )

    assert state.answers_by_question_id[PRESENTING_PROBLEM_ID] == "I feel overwhelmed."
    assert state.answers_by_question_id[DURATION_ID] == "About two years."
    assert state.completed is False


def test_intake_completes_after_all_required_questions():
    state = intake_state_from_answers(REGRESSION_INTAKE_ANSWERS, language="uk")
    assert state.completed is True
    assert len(state.answers_by_question_id) == 6


def test_report_includes_presenting_problem_section():
    presenting_problem = build_presenting_problem(intake_state_from_answers(REGRESSION_INTAKE_ANSWERS, language="uk"))
    report = build_human_profile_report_from_tags([], presenting_problem=presenting_problem)
    rendered = render_human_profile_report(report)

    assert "Presenting Problem" in rendered
    assert "Main problem:" in rendered
    assert "Duration:" in rendered
    assert "Desired outcome:" in rendered
    assert "знайти свою пісню" in rendered


def test_adaptive_interview_starts_after_intake():
    session = run_interview_session(
        intake_answers=REGRESSION_INTAKE_ANSWERS,
        user_inputs=["Мені важко довіряти людям на роботі."],
        turns=1,
        language="uk",
        print_output=False,
    )

    assert session.intake_result is not None
    assert session.intake_result.intake_state.completed is True
    assert len(session.adaptive_history) == 1
    assert session.adaptive_history[0].phase == "adaptive"


def test_adaptive_interview_does_not_repeat_presenting_problem_immediately():
    blocked = intake_blocked_questions(DEFAULT_INTAKE_PROTOCOL, "uk")
    presenting = DEFAULT_INTAKE_PROTOCOL.question_text(PRESENTING_PROBLEM_ID, "uk")
    duration = DEFAULT_INTAKE_PROTOCOL.question_text(DURATION_ID, "uk")

    intake_result = run_structured_intake(
        session_id="intake-test-session",
        answers_by_question_id=REGRESSION_INTAKE_ANSWERS,
        language="uk",
        normalize_answer=lambda text: normalize_user_input(text, mode="passthrough", provider="mock"),
    )

    first_adaptive = select_adaptive_question(
        session_id="intake-test-session",
        cumulative_pattern_tags=intake_result.cumulative_pattern_tags,
        turn_count=0,
        answered_questions=DEFAULT_INTAKE_PROTOCOL.all_question_texts("uk"),
        blocked_questions=blocked,
        explicit_language="uk",
    )

    assert first_adaptive is not None
    assert first_adaptive != presenting
    assert first_adaptive != duration
    assert "Tell me a little about yourself" not in first_adaptive


def test_ukrainian_intake_regression_patterns_and_fingerprint():
    session_id = "regression-intake-session"
    cumulative_tags = []

    for question_id, answer in REGRESSION_INTAKE_ANSWERS.items():
        tags, _store = process_intake_answer(
            question_id=question_id,
            raw_answer=answer,
            session_id=session_id,
            normalized_answer=answer,
            explicit_language="uk",
        )
        cumulative_tags.extend(tags)

    detected = {tag.canonical_id for tag in cumulative_tags}
    presenting_problem = build_presenting_problem(
        intake_state_from_answers(REGRESSION_INTAKE_ANSWERS, language="uk")
    )

    assert presenting_problem["main_problem"].startswith("Я прийшов")
    assert "existential_fear" in detected
    assert "emotional_distress_signal" in detected
    assert "sleep_disruption" in detected or "nightmare_disturbance" in detected
    assert "chronic_pain_burden" in detected or "body_sensitivity" in detected
    assert "знайти свою пісню" in presenting_problem["desired_outcome"]

    fingerprint = build_human_digital_fingerprint(
        detected_patterns=cumulative_tags,
        presenting_problem=presenting_problem,
    )
    assert fingerprint_presenting_problem_is_specific(presenting_problem)
    assert "Presenting problem:" in fingerprint["summary_text"]
    assert "знайти свою пісню" in fingerprint["summary_text"]
    assert fingerprint["summary_text"] != "No interview evidence has been collected yet."


def test_run_interview_session_prints_intake_before_adaptive():
    output = io.StringIO()
    session = run_interview_session(
        intake_answers=REGRESSION_INTAKE_ANSWERS,
        user_inputs=["Мені важко довіряти людям."],
        turns=1,
        language="uk",
        stream=output,
        print_output=True,
    )
    rendered = output.getvalue()

    assert session.intake_result is not None
    assert rendered.index("Structured Intake") < rendered.index("Adaptive Interview")
    assert "Intake Question 1:" in rendered
    assert DEFAULT_INTAKE_PROTOCOL.question_text(PRESENTING_PROBLEM_ID, "uk") in rendered
