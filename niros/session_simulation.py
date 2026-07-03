from __future__ import annotations

from dataclasses import dataclass

from niros.scenario_blueprint import build_scenario_blueprint
from niros.scenario_script_skeleton import (
    RELATIONSHIP_PATTERN_IDS,
    build_scenario_script_skeleton,
)
from niros.session_engine import SessionContext, SessionEngine, SessionState

EXPLORATION_SEGMENT_LABELS = {
    "self_worth_instability": "Self-compassion",
    "rumination": "Acceptance / release",
    "emotional_suppression": "Emotional expression",
    "perfectionism": "Flexibility",
}

PHASE_SEGMENT_LABELS = {
    "opening": "Opening",
    "stabilization": "Stabilization",
    "integration": "Integration",
    "closing": "Closing",
}


@dataclass(frozen=True)
class SessionEvent:
    timestamp: str
    state: SessionState
    segment_name: str
    objective: str
    expected_focus: str
    expected_patterns: tuple[str, ...]
    expected_emotions: tuple[str, ...]


@dataclass(frozen=True)
class SessionTimeline:
    start_time: str
    end_time: str
    ordered_events: tuple[SessionEvent, ...]


def simulate_session(human_profile: dict) -> SessionTimeline:
    blueprint = build_scenario_blueprint(human_profile)
    skeleton = build_scenario_script_skeleton(blueprint)
    engine = SessionEngine(skeleton)

    events: list[SessionEvent] = []
    context = engine.start_session()
    events.append(_event_from_context(context))

    while not engine.is_complete():
        context = engine.advance_state()
        events.append(_event_from_context(context))

    return SessionTimeline(
        start_time=format_timestamp(0),
        end_time=format_timestamp(context.elapsed_time),
        ordered_events=tuple(events),
    )


def format_timestamp(total_minutes: int) -> str:
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}:00"


def _event_from_context(context: SessionContext) -> SessionEvent:
    segment = context.current_segment
    if segment is None:
        return SessionEvent(
            timestamp=format_timestamp(context.elapsed_time),
            state=context.current_state,
            segment_name=_terminal_segment_name(context.current_state),
            objective="",
            expected_focus="",
            expected_patterns=(),
            expected_emotions=(),
        )

    return SessionEvent(
        timestamp=format_timestamp(context.elapsed_time),
        state=context.current_state,
        segment_name=_segment_display_name(segment),
        objective=segment.objective,
        expected_focus=_expected_focus(segment),
        expected_patterns=tuple(segment.target_patterns),
        expected_emotions=tuple(segment.target_emotions),
    )


def _terminal_segment_name(state: SessionState) -> str:
    if state == SessionState.PREPARATION:
        return "Preparation"
    if state == SessionState.COMPLETED:
        return "Completed"
    return state.value.replace("_", " ").title()


def _segment_display_name(segment) -> str:
    if segment.phase_name in PHASE_SEGMENT_LABELS:
        return PHASE_SEGMENT_LABELS[segment.phase_name]

    if segment.phase_name.startswith("exploration"):
        if any(pattern_id in RELATIONSHIP_PATTERN_IDS for pattern_id in segment.target_patterns):
            return "Relationship exploration"
        for pattern_id in segment.target_patterns:
            label = EXPLORATION_SEGMENT_LABELS.get(pattern_id)
            if label is not None:
                return label
        return "Exploration"

    return segment.phase_name.replace("_", " ").title()


def _expected_focus(segment) -> str:
    return f"{segment.musical_direction}; {segment.vocal_direction}"
