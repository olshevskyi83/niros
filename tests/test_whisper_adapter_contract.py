"""Tests for Whisper Adapter contract."""

from __future__ import annotations

from niros.voice_transcript import TRANSCRIPT_STATUS_TRANSCRIBED, VoiceInput, VoiceTranscript
from niros.whisper_adapter import (
    DEFAULT_DEVICE,
    DEFAULT_MODEL_NAME,
    DEFAULT_PROVIDER,
    WhisperAdapterConfig,
    WhisperTranscriptionResult,
    build_whisper_transcription_result,
    transcribe_audio_mock,
)


def test_whisper_adapter_config_defaults():
    config = WhisperAdapterConfig()
    assert config.provider == DEFAULT_PROVIDER
    assert config.provider == "mock_whisper"
    assert config.model_name == DEFAULT_MODEL_NAME
    assert config.model_name == "mock-small"
    assert config.language == "uk"
    assert config.device == DEFAULT_DEVICE
    assert config.device == "cpu"


def test_whisper_transcription_result_defaults():
    result = WhisperTranscriptionResult(
        transcript="sample transcript",
        language="uk",
    )
    assert result.confidence == 1.0
    assert result.provider == DEFAULT_PROVIDER
    assert result.model_name == DEFAULT_MODEL_NAME
    assert result.transcription_status == TRANSCRIPT_STATUS_TRANSCRIBED
    assert result.transcription_status == "transcribed"


def test_build_whisper_transcription_result_preserves_transcript():
    result = build_whisper_transcription_result("Мені важко говорити про себе.")
    assert result.transcript == "Мені важко говорити про себе."


def test_build_whisper_transcription_result_uses_config_fields():
    config = WhisperAdapterConfig(
        provider="mock_whisper",
        model_name="mock-large",
        language="en",
        device="cpu",
    )
    result = build_whisper_transcription_result("hello world", config=config)
    assert result.language == "en"
    assert result.provider == "mock_whisper"
    assert result.model_name == "mock-large"


def test_transcribe_audio_mock_returns_voice_transcript():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav")
    result = transcribe_audio_mock(voice_input, "sample transcript")
    assert isinstance(result, VoiceTranscript)


def test_transcribe_audio_mock_preserves_session_id():
    voice_input = VoiceInput(
        audio_path="/tmp/session_002.wav",
        session_id="voice_session_002",
    )
    result = transcribe_audio_mock(voice_input, "sample transcript")
    assert result.session_id == "voice_session_002"


def test_transcribe_audio_mock_preserves_source():
    voice_input = VoiceInput(
        audio_path="/tmp/session_001.wav",
        source="user_upload",
    )
    result = transcribe_audio_mock(voice_input, "sample transcript")
    assert result.source == "user_upload"


def test_transcribe_audio_mock_uses_config_language():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav", language="uk")
    config = WhisperAdapterConfig(language="en")
    result = transcribe_audio_mock(voice_input, "sample transcript", config=config)
    assert result.language == "en"


def test_transcribe_audio_mock_uses_voice_input_language_without_config():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav", language="uk")
    result = transcribe_audio_mock(voice_input, "sample transcript")
    assert result.language == "uk"


def test_transcribe_audio_mock_confidence_is_one():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav")
    result = transcribe_audio_mock(voice_input, "sample transcript")
    assert result.confidence == 1.0


def test_transcribe_audio_mock_transcript_status_is_transcribed():
    voice_input = VoiceInput(audio_path="/tmp/session_001.wav")
    result = transcribe_audio_mock(voice_input, "sample transcript")
    assert result.transcript_status == "transcribed"


def test_output_is_deterministic():
    voice_input = VoiceInput(
        audio_path="/tmp/session_001.wav",
        language="uk",
        source="user_upload",
        session_id="voice_session_001",
    )
    config = WhisperAdapterConfig(language="uk")
    first = transcribe_audio_mock(voice_input, "deterministic transcript", config=config)
    second = transcribe_audio_mock(voice_input, "deterministic transcript", config=config)
    assert first == second

    result_first = build_whisper_transcription_result("deterministic transcript", config=config)
    result_second = build_whisper_transcription_result("deterministic transcript", config=config)
    assert result_first == result_second
