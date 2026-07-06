"""Voice transcript to text pipeline bridge — voice is input modality only."""

from __future__ import annotations

from test_semantic_validation_fixtures import build_profile_from_case, semantic_validation_cases
from test_semantic_validation_pipeline import (
    PATTERN_ACCEPTANCE,
    PATTERN_DEEP_EXPOSURE,
    PATTERN_SELF_COMPASSION,
    semantic_validation_pattern_library,
    _caution_ids,
    _selected_ids,
)

from niros.pattern_person_fit_report import build_pattern_fit_report
from niros.strategy_candidate_builder import build_strategy_candidate
from niros.strategy_explanation import StrategyExplanation, build_strategy_explanation
from niros.voice_transcript import VoiceInput
from niros.whisper_adapter import transcribe_audio_mock
from niros_tle.universal_pattern_library import build_universal_pattern_library

SHAME_CASE_ID = "semantic_case_shame_self_criticism"


def _shame_case():
    return next(case for case in semantic_validation_cases() if case.case_id == SHAME_CASE_ID)


def run_voice_transcript_pipeline(
    *,
    max_patterns: int = 3,
) -> tuple[object, object, StrategyExplanation, object]:
    """Voice → mock transcript → existing text-based fit pipeline."""
    case = _shame_case()
    voice_input = VoiceInput(
        audio_path="fake_audio.wav",
        language="uk",
        source="user_upload",
        session_id="voice_session_shame_001",
    )
    transcript = transcribe_audio_mock(voice_input, case.user_text)
    profile = build_profile_from_case(case)
    library = build_universal_pattern_library(semantic_validation_pattern_library())
    fit_report = build_pattern_fit_report(profile, library)
    strategy = build_strategy_candidate(fit_report, max_patterns=max_patterns)
    explanation = build_strategy_explanation(strategy)
    return transcript, fit_report, strategy, explanation


def test_voice_transcript_enters_existing_text_pipeline():
    case = _shame_case()
    voice_input = VoiceInput(
        audio_path="fake_audio.wav",
        language="uk",
        source="user_upload",
        session_id="voice_session_shame_001",
    )
    transcript = transcribe_audio_mock(voice_input, case.user_text)

    assert transcript.session_id == "voice_session_shame_001"
    assert transcript.transcript == case.user_text
    assert transcript.language == "uk"

    _, _fit_report, strategy, explanation = run_voice_transcript_pipeline()
    selected = _selected_ids(strategy)
    caution = _caution_ids(strategy)

    assert PATTERN_SELF_COMPASSION in selected
    assert PATTERN_ACCEPTANCE in selected
    assert PATTERN_DEEP_EXPOSURE in caution
    assert PATTERN_DEEP_EXPOSURE not in selected
    assert explanation.explanation_items
    assert explanation.profile_id == case.case_id


def test_voice_transcript_pipeline_is_deterministic():
    first = run_voice_transcript_pipeline()
    second = run_voice_transcript_pipeline()

    first_selected = tuple(score.pattern_id for score in first[2].selected_patterns)
    second_selected = tuple(score.pattern_id for score in second[2].selected_patterns)
    assert first_selected == second_selected
    assert first[3].summary == second[3].summary
