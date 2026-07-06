"""Intake Session State — deterministic adaptive intake brain state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from niros.clarification_selector import ClarificationQuestion, select_adaptive_question
from niros.intake_coverage import IntakeCoverageState, evaluate_intake_coverage, update_coverage_from_signals
from niros.intake_readiness import build_readiness_report_from_session
from niros.pattern_person_fit_contracts import PersonFitProfile

DEFAULT_INTAKE_SESSION_ID = "intake_session_001"
USER_SPEAKER = "user"


@dataclass(frozen=True)
class IntakeTurn:
    turn_id: str
    speaker: str
    text: str
    detected_signals: tuple[str, ...] = field(default_factory=tuple)
    detected_needs: tuple[str, ...] = field(default_factory=tuple)
    detected_risk_signals: tuple[str, ...] = field(default_factory=tuple)
    target_dimension: str = ""


@dataclass(frozen=True)
class IntakeSessionState:
    session_id: str
    turns: tuple[IntakeTurn, ...] = field(default_factory=tuple)
    coverage_state: IntakeCoverageState = field(default_factory=IntakeCoverageState)
    active_signals: tuple[str, ...] = field(default_factory=tuple)
    needs: tuple[str, ...] = field(default_factory=tuple)
    risk_signals: tuple[str, ...] = field(default_factory=tuple)
    next_question: ClarificationQuestion | None = None
    is_ready_for_strategy: bool = False


def _unique_sorted(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _next_user_turn_id(turns: tuple[IntakeTurn, ...]) -> str:
    user_turn_count = sum(1 for turn in turns if turn.speaker == USER_SPEAKER)
    return f"user_turn_{user_turn_count + 1:03d}"


def _resolve_next_question(
    session_state: IntakeSessionState,
) -> tuple[bool, ClarificationQuestion | None]:
    readiness = build_readiness_report_from_session(session_state)
    if readiness.is_ready:
        return True, None
    coverage_report = evaluate_intake_coverage(session_state.coverage_state)
    return False, select_adaptive_question(
        coverage_report,
        active_signals=session_state.active_signals,
    )


def create_intake_session(session_id: str = DEFAULT_INTAKE_SESSION_ID) -> IntakeSessionState:
    """Create an empty intake session with the first clarification question."""
    coverage_state = IntakeCoverageState()
    session = IntakeSessionState(
        session_id=session_id,
        coverage_state=coverage_state,
    )
    is_ready, next_question = _resolve_next_question(session)
    return IntakeSessionState(
        session_id=session_id,
        coverage_state=coverage_state,
        next_question=next_question,
        is_ready_for_strategy=is_ready,
    )


def add_user_turn(
    session_state: IntakeSessionState,
    text: str,
    *,
    detected_signals: Iterable[str] = (),
    detected_needs: Iterable[str] = (),
    detected_risk_signals: Iterable[str] = (),
) -> IntakeSessionState:
    """Append a user turn and refresh coverage, accumulation, and next question."""
    signal_values = tuple(detected_signals)
    need_values = tuple(detected_needs)
    risk_values = tuple(detected_risk_signals)
    target_dimension = (
        session_state.next_question.target_dimension
        if session_state.next_question is not None
        else ""
    )

    turn = IntakeTurn(
        turn_id=_next_user_turn_id(session_state.turns),
        speaker=USER_SPEAKER,
        text=text,
        detected_signals=signal_values,
        detected_needs=need_values,
        detected_risk_signals=risk_values,
        target_dimension=target_dimension,
    )

    active_signals = _unique_sorted((*session_state.active_signals, *signal_values))
    needs = _unique_sorted((*session_state.needs, *need_values))
    risk_signals = _unique_sorted((*session_state.risk_signals, *risk_values))

    coverage_state = update_coverage_from_signals(
        session_state.coverage_state,
        active_signals=signal_values,
        needs=need_values,
        risk_signals=risk_values,
        turn_text=text,
    )

    updated_session = IntakeSessionState(
        session_id=session_state.session_id,
        turns=session_state.turns + (turn,),
        coverage_state=coverage_state,
        active_signals=active_signals,
        needs=needs,
        risk_signals=risk_signals,
    )
    is_ready, next_question = _resolve_next_question(updated_session)
    return IntakeSessionState(
        session_id=updated_session.session_id,
        turns=updated_session.turns,
        coverage_state=updated_session.coverage_state,
        active_signals=updated_session.active_signals,
        needs=updated_session.needs,
        risk_signals=updated_session.risk_signals,
        next_question=next_question,
        is_ready_for_strategy=is_ready,
    )


def build_intake_transcript(session_state: IntakeSessionState) -> str:
    """Build a deterministic USER-only transcript from intake turns."""
    lines = [f"USER: {turn.text}" for turn in session_state.turns if turn.speaker == USER_SPEAKER]
    return "\n".join(lines)


def _infer_dominant_domains(active_signals: tuple[str, ...]) -> tuple[str, ...]:
    domains: list[str] = []
    if any(
        signal in active_signals
        for signal in ("shame_sensitivity", "harsh_self_criticism")
    ):
        domains.append("self")
    if any(
        signal in active_signals
        for signal in ("emotional_avoidance", "overwhelm_risk", "emotional_instability")
    ):
        domains.append("emotion_regulation")
    if any(signal in active_signals for signal in ("rumination", "catastrophizing")):
        domains.append("cognitive")
    if any(signal in active_signals for signal in ("values_confusion", "low_direction")):
        domains.append("values")
    if any(
        signal in active_signals
        for signal in ("existential_emptiness", "loss_of_meaning", "identity_diffusion")
    ):
        domains.append("meaning")
    return tuple(dict.fromkeys(domains))


def build_person_fit_profile_from_intake(
    session_state: IntakeSessionState,
    profile_id: str | None = None,
) -> PersonFitProfile:
    """Build a PersonFitProfile from accumulated intake session signals."""
    return PersonFitProfile(
        profile_id=profile_id or session_state.session_id,
        active_signals=session_state.active_signals,
        dominant_domains=_infer_dominant_domains(session_state.active_signals),
        risk_signals=session_state.risk_signals,
        needs=session_state.needs,
        session_phase="preparation",
    )
