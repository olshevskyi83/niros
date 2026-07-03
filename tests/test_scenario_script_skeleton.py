import re

from niros.human_profile_summary import build_human_profile_summary
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.scenario_blueprint import ScenarioBlueprint, ScenarioPhase, build_scenario_blueprint
from niros.scenario_script_skeleton import build_scenario_script_skeleton


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str,
    sequence: int,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-skeleton-001",
        evidence_id=f"session-skeleton-001:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _blueprint_from_tags(tags: list[PatternTag]):
    profile = build_human_profile_summary(tags)
    return build_scenario_blueprint(profile)


def _empty_blueprint() -> ScenarioBlueprint:
    return build_scenario_blueprint(build_human_profile_summary([]))


ICARO_OR_LYRICS_PATTERN = re.compile(
    r"\b(icaro|lyric|verse|chorus|melody line)\b",
    re.IGNORECASE,
)


def test_empty_blueprint_handled_safely():
    skeleton = build_scenario_script_skeleton(_empty_blueprint())

    assert skeleton.title == "General Therapeutic Session Skeleton"
    assert skeleton.total_estimated_duration > 0
    assert len(skeleton.segments) == 4
    assert [segment.phase_name for segment in skeleton.segments] == [
        "opening",
        "stabilization",
        "integration",
        "closing",
    ]


def test_all_blueprint_phases_become_segments():
    blueprint = _blueprint_from_tags(
        [
            _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
            _pattern_tag("rumination", tag_id="tag-2", sequence=1),
        ]
    )

    skeleton = build_scenario_script_skeleton(blueprint)
    phase_names = [segment.phase_name for segment in skeleton.segments]

    assert phase_names[0] == "opening"
    assert phase_names[1] == "stabilization"
    assert phase_names[-2] == "integration"
    assert phase_names[-1] == "closing"
    assert any(name.startswith("exploration") for name in phase_names)
    assert len(skeleton.segments) == 2 + len(blueprint.exploration_phases) + 2


def test_high_priority_phase_increases_intensity():
    high_priority_blueprint = ScenarioBlueprint(
        opening_phase=ScenarioPhase(objective="open", estimated_duration=8, priority=1),
        stabilization_phase=ScenarioPhase(objective="stabilize", estimated_duration=10, priority=1),
        exploration_phases=[
            ScenarioPhase(
                objective="explore relationships",
                target_patterns=["attachment_anxiety"],
                estimated_duration=14,
                priority=1,
            )
        ],
        integration_phase=ScenarioPhase(objective="integrate", estimated_duration=8, priority=2),
        closing_phase=ScenarioPhase(objective="close", estimated_duration=5, priority=1),
    )
    lower_priority_blueprint = ScenarioBlueprint(
        opening_phase=ScenarioPhase(objective="open", estimated_duration=8, priority=1),
        stabilization_phase=ScenarioPhase(objective="stabilize", estimated_duration=10, priority=1),
        exploration_phases=[
            ScenarioPhase(
                objective="explore rumination",
                target_patterns=["rumination"],
                estimated_duration=10,
                priority=3,
            )
        ],
        integration_phase=ScenarioPhase(objective="integrate", estimated_duration=8, priority=2),
        closing_phase=ScenarioPhase(objective="close", estimated_duration=5, priority=1),
    )

    high_priority_segment = build_scenario_script_skeleton(
        high_priority_blueprint
    ).segments[2]
    lower_priority_segment = build_scenario_script_skeleton(
        lower_priority_blueprint
    ).segments[2]

    assert high_priority_segment.intensity == "medium_to_high"
    assert lower_priority_segment.intensity == "medium_to_low"
    assert high_priority_segment.intensity != lower_priority_segment.intensity


def test_target_patterns_influence_musical_direction():
    rumination_skeleton = build_scenario_script_skeleton(
        _blueprint_from_tags([_pattern_tag("rumination", tag_id="tag-1", sequence=0)])
    )
    self_worth_skeleton = build_scenario_script_skeleton(
        _blueprint_from_tags(
            [_pattern_tag("self_worth_instability", tag_id="tag-1", sequence=0)]
        )
    )
    relationship_skeleton = build_scenario_script_skeleton(
        _blueprint_from_tags(
            [_pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0)]
        )
    )
    perfectionism_skeleton = build_scenario_script_skeleton(
        _blueprint_from_tags([_pattern_tag("perfectionism", tag_id="tag-1", sequence=0)])
    )

    rumination_segment = next(
        segment
        for segment in rumination_skeleton.segments
        if segment.phase_name.startswith("exploration")
    )
    self_worth_segment = next(
        segment
        for segment in self_worth_skeleton.segments
        if segment.phase_name.startswith("exploration")
    )
    relationship_segment = next(
        segment
        for segment in relationship_skeleton.segments
        if segment.phase_name.startswith("exploration")
    )
    perfectionism_segment = next(
        segment
        for segment in perfectionism_skeleton.segments
        if segment.phase_name.startswith("exploration")
    )

    assert rumination_segment.musical_direction == "spacious / repetitive / releasing"
    assert self_worth_segment.musical_direction == "compassionate / warm"
    assert relationship_segment.musical_direction == "holding / relational"
    assert perfectionism_segment.musical_direction == "flexible / fluid"


def test_no_final_lyrics_or_icaros_text_generated():
    blueprint = _blueprint_from_tags(
        [
            _pattern_tag("emotional_suppression", tag_id="tag-1", sequence=0),
            _pattern_tag("perfectionism", tag_id="tag-2", sequence=1),
        ]
    )
    skeleton = build_scenario_script_skeleton(blueprint)

    serialized = " ".join(
        [
            skeleton.title,
            *(
                field
                for segment in skeleton.segments
                for field in (
                    segment.phase_name,
                    segment.objective,
                    segment.intensity,
                    segment.musical_direction,
                    segment.vocal_direction,
                    segment.silence_ratio,
                    segment.transition_notes,
                )
            ),
        ]
    )

    assert ICARO_OR_LYRICS_PATTERN.search(serialized) is None


def test_output_is_deterministic():
    blueprint = _blueprint_from_tags(
        [
            _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
            _pattern_tag("rumination", tag_id="tag-2", sequence=1),
            _pattern_tag("perfectionism", tag_id="tag-3", sequence=2),
        ]
    )

    first = build_scenario_script_skeleton(blueprint)
    second = build_scenario_script_skeleton(blueprint)

    assert first == second


def test_total_duration_matches_segment_sum():
    skeleton = build_scenario_script_skeleton(_empty_blueprint())

    assert skeleton.total_estimated_duration == sum(
        segment.estimated_duration for segment in skeleton.segments
    )


def test_opening_and_closing_segment_directions():
    skeleton = build_scenario_script_skeleton(_empty_blueprint())

    opening = skeleton.segments[0]
    closing = skeleton.segments[-1]

    assert opening.intensity == "low"
    assert opening.musical_direction == "grounding"
    assert opening.vocal_direction == "soft / invitational"
    assert opening.silence_ratio == "high"

    assert closing.intensity == "low"
    assert closing.musical_direction == "grounding / settling"
    assert closing.vocal_direction == "minimal"
    assert closing.silence_ratio == "high"
