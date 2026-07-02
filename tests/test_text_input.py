import pytest

from niros.models import InputModality, SupportedLanguage, Transcript
from niros.text_input import UnsupportedModalityError, extract_statements


def test_transcript_defaults_to_text_modality():
    transcript = Transcript(
        session_id="session-001",
        raw_text="I feel overwhelmed.",
        language=SupportedLanguage.ENGLISH,
    )

    assert transcript.input_modality == InputModality.TEXT
    assert transcript.audio_ref is None
    assert transcript.voice_features is None


def test_transcript_accepts_future_voice_fields():
    transcript = Transcript(
        session_id="session-001",
        raw_text="I feel overwhelmed.",
        language=SupportedLanguage.SPANISH,
        input_modality=InputModality.VOICE,
        audio_ref="s3://bucket/session-001.wav",
        voice_features={"duration_ms": 4200},
    )

    assert transcript.input_modality == InputModality.VOICE
    assert transcript.audio_ref == "s3://bucket/session-001.wav"
    assert transcript.voice_features == {"duration_ms": 4200}


def test_extract_statements_splits_sentences():
    transcript = Transcript(
        session_id="session-001",
        raw_text="I feel anxious. It started last month. Sleep is worse.",
        language=SupportedLanguage.ENGLISH,
    )

    statements = extract_statements(transcript)

    assert len(statements) == 3
    assert [s.text for s in statements] == [
        "I feel anxious.",
        "It started last month.",
        "Sleep is worse.",
    ]
    assert [s.sequence for s in statements] == [0, 1, 2]
    assert all(s.session_id == "session-001" for s in statements)
    assert all(s.language == SupportedLanguage.ENGLISH for s in statements)
    assert all(s.input_modality == InputModality.TEXT for s in statements)


def test_extract_statements_splits_paragraphs_without_punctuation():
    transcript = Transcript(
        session_id="session-001",
        raw_text="Me siento agotado\nNo duermo bien",
        language=SupportedLanguage.SPANISH,
    )

    statements = extract_statements(transcript)

    assert len(statements) == 2
    assert statements[0].text == "Me siento agotado"
    assert statements[1].text == "No duermo bien"


def test_extract_statements_returns_empty_list_for_blank_text():
    transcript = Transcript(
        session_id="session-001",
        raw_text="   \n\n  ",
        language=SupportedLanguage.RUSSIAN,
    )

    assert extract_statements(transcript) == []


def test_extract_statements_rejects_voice_modality():
    transcript = Transcript(
        session_id="session-001",
        raw_text="I feel anxious.",
        language=SupportedLanguage.ENGLISH,
        input_modality=InputModality.VOICE,
        audio_ref="s3://bucket/session-001.wav",
    )

    with pytest.raises(UnsupportedModalityError, match="Only text input is supported"):
        extract_statements(transcript)
