import pytest

from niros.models import SupportedLanguage
from niros.statements import UnsupportedModalityError, split_transcript_to_statements
from niros.transcript import InputModality, Transcript


def test_split_transcript_to_statements_example():
    transcript = Transcript(
        session_id="session-001",
        raw_text="I am afraid of disappointing people. I avoid conflict.",
        language=SupportedLanguage.ENGLISH,
    )

    statements = split_transcript_to_statements(transcript)

    assert len(statements) == 2
    assert statements[0].text == "I am afraid of disappointing people."
    assert statements[1].text == "I avoid conflict."
    assert statements[0].sequence == 0
    assert statements[1].sequence == 1
    assert transcript.raw_text == "I am afraid of disappointing people. I avoid conflict."


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


def test_split_preserves_language():
    transcript = Transcript(
        session_id="session-001",
        raw_text="Me siento agotado. No duermo bien.",
        language=SupportedLanguage.SPANISH,
    )

    statements = split_transcript_to_statements(transcript)

    assert len(statements) == 2
    assert all(statement.language == SupportedLanguage.SPANISH for statement in statements)


def test_split_handles_exclamation_and_question_marks():
    transcript = Transcript(
        session_id="session-001",
        raw_text="I feel stuck! What should I do?",
        language=SupportedLanguage.ENGLISH,
    )

    statements = split_transcript_to_statements(transcript)

    assert [statement.text for statement in statements] == [
        "I feel stuck!",
        "What should I do?",
    ]


def test_split_ignores_empty_statements():
    transcript = Transcript(
        session_id="session-001",
        raw_text="   ",
        language=SupportedLanguage.RUSSIAN,
    )

    assert split_transcript_to_statements(transcript) == []


def test_split_rejects_voice_modality():
    transcript = Transcript(
        session_id="session-001",
        raw_text="I feel anxious.",
        language=SupportedLanguage.ENGLISH,
        input_modality=InputModality.VOICE,
        audio_ref="s3://bucket/session-001.wav",
    )

    with pytest.raises(UnsupportedModalityError, match="Only text input is supported"):
        split_transcript_to_statements(transcript)
