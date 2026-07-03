from __future__ import annotations

from niros.session_simulation import SessionEvent, SessionTimeline

TIMELINE_TITLE = "=== NIROS Session Timeline ==="
EMPTY_TIMELINE_TEXT = (
    f"{TIMELINE_TITLE}\n\n"
    "No session events are available yet."
)


def render_session_timeline(timeline: SessionTimeline) -> str:
    if not timeline.ordered_events:
        return EMPTY_TIMELINE_TEXT

    lines = [
        TIMELINE_TITLE,
        "",
        f"Total duration: {_total_duration_minutes(timeline)} min",
        "",
    ]

    event_blocks = [_render_event(event) for event in timeline.ordered_events]
    lines.extend("\n".join(block for block in event_blocks).splitlines())

    return "\n".join(lines)


def _render_event(event: SessionEvent) -> str:
    lines = [
        f"{_display_timestamp(event.timestamp)} — {event.state.value.upper()}",
        f"Objective: {_format_field(event.objective)}",
        f"Expected focus: {_format_field(event.expected_focus)}",
        f"Expected patterns: {_format_list(event.expected_patterns)}",
        f"Expected emotions: {_format_list(event.expected_emotions)}",
        "",
    ]
    return "\n".join(lines)


def _display_timestamp(timestamp: str) -> str:
    hours, minutes, _seconds = timestamp.split(":")
    total_minutes = int(hours) * 60 + int(minutes)
    return f"{total_minutes:02d}:00"


def _total_duration_minutes(timeline: SessionTimeline) -> int:
    hours, minutes, _seconds = timeline.end_time.split(":")
    return int(hours) * 60 + int(minutes)


def _format_field(value: str) -> str:
    return value if value else "None"


def _format_list(values: tuple[str, ...]) -> str:
    if not values:
        return "None"
    return ", ".join(values)
