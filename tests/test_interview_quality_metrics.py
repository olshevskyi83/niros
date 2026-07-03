from niros.human_profile_summary import build_human_profile_summary
from niros.interview_quality_metrics import calculate_interview_quality, empty_interview_state
from niros.models import InterviewPhase, InterviewState, SupportedLanguage
from niros.patterns import PatternTag


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str,
    sequence: int,
    confidence: float = 1.0,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-quality-001",
        evidence_id=f"session-quality-001:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def _profile_from_tags(tags: list[PatternTag]) -> dict:
    return build_human_profile_summary(tags)


def _interview_state(
    *,
    turn_count: int = 0,
    current_hypotheses: list[dict] | None = None,
) -> InterviewState:
    return InterviewState(
        session_id="session-quality-001",
        state=InterviewPhase.FREE_NARRATIVE,
        turn_count=turn_count,
        current_hypotheses=current_hypotheses or [],
    )


def test_empty_interview_has_low_score():
    profile = _profile_from_tags([])
    metrics = calculate_interview_quality(empty_interview_state(), profile)

    assert metrics.coverage_score == 0.0
    assert metrics.evidence_depth_score == 0.0
    assert metrics.confidence_score == 0.0
    assert metrics.repeated_topic_count == 0
    assert metrics.unresolved_hypotheses_count == 0
    assert metrics.overall_score == 0.0


def test_multi_domain_interview_has_higher_coverage():
    single_domain_tags = [
        _pattern_tag("people_pleasing", tag_id="tag-1", sequence=0),
    ]
    multi_domain_tags = [
        _pattern_tag("people_pleasing", tag_id="tag-1", sequence=0),
        _pattern_tag("perfectionism", tag_id="tag-2", sequence=1),
        _pattern_tag("emotional_suppression", tag_id="tag-3", sequence=2),
    ]

    single_domain_metrics = calculate_interview_quality(
        _interview_state(turn_count=3),
        _profile_from_tags(single_domain_tags),
    )
    multi_domain_metrics = calculate_interview_quality(
        _interview_state(turn_count=3),
        _profile_from_tags(multi_domain_tags),
    )

    assert single_domain_metrics.coverage_score == 1 / 3
    assert multi_domain_metrics.coverage_score == 1.0
    assert multi_domain_metrics.coverage_score > single_domain_metrics.coverage_score


def test_repeated_topics_reduce_score():
    unique_tags = [
        _pattern_tag("people_pleasing", tag_id="tag-1", sequence=0),
        _pattern_tag("shame_sensitivity", tag_id="tag-2", sequence=1),
    ]
    repeated_tags = [
        _pattern_tag("people_pleasing", tag_id="tag-1", sequence=0),
        _pattern_tag("people_pleasing", tag_id="tag-2", sequence=1),
        _pattern_tag("people_pleasing", tag_id="tag-3", sequence=2),
        _pattern_tag("shame_sensitivity", tag_id="tag-4", sequence=3),
    ]

    unique_metrics = calculate_interview_quality(
        _interview_state(turn_count=2),
        _profile_from_tags(unique_tags),
    )
    repeated_metrics = calculate_interview_quality(
        _interview_state(turn_count=4),
        _profile_from_tags(repeated_tags),
    )

    assert unique_metrics.repeated_topic_count == 0
    assert repeated_metrics.repeated_topic_count == 1
    assert repeated_metrics.overall_score < unique_metrics.overall_score


def test_unresolved_hypotheses_reduce_score():
    profile = _profile_from_tags(
        [
            _pattern_tag("conflict_avoidance", tag_id="tag-1", sequence=0),
            _pattern_tag("fear_of_disappointing_others", tag_id="tag-2", sequence=1),
        ]
    )
    resolved_state = _interview_state(
        turn_count=2,
        current_hypotheses=[
            {
                "canonical_id": "people_pleasing_pattern",
                "confidence": 0.65,
            }
        ],
    )
    unresolved_state = _interview_state(
        turn_count=2,
        current_hypotheses=[
            {
                "canonical_id": "people_pleasing_pattern",
                "confidence": 0.40,
            }
        ],
    )

    resolved_metrics = calculate_interview_quality(resolved_state, profile)
    unresolved_metrics = calculate_interview_quality(unresolved_state, profile)

    assert resolved_metrics.unresolved_hypotheses_count == 0
    assert unresolved_metrics.unresolved_hypotheses_count == 1
    assert unresolved_metrics.overall_score < resolved_metrics.overall_score


def test_stronger_evidence_increases_score():
    low_confidence_tags = [
        _pattern_tag("people_pleasing", tag_id="tag-1", sequence=0, confidence=0.4),
        _pattern_tag("shame_sensitivity", tag_id="tag-2", sequence=1, confidence=0.4),
    ]
    high_confidence_tags = [
        _pattern_tag("people_pleasing", tag_id="tag-1", sequence=0, confidence=1.0),
        _pattern_tag("shame_sensitivity", tag_id="tag-2", sequence=1, confidence=1.0),
    ]

    low_metrics = calculate_interview_quality(
        _interview_state(turn_count=2),
        _profile_from_tags(low_confidence_tags),
    )
    high_metrics = calculate_interview_quality(
        _interview_state(turn_count=2),
        _profile_from_tags(high_confidence_tags),
    )

    assert high_metrics.confidence_score > low_metrics.confidence_score
    assert high_metrics.overall_score > low_metrics.overall_score


def test_output_is_deterministic():
    tags = [
        _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
        _pattern_tag("attachment_anxiety", tag_id="tag-2", sequence=1),
        _pattern_tag("rumination", tag_id="tag-3", sequence=2),
    ]
    state = _interview_state(
        turn_count=3,
        current_hypotheses=[
            {"canonical_id": "people_pleasing_pattern", "confidence": 0.50},
        ],
    )
    profile = _profile_from_tags(tags)

    first = calculate_interview_quality(state, profile)
    second = calculate_interview_quality(state, profile)

    assert first == second


def test_evidence_depth_increases_with_multiple_references():
    shallow_tags = [
        _pattern_tag("people_pleasing", tag_id="tag-1", sequence=0),
    ]
    deep_tags = [
        _pattern_tag("people_pleasing", tag_id="tag-1", sequence=0),
        _pattern_tag("people_pleasing", tag_id="tag-2", sequence=1),
        _pattern_tag("people_pleasing", tag_id="tag-3", sequence=2),
    ]

    shallow_metrics = calculate_interview_quality(
        _interview_state(turn_count=1),
        _profile_from_tags(shallow_tags),
    )
    deep_metrics = calculate_interview_quality(
        _interview_state(turn_count=3),
        _profile_from_tags(deep_tags),
    )

    assert deep_metrics.evidence_depth_score > shallow_metrics.evidence_depth_score
