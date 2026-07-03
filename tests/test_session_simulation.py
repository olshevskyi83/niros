from niros.human_profile_summary import build_human_profile_summary
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.scenario_blueprint import build_scenario_blueprint
from niros.scenario_script_skeleton import build_scenario_script_skeleton
from niros.session_engine import SessionState
from niros.session_simulation import format_timestamp, simulate_session


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str,
    sequence: int,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-simulation-001",
        evidence_id=f"session-simulation-001:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _profile_from_tags(tags: list[PatternTag]) -> dict:
    return build_human_profile_summary(tags)


def test_empty_profile_handled_safely():
    profile = _profile_from_tags([])
    timeline = simulate_session(profile)

    assert timeline.start_time == "00:00:00"
    assert timeline.end_time == format_timestamp(
        build_scenario_script_skeleton(build_scenario_blueprint(profile)).total_estimated_duration
    )
    assert timeline.ordered_events
    assert timeline.ordered_events[0].state == SessionState.PREPARATION
    assert timeline.ordered_events[-1].state == SessionState.COMPLETED


def test_deterministic_timeline():
    profile = _profile_from_tags(
        [
            _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
            _pattern_tag("emotional_suppression", tag_id="tag-2", sequence=1),
        ]
    )

    first = simulate_session(profile)
    second = simulate_session(profile)

    assert first == second


def test_no_missing_phases():
    profile = _profile_from_tags(
        [
            _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
            _pattern_tag("emotional_suppression", tag_id="tag-2", sequence=1),
        ]
    )
    skeleton = build_scenario_script_skeleton(build_scenario_blueprint(profile))
    timeline = simulate_session(profile)

    active_events = [
        event
        for event in timeline.ordered_events
        if event.state not in {SessionState.PREPARATION, SessionState.COMPLETED}
    ]

    assert len(active_events) == len(skeleton.segments)
    assert {event.segment_name for event in active_events} >= {
        "Opening",
        "Stabilization",
        "Relationship exploration",
        "Emotional expression",
        "Integration",
        "Closing",
    }


def test_ordered_timestamps():
    profile = _profile_from_tags(
        [
            _pattern_tag("rumination", tag_id="tag-1", sequence=0),
            _pattern_tag("perfectionism", tag_id="tag-2", sequence=1),
        ]
    )
    timeline = simulate_session(profile)

    minute_values = [
        int(event.timestamp.split(":")[0]) * 60 + int(event.timestamp.split(":")[1])
        for event in timeline.ordered_events
    ]

    assert minute_values == sorted(minute_values)
    assert timeline.ordered_events[0].timestamp == "00:00:00"


def test_total_duration_matches_script():
    profile = _profile_from_tags(
        [
            _pattern_tag("self_worth_instability", tag_id="tag-1", sequence=0),
            _pattern_tag("rumination", tag_id="tag-2", sequence=1),
        ]
    )
    skeleton = build_scenario_script_skeleton(build_scenario_blueprint(profile))
    timeline = simulate_session(profile)

    assert timeline.end_time == format_timestamp(skeleton.total_estimated_duration)
    assert timeline.ordered_events[-1].timestamp == timeline.end_time


def test_timeline_contains_every_transition():
    profile = _profile_from_tags(
        [_pattern_tag("emotional_suppression", tag_id="tag-1", sequence=0)]
    )
    timeline = simulate_session(profile)
    states = [event.state for event in timeline.ordered_events]

    assert states[0] == SessionState.PREPARATION
    assert SessionState.OPENING in states
    assert SessionState.STABILIZATION in states
    assert SessionState.EXPLORATION in states
    assert SessionState.INTEGRATION in states
    assert SessionState.CLOSING in states
    assert states[-1] == SessionState.COMPLETED


def test_active_events_carry_segment_metadata():
    profile = _profile_from_tags(
        [_pattern_tag("rumination", tag_id="tag-1", sequence=0)]
    )
    timeline = simulate_session(profile)

    exploration_event = next(
        event for event in timeline.ordered_events if event.state == SessionState.EXPLORATION
    )

    assert exploration_event.objective
    assert exploration_event.expected_focus
    assert exploration_event.expected_patterns == ("rumination",)
    assert exploration_event.expected_emotions
