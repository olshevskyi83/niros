"""Whisper Adapter contract — deterministic mock transcription until Whisper is integrated."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from niros.voice_transcript import (
    DEFAULT_CONFIDENCE,
    TRANSCRIPT_STATUS_TRANSCRIBED,
    VoiceInput,
    VoiceTranscript,
)

DEFAULT_PROVIDER = "mock_whisper"
DEFAULT_MODEL_NAME = "mock-small"
DEFAULT_DEVICE = "cpu"


@dataclass(frozen=True)
class WhisperAdapterConfig:
    provider: str = DEFAULT_PROVIDER
    model_name: str = DEFAULT_MODEL_NAME
    language: str = "uk"
    device: str = DEFAULT_DEVICE


@dataclass(frozen=True)
class WhisperTranscriptionResult:
    transcript: str
    language: str
    confidence: float = DEFAULT_CONFIDENCE
    provider: str = DEFAULT_PROVIDER
    model_name: str = DEFAULT_MODEL_NAME
    transcription_status: str = TRANSCRIPT_STATUS_TRANSCRIBED


class VoiceInputLike(Protocol):
    audio_path: str
    language: str
    source: str
    session_id: str


def build_whisper_transcription_result(
    transcript: str,
    config: WhisperAdapterConfig | None = None,
) -> WhisperTranscriptionResult:
    """Build a deterministic whisper transcription result."""
    resolved = config or WhisperAdapterConfig()
    return WhisperTranscriptionResult(
        transcript=transcript,
        language=resolved.language,
        confidence=DEFAULT_CONFIDENCE,
        provider=resolved.provider,
        model_name=resolved.model_name,
        transcription_status=TRANSCRIPT_STATUS_TRANSCRIBED,
    )


def transcribe_audio_mock(
    voice_input: VoiceInputLike,
    transcript: str,
    config: WhisperAdapterConfig | None = None,
) -> VoiceTranscript:
    """Mock transcription adapter for tests before Whisper is added."""
    language = config.language if config is not None else voice_input.language
    return VoiceTranscript(
        session_id=voice_input.session_id,
        transcript=transcript,
        language=language,
        source=voice_input.source,
        confidence=DEFAULT_CONFIDENCE,
        transcript_status=TRANSCRIPT_STATUS_TRANSCRIBED,
    )
