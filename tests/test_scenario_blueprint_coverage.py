import re

from niros.fingerprint_coverage import FingerprintCoverageAnalyzer
from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.human_profile_summary import build_human_profile_summary
from niros.intervention_strategy import (
    STRATEGY_CONFIDENCE_HIGH,
    STRATEGY_CONFIDENCE_LOW,
    STRATEGY_CONFIDENCE_MEDIUM,
    build_intervention_strategy,
)
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.scenario_blueprint import (
    DEFAULT_SCENARIO_FRAMING,
    build_scenario_blueprint,
    render_scenario_blueprint,
)
from niros.semantic_interpreter.facts import SemanticFact

DIAGNOSIS_PATTERN = re.compile(
    r"\b(diagnos(is|e|ed|ing)?|disorder|patholog|clinical syndrome|bipolar|"
    r"ptsd|narcissistic personality|borderline personality)\b",
    re.IGNORECASE,
)


def _pattern_tag(canonical_id: str) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-blueprint-coverage",
        evidence_id="session-blueprint-coverage:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _full_intake() -> dict[str, str]:
    return {
        "main_problem": "feeling disconnected after loss",
        "duration": "months",
        "perceived_causes": "grief",
        "current_impact": "withdrawal",
        "previous_attempts": "talking with friends",
        "desired_outcome": "feel more like myself",
    }


def _profile(pattern_ids: list[str]) -> dict:
    return build_human_profile_summary([_pattern_tag(pattern_id) for pattern_id in pattern_ids])


def _strategy_with_coverage(pattern_ids: list[str]):
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem=_full_intake(),
        patterns=[_pattern_tag(pattern_id) for pattern_id in pattern_ids],
    )
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[_pattern_tag(pattern_id) for pattern_id in pattern_ids],
        presenting_problem=_full_intake(),
    )
    return build_intervention_strategy(fingerprint, fingerprint_coverage_report=coverage)


def test_blueprint_accepts_coverage_aware_strategy():
    strategy = _strategy_with_coverage(["social_withdrawal"])
    blueprint = build_scenario_blueprint(
        _profile(["social_withdrawal"]),
        intervention_strategy=strategy,
    )

    assert blueprint.confidence_phases
    assert blueprint.confidence_summary is not None
    assert blueprint.opening_phase.objective


def test_high_confidence_areas_produce_direct_framing():
    strategy = _strategy_with_coverage(["social_withdrawal"])
    blueprint = build_scenario_blueprint(
        _profile(["social_withdrawal"]),
        intervention_strategy=strategy,
    )

    high_phases = [
        phase for phase in blueprint.confidence_phases if phase.confidence == STRATEGY_CONFIDENCE_HIGH
    ]
    assert high_phases
    for phase in high_phases:
        assert phase.framing == DEFAULT_SCENARIO_FRAMING[STRATEGY_CONFIDENCE_HIGH]


def test_medium_confidence_self_area_produces_gentle_framing():
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={"main_problem": "I feel useless"},
        patterns=[_pattern_tag("shame_sensitivity"), _pattern_tag("social_withdrawal")],
        semantic_facts=[
            SemanticFact(
                category="self",
                attribute="unworthiness",
                value="present",
                evidence="useless",
            ),
            SemanticFact(
                category="self",
                attribute="self_criticism",
                value="present",
                evidence="harsh",
            ),
        ],
    )
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[_pattern_tag("shame_sensitivity"), _pattern_tag("social_withdrawal")],
        presenting_problem={"main_problem": "I feel useless"},
    )
    strategy = build_intervention_strategy(fingerprint, fingerprint_coverage_report=coverage)
    blueprint = build_scenario_blueprint(
        _profile(["shame_sensitivity", "social_withdrawal"]),
        intervention_strategy=strategy,
    )

    self_phase = next(
        phase
        for phase in blueprint.confidence_phases
        if phase.focus == "self-worth / self-criticism"
    )
    assert self_phase.confidence == STRATEGY_CONFIDENCE_LOW
    assert "open-ended" in self_phase.framing.lower()


