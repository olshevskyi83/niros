import pytest

from niros.models import InterviewPhase, InterviewState
from niros.state_machine import InvalidTransitionError, advance, initial_state


def test_initial_state_is_consent():
    state = initial_state("session-001")

    assert state.session_id == "session-001"
    assert state.state == InterviewPhase.CONSENT
    assert state.completed_domains == []
    assert state.current_hypotheses == []


def test_consent_to_free_narrative_when_consent_granted():
    state = initial_state("session-001")

    next_state = advance(state, consent_granted=True)

    assert next_state.state == InterviewPhase.FREE_NARRATIVE
    assert next_state.session_id == "session-001"


def test_consent_without_grant_raises():
    state = initial_state("session-001")

    with pytest.raises(InvalidTransitionError, match="active consent"):
        advance(state, consent_granted=False)


def test_unimplemented_transition_raises():
    state = InterviewState(
        session_id="session-001",
        state=InterviewPhase.FREE_NARRATIVE,
    )

    with pytest.raises(InvalidTransitionError, match="No transition implemented"):
        advance(state, consent_granted=True)
