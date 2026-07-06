"""Tests for intake session state."""

from __future__ import annotations

from niros.intake_readiness import build_readiness_report_from_session
from niros.intake_session_state import (
    DEFAULT_INTAKE_SESSION_ID,
    IntakeSessionState,
    IntakeTurn,
    add_user_turn,
    build_intake_transcript,
    build_person_fit_profile_from_intake,
    create_intake_session,
)


def _complete_session() -> IntakeSessionState:
    session = create_intake_session("intake_session_complete")
    session = add_user_turn(session, "I came because shame is overwhelming.")
    session = add_user_turn(
        session,
        "Shame is hardest to stay with.",
        detected_signals=("shame_sensitivity",),
    )
    session = add_user_turn(
        session,
        "I avoid and suppress feelings.",
        detected_signals=("emotional_avoidance",),
    )
    session = add_user_turn(
        session,
        "My inner critic says I am not enough.",
        detected_signals=("harsh_self_criticism",),
    )
    session = add_user_turn(
        session,
        "I need self-compassion.",
        detected_needs=("self_compassion",),
    )
    session = add_user_turn(
        session,
        "Too much too fast could overwhelm me.",
        detected_signals=("overwhelm_risk",),
        detected_risk_signals=("overwhelm_risk",),
    )
    return session


def test_create_intake_session_starts_with_initial_question() -> None:
    session = create_intake_session()
    assert session.next_question is not None
    assert session.next_question.target_dimension == "initial_statement"
    assert session.next_question.question_id == "clarify_initial_statement"


def test_new_session_not_ready_for_strategy() -> None:
    session = create_intake_session()
    assert session.is_ready_for_strategy is False


def test_add_user_turn_appends_turn() -> None:
    session = create_intake_session()
    updated = add_user_turn(session, "I need help.")
    assert len(updated.turns) == 1
    assert updated.turns[0].text == "I need help."


def test_turn_id_deterministic() -> None:
    session = create_intake_session()
    first = add_user_turn(session, "First turn.")
    second = add_user_turn(first, "Second turn.")
    assert first.turns[0].turn_id == "user_turn_001"
    assert second.turns[1].turn_id == "user_turn_002"


def test_target_dimension_copied_from_current_next_question() -> None:
    session = create_intake_session()
    updated = add_user_turn(session, "I feel stuck.")
    assert updated.turns[0].target_dimension == "initial_statement"


def test_signals_accumulate_uniquely() -> None:
    session = create_intake_session()
    updated = add_user_turn(
        session,
        "Shame and criticism.",
        detected_signals=("shame_sensitivity", "harsh_self_criticism"),
    )
    again = add_user_turn(
        updated,
        "More shame.",
        detected_signals=("shame_sensitivity", "emotional_avoidance"),
    )
    assert again.active_signals == (
        "emotional_avoidance",
        "harsh_self_criticism",
        "shame_sensitivity",
    )


def test_needs_accumulate_uniquely() -> None:
    session = create_intake_session()
    updated = add_user_turn(session, "Need one.", detected_needs=("self_compassion",))
    again = add_user_turn(
        updated,
        "Need two.",
        detected_needs=("self_compassion", "emotional_tolerance"),
    )
    assert again.needs == ("emotional_tolerance", "self_compassion")


def test_risk_signals_accumulate_uniquely() -> None:
    session = create_intake_session()
    updated = add_user_turn(
        session,
        "Risk one.",
        detected_risk_signals=("overwhelm_risk",),
    )
    again = add_user_turn(
        updated,
        "Risk two.",
        detected_risk_signals=("overwhelm_risk", "panic_reactivity"),
    )
    assert again.risk_signals == ("overwhelm_risk", "panic_reactivity")


def test_coverage_updates_after_user_turn() -> None:
    session = create_intake_session()
    updated = add_user_turn(session, "I came because I feel ashamed.")
    assert updated.coverage_state.initial_statement is True


def test_next_question_advances_after_coverage_update() -> None:
    session = create_intake_session()
    updated = add_user_turn(session, "I came because I feel ashamed.")
    assert updated.next_question is not None
    assert updated.next_question.target_dimension == "emotional_pattern"


def test_ready_session_sets_next_question_none() -> None:
    session = _complete_session()
    assert session.is_ready_for_strategy is True
    assert session.next_question is None


def test_session_readiness_matches_readiness_report() -> None:
    session = _complete_session()
    report = build_readiness_report_from_session(session)
    assert report.is_ready is True
    assert session.is_ready_for_strategy == report.is_ready


def test_transcript_preserves_turn_order() -> None:
    session = create_intake_session()
    session = add_user_turn(session, "First.")
    session = add_user_turn(session, "Second.")
    assert build_intake_transcript(session) == "USER: First.\nUSER: Second."


def test_profile_built_from_intake_preserves_session_profile_id() -> None:
    session = _complete_session()
    profile = build_person_fit_profile_from_intake(session)
    assert profile.profile_id == "intake_session_complete"

    explicit = build_person_fit_profile_from_intake(session, profile_id="custom_profile")
    assert explicit.profile_id == "custom_profile"


def test_profile_active_signals_from_accumulated_signals() -> None:
    session = _complete_session()
    profile = build_person_fit_profile_from_intake(session)
    assert "shame_sensitivity" in profile.active_signals
    assert "harsh_self_criticism" in profile.active_signals
    assert "emotional_avoidance" in profile.active_signals


def test_profile_needs_from_accumulated_needs() -> None:
    session = _complete_session()
    profile = build_person_fit_profile_from_intake(session)
    assert profile.needs == ("self_compassion",)


def test_profile_risk_signals_from_accumulated_risk_signals() -> None:
    session = _complete_session()
    profile = build_person_fit_profile_from_intake(session)
    assert profile.risk_signals == ("overwhelm_risk",)


def test_profile_domains_inferred_from_signals() -> None:
    session = _complete_session()
    profile = build_person_fit_profile_from_intake(session)
    assert profile.dominant_domains == ("self", "emotion_regulation")


def test_output_deterministic() -> None:
    first = create_intake_session(DEFAULT_INTAKE_SESSION_ID)
    second = create_intake_session(DEFAULT_INTAKE_SESSION_ID)
    assert first == second

    updated_once = add_user_turn(first, "Hello.", detected_signals=("shame_sensitivity",))
    updated_twice = add_user_turn(second, "Hello.", detected_signals=("shame_sensitivity",))
    assert updated_once == updated_twice
    assert isinstance(updated_once.turns[0], IntakeTurn)
    assert isinstance(updated_once, IntakeSessionState)

    profile_once = build_person_fit_profile_from_intake(updated_once)
    profile_twice = build_person_fit_profile_from_intake(updated_twice)
    assert profile_once == profile_twice