def test_partial_self_domain_uses_medium_framing_when_confidence_is_medium():
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem={"main_problem": "I feel useless"},
        patterns=[_pattern_tag("shame_sensitivity")],
        semantic_facts=[
            SemanticFact(
                category="self",
                attribute="unworthiness",
                value="present",
                evidence="useless",
            ),
            SemanticFact(
                category="self",
                attribute="self_criticism",
                value="present",
                evidence="harsh",
            ),
        ],
    )
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[_pattern_tag("shame_sensitivity")],
        presenting_problem={"main_problem": "I feel useless"},
    )
    strategy = build_intervention_strategy(fingerprint, fingerprint_coverage_report=coverage)
    blueprint = build_scenario_blueprint(
        _profile(["shame_sensitivity"]),
        intervention_strategy=strategy,
    )

    self_phase = next(
        phase
        for phase in blueprint.confidence_phases
        if phase.focus == "self-worth / self-criticism"
    )
    if self_phase.confidence == STRATEGY_CONFIDENCE_MEDIUM:
        assert "gentle exploratory language" in self_phase.framing.lower()


def test_low_confidence_areas_produce_exploratory_framing():
    strategy = _strategy_with_coverage(["social_withdrawal"])
    blueprint = build_scenario_blueprint(
        _profile(["social_withdrawal"]),
        intervention_strategy=strategy,
    )

    emotion_phase = next(
        phase for phase in blueprint.confidence_phases if phase.focus == "emotion regulation"
    )
    assert emotion_phase.confidence == STRATEGY_CONFIDENCE_LOW
    assert "exploratory" in emotion_phase.framing.lower() or "stabilization" in emotion_phase.framing.lower()


def test_uncertainty_notes_are_preserved():
    strategy = _strategy_with_coverage(["social_withdrawal"])
    blueprint = build_scenario_blueprint(
        _profile(["social_withdrawal"]),
        intervention_strategy=strategy,
    )
    rendered = render_scenario_blueprint(blueprint)

    strategy_self = next(
        item for item in strategy.focus_confidence if item.focus_area == "self-worth / self-criticism"
    )
    blueprint_self = next(
        phase for phase in blueprint.confidence_phases if phase.focus == "self-worth / self-criticism"
    )

    assert blueprint_self.uncertainty_notes == strategy_self.uncertainty_notes
    for note in blueprint_self.uncertainty_notes:
        assert note in rendered


def test_source_domains_are_included():
    strategy = _strategy_with_coverage(["social_withdrawal"])
    blueprint = build_scenario_blueprint(
        _profile(["social_withdrawal"]),
        intervention_strategy=strategy,
    )
    rendered = render_scenario_blueprint(blueprint)

    self_phase = next(
        phase for phase in blueprint.confidence_phases if phase.focus == "self-worth / self-criticism"
    )
    assert self_phase.source_domains
    assert "Source domains:" in rendered
    assert self_phase.source_domains[0] in rendered


def test_rendered_blueprint_includes_confidence_summary():
    strategy = _strategy_with_coverage(["social_withdrawal"])
    blueprint = build_scenario_blueprint(
        _profile(["social_withdrawal"]),
        intervention_strategy=strategy,
    )
    rendered = render_scenario_blueprint(blueprint)

    assert "Scenario Confidence Summary" in rendered
    assert "Direct personalization:" in rendered
    assert "Gentle personalization:" in rendered
    assert "Exploratory only:" in rendered
    assert "Confidence-aware scenario themes:" in rendered


def test_rendered_blueprint_avoids_diagnosis_language():
    strategy = _strategy_with_coverage(["rumination", "shame_sensitivity"])
    blueprint = build_scenario_blueprint(
        _profile(["rumination", "shame_sensitivity"]),
        intervention_strategy=strategy,
    )
    rendered = render_scenario_blueprint(blueprint)

    assert DIAGNOSIS_PATTERN.search(rendered) is None


def test_build_scenario_blueprint_with_coverage_is_deterministic():
    strategy = _strategy_with_coverage(["social_withdrawal", "rumination"])
    profile = _profile(["social_withdrawal", "rumination"])

    first = build_scenario_blueprint(profile, intervention_strategy=strategy)
    second = build_scenario_blueprint(profile, intervention_strategy=strategy)

    assert first == second
    assert render_scenario_blueprint(first) == render_scenario_blueprint(second)


def test_existing_blueprint_behavior_remains_backward_compatible():
    profile = _profile(["rumination"])
    baseline = build_scenario_blueprint(profile)
    rendered = render_scenario_blueprint(baseline)

    assert baseline.confidence_phases == ()
    assert baseline.confidence_summary is None
    assert baseline.exploration_phases
    assert "Scenario Confidence Summary" not in rendered
    assert baseline.opening_phase.objective
