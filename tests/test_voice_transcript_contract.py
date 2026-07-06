"""Tests for voice transcript contract (Sprint 025 / Slice 1)."""

from __future__ import annotations

from niros.voice_transcript import (
    DEFAULT_CONFIDENCE,
    DEFAULT_LANGUAGE,
    DEFAULT_SESSION_ID,
    DEFAULT_SOURCE,
    TRANSCRIPT_STATUS_TRANSCRIBED,
    VoiceInput,
    VoiceTranscript,
    create_transcript_from_text,
)


def test_voice_input_defaults():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav")
    assert voice_input.language == DEFAULT_LANGUAGE
    assert voice_input.language == "uk"
    assert voice_input.source == DEFAULT_SOURCE
    assert voice_input.source == "user_upload"
    assert voice_input.session_id == DEFAULT_SESSION_ID
    assert voice_input.session_id == "voice_session_001"


def test_voice_transcript_defaults():
    transcript = VoiceTranscript(
        session_id="voice_session_001",
        transcript="test transcript",
        language="uk",
        source="user_upload",
    )
    assert transcript.confidence == DEFAULT_CONFIDENCE
    assert transcript.confidence == 1.0
    assert transcript.transcript_status == TRANSCRIPT_STATUS_TRANSCRIBED
    assert transcript.transcript_status == "transcribed"


def test_create_transcript_from_text_preserves_session_id():
    voice_input = VoiceInput(
        audio_path="/tmp/session_002.wav",
        session_id="voice_session_002",
    )
    result = create_transcript_from_text(voice_input, "sample transcript")
    assert result.session_id == voice_input.session_id


def test_create_transcript_from_text_preserves_language():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav", language="uk")
    result = create_transcript_from_text(voice_input, "sample transcript")
    assert result.language == voice_input.language


def test_create_transcript_from_text_preserves_source():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav", source="user_upload")
    result = create_transcript_from_text(voice_input, "sample transcript")
    assert result.source == voice_input.source


def test_create_transcript_from_text_preserves_transcript():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav")
    result = create_transcript_from_text(voice_input, "Мені важко говорити про себе.")
    assert result.transcript == "Мені важко говорити про себе."


def test_create_transcript_from_text_confidence_defaults_to_one():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav")
    result = create_transcript_from_text(voice_input, "sample transcript")
    assert result.confidence == 1.0


def test_create_transcript_from_text_transcript_status_defaults_to_transcribed():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav")
    result = create_transcript_from_text(voice_input, "sample transcript")
    assert result.transcript_status == "transcribed"


def test_create_transcript_from_text_output_is_deterministic():
    voice_input = VoiceInput(
        audio_path="/tmp/session_001.wav",
        language="uk",
        source="user_upload",
        session_id="voice_session_001",
    )
    first = create_transcript_from_text(voice_input, "deterministic transcript")
    second = create_transcript_from_text(voice_input, "deterministic transcript")
    assert first == second
