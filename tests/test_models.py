import pytest
from pydantic import ValidationError

from niros.models import InterviewPhase, InterviewState, SupportedLanguage


@pytest.mark.parametrize(
    "language",
    [
        SupportedLanguage.ENGLISH,
        SupportedLanguage.SPANISH,
        SupportedLanguage.RUSSIAN,
    ],
)
def test_interview_state_accepts_supported_input_languages(language):
    state = InterviewState(
        session_id="session-001",
        state=InterviewPhase.CONSENT,
        input_language=language,
    )

    assert state.input_language == language


def test_interview_state_rejects_unsupported_input_language():
    with pytest.raises(ValidationError):
        InterviewState(
            session_id="session-001",
            state=InterviewPhase.CONSENT,
            input_language="fr",
        )
