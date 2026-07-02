from niros.models import InterviewPhase, InterviewState


class InvalidTransitionError(ValueError):
    """Raised when an interview state transition is not allowed."""


def initial_state(session_id: str) -> InterviewState:
    return InterviewState(
        session_id=session_id,
        state=InterviewPhase.CONSENT,
    )


def advance(state: InterviewState, *, consent_granted: bool = False) -> InterviewState:
    if state.state == InterviewPhase.CONSENT:
        if not consent_granted:
            raise InvalidTransitionError(
                "Cannot leave consent without active consent from the user."
            )
        return state.model_copy(update={"state": InterviewPhase.FREE_NARRATIVE})

    raise InvalidTransitionError(
        f"No transition implemented from state {state.state.value!r}."
    )
