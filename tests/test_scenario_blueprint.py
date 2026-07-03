from niros.human_profile_summary import build_human_profile_summary
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.scenario_blueprint import build_scenario_blueprint


def _pattern_tag(
    canonical_id: str,
    *,
    tag_id: str,
    sequence: int,
    confidence: float = 1.0,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-blueprint-001",
        evidence_id=f"session-blueprint-001:evidence:{sequence}",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def _profile_from_tags(tags: list[PatternTag]) -> dict:
    return build_human_profile_summary(tags)


def test_empty_profile_handled_safely():
    profile = _profile_from_tags([])
    blueprint = build_scenario_blueprint(profile)

    assert blueprint.opening_phase.objective
    assert blueprint.stabilization_phase.objective
    assert blueprint.exploration_phases == []
    assert blueprint.integration_phase.objective
    assert blueprint.closing_phase.objective
    assert blueprint.opening_phase.estimated_duration > 0


def test_rumination_profile_includes_acceptance_release_phase():
    profile = _profile_from_tags(
        [
            _pattern_tag("rumination", tag_id="tag-1", sequence=0),
        ]
    )

    blueprint = build_scenario_blueprint(profile)
    objectives = [phase.objective for phase in blueprint.exploration_phases]

    assert any("acceptance" in objective.lower() for objective in objectives)
    assert any(
        phase.target_patterns == ["rumination"]
        for phase in blueprint.exploration_phases
    )


def test_relationship_patterns_drive_relationship_exploration():
    profile = _profile_from_tags(
        [
            _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
            _pattern_tag("trust_difficulty", tag_id="tag-2", sequence=1),
        ]
    )

    blueprint = build_scenario_blueprint(profile)
    relationship_phases = [
        phase
        for phase in blueprint.exploration_phases
        if "relationship" in phase.objective.lower()
    ]

    assert len(relationship_phases) == 1
    assert set(relationship_phases[0].target_patterns) == {
        "attachment_anxiety",
        "trust_difficulty",
    }


def test_vulnerable_profile_includes_targeted_exploration_phases():
    profile = _profile_from_tags(
        [
            _pattern_tag("self_worth_instability", tag_id="tag-1", sequence=0),
            _pattern_tag("emotional_suppression", tag_id="tag-2", sequence=1),
            _pattern_tag("perfectionism", tag_id="tag-3", sequence=2),
        ]
    )

    blueprint = build_scenario_blueprint(profile)
    targeted_patterns = {
        pattern_id
        for phase in blueprint.exploration_phases
        for pattern_id in phase.target_patterns
    }

    assert "self_worth_instability" in targeted_patterns
    assert "emotional_suppression" in targeted_patterns
    assert "perfectionism" in targeted_patterns


def test_healthy_profile_differs_from_vulnerable_profile():
    healthy_profile = _profile_from_tags(
        [
            _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
        ]
    )
    vulnerable_profile = _profile_from_tags(
        [
            _pattern_tag("rumination", tag_id="tag-1", sequence=0),
            _pattern_tag("self_worth_instability", tag_id="tag-2", sequence=1),
        ]
    )

    healthy_blueprint = build_scenario_blueprint(healthy_profile)
    vulnerable_blueprint = build_scenario_blueprint(vulnerable_profile)

    assert (
        healthy_blueprint.opening_phase.objective
        != vulnerable_blueprint.opening_phase.objective
    )
    assert "strengths" in healthy_blueprint.opening_phase.objective.lower()
    assert healthy_blueprint.stabilization_phase.objective != (
        vulnerable_blueprint.stabilization_phase.objective
    )


def test_profile_drives_blueprint_content():
    rumination_profile = _profile_from_tags(
        [_pattern_tag("rumination", tag_id="tag-1", sequence=0)]
    )
    perfectionism_profile = _profile_from_tags(
        [_pattern_tag("perfectionism", tag_id="tag-1", sequence=0)]
    )

    rumination_blueprint = build_scenario_blueprint(rumination_profile)
    perfectionism_blueprint = build_scenario_blueprint(perfectionism_profile)

    rumination_objectives = [phase.objective for phase in rumination_blueprint.exploration_phases]
    perfectionism_objectives = [
        phase.objective for phase in perfectionism_blueprint.exploration_phases
    ]

    assert rumination_objectives != perfectionism_objectives
    assert any("acceptance" in objective.lower() for objective in rumination_objectives)
    assert any("flexibility" in objective.lower() for objective in perfectionism_objectives)


def test_output_is_deterministic():
    profile = _profile_from_tags(
        [
            _pattern_tag("attachment_anxiety", tag_id="tag-1", sequence=0),
            _pattern_tag("rumination", tag_id="tag-2", sequence=1),
            _pattern_tag("perfectionism", tag_id="tag-3", sequence=2),
        ]
    )

    first = build_scenario_blueprint(profile)
    second = build_scenario_blueprint(profile)

    assert first == second


def test_expected_phase_structure_present():
    profile = _profile_from_tags(
        [_pattern_tag("emotional_suppression", tag_id="tag-1", sequence=0)]
    )

    blueprint = build_scenario_blueprint(profile)

    assert blueprint.opening_phase.priority > 0
    assert blueprint.stabilization_phase.estimated_duration > 0
    assert len(blueprint.exploration_phases) >= 1
    assert blueprint.integration_phase.target_patterns == ["emotional_suppression"]
    assert blueprint.closing_phase.target_emotions
