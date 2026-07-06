"""Tests for guided assessment mapping."""

from __future__ import annotations

from niros.guided_assessment import (
    GuidedAssessmentAnswers,
    all_required_answers_collected,
    build_profile_from_answers,
    build_transcript,
    combined_answer_text,
)


def _full_answers(**overrides: str) -> GuidedAssessmentAnswers:
    base = {
        "initial_statement": "I feel stuck and ashamed lately.",
        "q_difficult": "My inner critic is loud.",
        "q_coping": "I avoid feeling sadness.",
        "q_emotion": "Shame is hardest to stay with.",
        "q_self_talk": "I tell myself I am not enough.",
        "q_need": "I need self-compassion and emotional tolerance.",
        "q_risk": "Yes, too much too fast could overwhelm me.",
    }
    base.update(overrides)
    return GuidedAssessmentAnswers.from_dict(base)


def test_shame_answer_maps_shame_sensitivity() -> None:
    answers = _full_answers(initial_statement="I feel deep shame about this.")
    result = build_profile_from_answers(answers)
    assert result.profile is not None
    assert "shame_sensitivity" in result.profile.active_signals


def test_self_criticism_answer_maps_harsh_self_criticism() -> None:
    answers = _full_answers(q_self_talk="My inner critic says I failed again.")
    result = build_profile_from_answers(answers)
    assert result.profile is not None
    assert "harsh_self_criticism" in result.profile.active_signals


def test_avoidance_answer_maps_emotional_avoidance() -> None:
    answers = _full_answers(q_coping="I avoid feeling anything and escape into work.")
    result = build_profile_from_answers(answers)
    assert result.profile is not None
    assert "emotional_avoidance" in result.profile.active_signals


def test_overwhelm_answer_maps_risk_signals() -> None:
    answers = _full_answers(q_risk="It feels like too much and could overwhelm me.")
    result = build_profile_from_answers(answers)
    assert result.profile is not None
    assert "overwhelm_risk" in result.profile.active_signals
    assert "overwhelm_risk" in result.profile.risk_signals


def test_need_self_compassion_maps_need() -> None:
    answers = _full_answers(
        initial_statement="Something is wrong.",
        q_need="I need self-compassion most.",
    )
    result = build_profile_from_answers(answers)
    assert result.profile is not None
    assert "self_compassion" in result.profile.needs


def test_empty_vague_answers_produce_insufficient_coverage() -> None:
    answers = GuidedAssessmentAnswers(
        initial_statement="I feel bad.",
        q_difficult="Things are hard.",
        q_coping="I keep going.",
        q_emotion="Sadness.",
        q_self_talk="I try to stay strong.",
        q_need="Clarity.",
        q_risk="Maybe.",
    )
    result = build_profile_from_answers(answers)
    assert result.insufficient_coverage is True
    assert result.profile is None


def test_transcript_builder_includes_questions_and_answers() -> None:
    answers = _full_answers(initial_statement="Shame is here.")
    transcript = build_transcript(answers, "en")
    assert "Question: What brings you here today?" in transcript
    assert "Answer: Shame is here." in transcript
    assert "Question: What emotion is hardest to stay with?" in transcript
    assert "Answer: Shame is hardest to stay with." in transcript


def test_output_deterministic() -> None:
    answers = _full_answers()
    first = build_profile_from_answers(answers)
    second = build_profile_from_answers(answers)
    assert first == second
    assert combined_answer_text(answers) == combined_answer_text(answers)


def test_all_required_answers_collected() -> None:
    assert all_required_answers_collected(_full_answers()) is True
    assert all_required_answers_collected(GuidedAssessmentAnswers()) is False
