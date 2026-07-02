import re

from niros.models import InputModality, Statement, Transcript

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


class UnsupportedModalityError(ValueError):
    """Raised when input processing is not implemented for a modality."""


def extract_statements(transcript: Transcript) -> list[Statement]:
    if transcript.input_modality != InputModality.TEXT:
        raise UnsupportedModalityError(
            f"Only text input is supported; got {transcript.input_modality.value!r}."
        )

    segments = _split_text(transcript.raw_text)
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


def _split_text(raw_text: str) -> list[str]:
    normalized = raw_text.strip()
    if not normalized:
        return []

    segments: list[str] = []
    for paragraph in re.split(r"\n+", normalized):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        parts = _SENTENCE_BOUNDARY.split(paragraph)
        for part in parts:
            text = part.strip()
            if text:
                segments.append(text)

    return segments
