from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from niros.scenario_script_skeleton import (
    CLOSING_PHASE_NAME,
    EXPLORATION_PHASE_NAME,
    INTEGRATION_PHASE_NAME,
    OPENING_PHASE_NAME,
    STABILIZATION_PHASE_NAME,
    ScenarioScriptSkeleton,
    ScenarioSegment,
)


class SessionState(str, Enum):
    PREPARATION = "preparation"
    OPENING = "opening"
    STABILIZATION = "stabilization"
    EXPLORATION = "exploration"
    DEEP_EXPLORATION = "deep_exploration"
    INTEGRATION = "integration"
    CLOSING = "closing"
    COMPLETED = "completed"


@dataclass(frozen=True)
class SessionContext:
    current_state: SessionState
    elapsed_time: int
    completed_segments: tuple[ScenarioSegment, ...]
    remaining_segments: tuple[ScenarioSegment, ...]
    current_segment: ScenarioSegment | None


class SessionEngine:
    def __init__(self, skeleton: ScenarioScriptSkeleton) -> None:
        self._skeleton = skeleton
        self._context: SessionContext | None = None

    def start_session(self) -> SessionContext:
        self._context = SessionContext(
            current_state=SessionState.PREPARATION,
            elapsed_time=0,
            completed_segments=(),
            remaining_segments=tuple(self._skeleton.segments),
            current_segment=None,
        )
        return self._context

    def advance_state(self) -> SessionContext:
        context = self._require_context()
        if context.current_state == SessionState.COMPLETED:
            return context

        if context.current_state == SessionState.PREPARATION:
            return self._enter_segment(
                segment_index=0,
                completed_segments=(),
                elapsed_time=0,
            )

        completed_segments = list(context.completed_segments)
        elapsed_time = context.elapsed_time
        if context.current_segment is not None:
            completed_segments.append(context.current_segment)
            elapsed_time += context.current_segment.estimated_duration

        next_index = len(completed_segments)
        if next_index >= len(self._skeleton.segments):
            self._context = SessionContext(
                current_state=SessionState.COMPLETED,
                elapsed_time=elapsed_time,
                completed_segments=tuple(completed_segments),
                remaining_segments=(),
                current_segment=None,
            )
            return self._context

        return self._enter_segment(
            segment_index=next_index,
            completed_segments=tuple(completed_segments),
            elapsed_time=elapsed_time,
        )

    def current_state(self) -> SessionState:
        return self._require_context().current_state

    def is_complete(self) -> bool:
        return self._require_context().current_state == SessionState.COMPLETED

    def context(self) -> SessionContext:
        return self._require_context()

    def _enter_segment(
        self,
        *,
        segment_index: int,
        completed_segments: tuple[ScenarioSegment, ...],
        elapsed_time: int,
    ) -> SessionContext:
        segment = self._skeleton.segments[segment_index]
        self._context = SessionContext(
            current_state=_state_for_segment(
                segment,
                segment_index=segment_index,
                segments=self._skeleton.segments,
            ),
            elapsed_time=elapsed_time,
            completed_segments=completed_segments,
            remaining_segments=tuple(self._skeleton.segments[segment_index + 1 :]),
            current_segment=segment,
        )
        return self._context

    def _require_context(self) -> SessionContext:
        if self._context is None:
            raise RuntimeError("Session has not started. Call start_session() first.")
        return self._context


def _state_for_segment(
    segment: ScenarioSegment,
    *,
    segment_index: int,
    segments: list[ScenarioSegment],
) -> SessionState:
    if segment.phase_name == OPENING_PHASE_NAME:
        return SessionState.OPENING
    if segment.phase_name == STABILIZATION_PHASE_NAME:
        return SessionState.STABILIZATION
    if segment.phase_name.startswith(EXPLORATION_PHASE_NAME):
        exploration_number = sum(
            1
            for index in range(segment_index + 1)
            if segments[index].phase_name.startswith(EXPLORATION_PHASE_NAME)
        )
        if exploration_number == 1:
            return SessionState.EXPLORATION
        return SessionState.DEEP_EXPLORATION
    if segment.phase_name == INTEGRATION_PHASE_NAME:
        return SessionState.INTEGRATION
    if segment.phase_name == CLOSING_PHASE_NAME:
        return SessionState.CLOSING
    raise ValueError(f"Unsupported segment phase: {segment.phase_name}")
