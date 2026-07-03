from niros.human_profile_summary import build_human_profile_summary
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.scenario_blueprint import build_scenario_blueprint
from niros.scenario_script_skeleton import build_scenario_script_skeleton
from niros.session_engine import SessionEngine, SessionState


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str,
    sequence: int,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-engine-001",
        evidence_id=f"session-engine-001:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _skeleton_from_tags(tags: list[PatternTag]):
    profile = build_human_profile_summary(tags)
    blueprint = build_scenario_blueprint(profile)
    return build_scenario_script_skeleton(blueprint)


def _run_session(engine: SessionEngine) -> list[SessionState]:
    states: list[SessionState] = [engine.start_session().current_state]
    while not engine.is_complete():
        states.append(engine.advance_state().current_state)
    return states


def test_correct_initial_state():
    skeleton = _skeleton_from_tags([])
    engine = SessionEngine(skeleton)

    context = engine.start_session()

    assert context.current_state == SessionState.PREPARATION
    assert engine.current_state() == SessionState.PREPARATION
    assert context.current_segment is None
    assert context.completed_segments == ()
    assert len(context.remaining_segments) == len(skeleton.segments)
    assert context.elapsed_time == 0
    assert engine.is_complete() is False


def test_correct_transitions_for_empty_skeleton():
    skeleton = _skeleton_from_tags([])
    engine = SessionEngine(skeleton)

    states = _run_session(engine)

    assert states == [
        SessionState.PREPARATION,
        SessionState.OPENING,
        SessionState.STABILIZATION,
        SessionState.INTEGRATION,
        SessionState.CLOSING,
        SessionState.COMPLETED,
    ]


def test_no_skipped_segment_states():
    skeleton = _skeleton_from_tags(
        [
            _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
            _pattern_tag("rumination", tag_id="tag-2", sequence=1),
            _pattern_tag("perfectionism", tag_id="tag-3", sequence=2),
        ]
    )
    engine = SessionEngine(skeleton)
    states = _run_session(engine)

    assert states == [
        SessionState.PREPARATION,
        SessionState.OPENING,
        SessionState.STABILIZATION,
        SessionState.EXPLORATION,
        SessionState.DEEP_EXPLORATION,
        SessionState.DEEP_EXPLORATION,
        SessionState.INTEGRATION,
        SessionState.CLOSING,
        SessionState.COMPLETED,
    ]


def test_single_exploration_uses_exploration_not_deep_exploration():
    skeleton = _skeleton_from_tags(
        [_pattern_tag("rumination", tag_id="tag-1", sequence=0)]
    )
    engine = SessionEngine(skeleton)
    states = _run_session(engine)

    assert SessionState.EXPLORATION in states
    assert SessionState.DEEP_EXPLORATION not in states


def test_completion_detected():
    skeleton = _skeleton_from_tags(
        [_pattern_tag("emotional_suppression", tag_id="tag-1", sequence=0)]
    )
    engine = SessionEngine(skeleton)
    engine.start_session()

    while not engine.is_complete():
        engine.advance_state()

    context = engine.context()

    assert context.current_state == SessionState.COMPLETED
    assert context.current_segment is None
    assert context.remaining_segments == ()
    assert len(context.completed_segments) == len(skeleton.segments)
    assert context.elapsed_time == skeleton.total_estimated_duration


def test_completed_segments_and_remaining_segments_track_progress():
    skeleton = _skeleton_from_tags([])
    engine = SessionEngine(skeleton)
    engine.start_session()

    context = engine.advance_state()
    assert context.current_state == SessionState.OPENING
    assert context.current_segment == skeleton.segments[0]
    assert context.completed_segments == ()
    assert context.remaining_segments == tuple(skeleton.segments[1:])

    context = engine.advance_state()
    assert context.current_state == SessionState.STABILIZATION
    assert context.completed_segments == (skeleton.segments[0],)
    assert context.current_segment == skeleton.segments[1]
    assert context.elapsed_time == skeleton.segments[0].estimated_duration


def test_output_is_deterministic():
    skeleton = _skeleton_from_tags(
        [
            _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
            _pattern_tag("rumination", tag_id="tag-2", sequence=1),
        ]
    )

    first_states = _run_session(SessionEngine(skeleton))
    second_states = _run_session(SessionEngine(skeleton))

    assert first_states == second_states


def test_advance_after_complete_is_idempotent():
    skeleton = _skeleton_from_tags([])
    engine = SessionEngine(skeleton)
    _run_session(engine)

    before = engine.context()
    after = engine.advance_state()

    assert after == before
    assert engine.is_complete() is True
