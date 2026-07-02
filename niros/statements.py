import re

from pydantic import BaseModel

from niros.models import SupportedLanguage
from niros.transcript import InputModality, Transcript

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


class UnsupportedModalityError(ValueError):
    """Raised when input processing is not implemented for a modality."""


class Statement(BaseModel):
    session_id: str
    text: str
    sequence: int
    language: SupportedLanguage
    input_modality: InputModality = InputModality.TEXT


def split_transcript_to_statements(transcript: Transcript) -> list[Statement]:
    if transcript.input_modality != InputModality.TEXT:
        raise UnsupportedModalityError(
            f"Only text input is supported; got {transcript.input_modality.value!r}."
        )

    segments = _split_on_punctuation(transcript.raw_text)
    return [
        Statement(
            session_id=transcript.session_id,
            text=text,
            sequence=index,
            language=transcript.language,
            input_modality=InputModality.TEXT,
        )
        for index, text in enumerate(segments)
    ]


def _split_on_punctuation(raw_text: str) -> list[str]:
    normalized = raw_text.strip()
    if not normalized:
        return []

    parts = _SENTENCE_BOUNDARY.split(normalized)
    return [part.strip() for part in parts if part.strip()]
