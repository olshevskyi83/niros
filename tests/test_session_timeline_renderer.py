from niros.human_profile_summary import build_human_profile_summary
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.scenario_blueprint import build_scenario_blueprint
from niros.scenario_script_skeleton import build_scenario_script_skeleton
from niros.session_engine import SessionState
from niros.session_simulation import SessionTimeline, simulate_session
from niros.session_timeline_renderer import EMPTY_TIMELINE_TEXT, render_session_timeline


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str,
    sequence: int,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-renderer-001",
        evidence_id=f"session-renderer-001:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _profile_from_tags(tags: list[PatternTag]) -> dict:
    return build_human_profile_summary(tags)


def test_renderer_includes_title():
    timeline = simulate_session(
        _profile_from_tags([_pattern_tag("rumination", tag_id="tag-1", sequence=0)])
    )

    rendered = render_session_timeline(timeline)

    assert "=== NIROS Session Timeline ===" in rendered


def test_renderer_includes_total_duration():
    profile = _profile_from_tags([_pattern_tag("rumination", tag_id="tag-1", sequence=0)])
    skeleton = build_scenario_script_skeleton(build_scenario_blueprint(profile))
    rendered = render_session_timeline(simulate_session(profile))

    assert f"Total duration: {skeleton.total_estimated_duration} min" in rendered


def test_renderer_includes_all_session_states():
    timeline = simulate_session(
        _profile_from_tags(
            [
                _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
                _pattern_tag("emotional_suppression", tag_id="tag-2", sequence=1),
            ]
        )
    )
    rendered = render_session_timeline(timeline)

    for state in (
        SessionState.PREPARATION,
        SessionState.OPENING,
        SessionState.STABILIZATION,
        SessionState.EXPLORATION,
        SessionState.INTEGRATION,
        SessionState.CLOSING,
        SessionState.COMPLETED,
    ):
        assert state.value.upper() in rendered


def test_renderer_includes_objectives():
    timeline = simulate_session(
        _profile_from_tags([_pattern_tag("perfectionism", tag_id="tag-1", sequence=0)])
    )
    rendered = render_session_timeline(timeline)

    assert "Objective:" in rendered
    assert "Practice flexibility and reduce performance-linked pressure." in rendered


def test_renderer_handles_empty_timeline_safely():
    empty_timeline = SessionTimeline(
        start_time="00:00:00",
        end_time="00:00:00",
        ordered_events=(),
    )

    rendered = render_session_timeline(empty_timeline)

    assert rendered == EMPTY_TIMELINE_TEXT
    assert "No session events are available yet." in rendered


def test_output_is_deterministic():
    profile = _profile_from_tags(
        [
            _pattern_tag("self_worth_instability", tag_id="tag-1", sequence=0),
            _pattern_tag("rumination", tag_id="tag-2", sequence=1),
        ]
    )

    first = render_session_timeline(simulate_session(profile))
    second = render_session_timeline(simulate_session(profile))

    assert first == second


def test_renderer_includes_expected_metadata_fields():
    timeline = simulate_session(
        _profile_from_tags([_pattern_tag("rumination", tag_id="tag-1", sequence=0)])
    )
    rendered = render_session_timeline(timeline)

    assert "Expected focus:" in rendered
    assert "Expected patterns:" in rendered
    assert "Expected emotions:" in rendered
    assert "rumination" in rendered
    assert "worry" in rendered
