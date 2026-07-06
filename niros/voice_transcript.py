"""Voice transcript contract — audio metadata and transcript records (no interpretation)."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_LANGUAGE = "uk"
DEFAULT_SOURCE = "user_upload"
DEFAULT_SESSION_ID = "voice_session_001"
DEFAULT_CONFIDENCE = 1.0
TRANSCRIPT_STATUS_TRANSCRIBED = "transcribed"


@dataclass(frozen=True)
class VoiceInput:
    audio_path: str
    language: str = DEFAULT_LANGUAGE
    source: str = DEFAULT_SOURCE
    session_id: str = DEFAULT_SESSION_ID


@dataclass(frozen=True)
class VoiceTranscript:
    session_id: str
    transcript: str
    language: str
    source: str
    confidence: float = DEFAULT_CONFIDENCE
    transcript_status: str = TRANSCRIPT_STATUS_TRANSCRIBED


def create_transcript_from_text(voice_input: VoiceInput, transcript: str) -> VoiceTranscript:
    """Deterministic test adapter until Whisper transcription is added."""
    return VoiceTranscript(
        session_id=voice_input.session_id,
        transcript=transcript,
        language=voice_input.language,
        source=voice_input.source,
        confidence=DEFAULT_CONFIDENCE,
        transcript_status=TRANSCRIPT_STATUS_TRANSCRIBED,
    )
