"""End-to-end regression test for the Adaptive Intake Brain."""

from __future__ import annotations

from niros.intake_session_state import (
    add_user_turn,
    build_intake_transcript,
    build_person_fit_profile_from_intake,
    create_intake_session,
)


def _run_shame_case(session_id: str = "intake_case_001"):
    session = create_intake_session(session_id)

    session = add_user_turn(
        session,
        "I feel like something is wrong with me. I feel ashamed and I avoid strong emotions.",
        detected_signals=("shame_sensitivity", "emotional_avoidance"),
    )
    session = add_user_turn(
        session,
        "When this happens, I criticize myself very harshly.",
        detected_signals=("harsh_self_criticism",),
    )
    session = add_user_turn(
        session,
        "I think I need self-compassion and the ability to stay with emotions.",
        detected_needs=("self_compassion", "emotional_tolerance"),
    )
    session = add_user_turn(
        session,
        "If we go too deep too fast, I might get overwhelmed.",
        detected_signals=("overwhelm_risk",),
        detected_risk_signals=("overwhelm_risk",),
    )
    return session


def test_adaptive_intake_end_to_end_shame_case() -> None:
    session = create_intake_session("intake_case_001")

    assert session.next_question is not None
    assert session.next_question.target_dimension == "initial_statement"
    assert session.is_ready_for_strategy is False

    session = add_user_turn(
        session,
        "I feel like something is wrong with me. I feel ashamed and I avoid strong emotions.",
        detected_signals=("shame_sensitivity", "emotional_avoidance"),
    )
    assert "shame_sensitivity" in session.active_signals
    assert "emotional_avoidance" in session.active_signals
    assert session.coverage_state.initial_statement is True
    assert session.coverage_state.emotional_pattern is True
    assert session.coverage_state.coping_or_avoidance is True
    assert session.is_ready_for_strategy is False
    assert session.next_question is not None
    assert session.next_question.target_dimension != "initial_statement"
    assert session.next_question.target_dimension in {"self_talk", "needs"}

    session = add_user_turn(
        session,
        "When this happens, I criticize myself very harshly.",
        detected_signals=("harsh_self_criticism",),
    )
    assert "harsh_self_criticism" in session.active_signals
    assert session.coverage_state.self_talk is True
    assert session.is_ready_for_strategy is False
    assert session.next_question is not None
    assert session.next_question.target_dimension in {"needs", "risks"}

    session = add_user_turn(
        session,
        "I think I need self-compassion and the ability to stay with emotions.",
        detected_needs=("self_compassion", "emotional_tolerance"),
    )
    assert session.coverage_state.needs is True
    assert session.needs == ("emotional_tolerance", "self_compassion")
    assert session.is_ready_for_strategy is False
    assert session.next_question is not None
    assert session.next_question.target_dimension == "risks"

    session = add_user_turn(
        session,
        "If we go too deep too fast, I might get overwhelmed.",
        detected_signals=("overwhelm_risk",),
        detected_risk_signals=("overwhelm_risk",),
    )
    assert "overwhelm_risk" in session.risk_signals
    assert session.coverage_state.risks is True
    assert session.is_ready_for_strategy is True
    assert session.next_question is None

    profile = build_person_fit_profile_from_intake(session)
    assert profile.profile_id == session.session_id
    assert profile.active_signals == (
        "emotional_avoidance",
        "harsh_self_criticism",
        "overwhelm_risk",
        "shame_sensitivity",
    )
    assert profile.needs == ("emotional_tolerance", "self_compassion")
    assert profile.risk_signals == ("overwhelm_risk",)
    assert "self" in profile.dominant_domains
    assert "emotion_regulation" in profile.dominant_domains
    assert profile.session_phase == "preparation"

    transcript = build_intake_transcript(session)
    assert transcript == (
        "USER: I feel like something is wrong with me. I feel ashamed and I avoid strong emotions.\n"
        "USER: When this happens, I criticize myself very harshly.\n"
        "USER: I think I need self-compassion and the ability to stay with emotions.\n"
        "USER: If we go too deep too fast, I might get overwhelmed."
    )


def test_adaptive_intake_end_to_end_deterministic() -> None:
    first_session = _run_shame_case("intake_case_deterministic")
    second_session = _run_shame_case("intake_case_deterministic")

    assert first_session.active_signals == second_session.active_signals
    assert first_session.needs == second_session.needs
    assert first_session.risk_signals == second_session.risk_signals
    assert first_session.is_ready_for_strategy == second_session.is_ready_for_strategy
    assert build_intake_transcript(first_session) == build_intake_transcript(second_session)
    assert build_person_fit_profile_from_intake(first_session) == build_person_fit_profile_from_intake(
        second_session
    )
