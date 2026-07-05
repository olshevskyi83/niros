"""Tests for Universal Therapeutic Pattern schema and seed library."""

from __future__ import annotations

import io
import json
from dataclasses import replace

import pytest

from niros.assessment import AssessmentResult
from niros.assessment_runner import neutral_answers_for_module, run_big_five_short_assessment
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    FingerprintCoverageAnalyzer,
)
from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.icaros_readiness import IcarosReadinessEvaluator, READINESS_READY
from niros.intervention_strategy import build_intervention_strategy
from niros.models import SupportedLanguage
from niros.pattern_person_fit import PatternPersonFitEvaluator, normalize_candidate_pattern
from niros.patterns import PatternTag
from niros.scenario_blueprint import build_scenario_blueprint
from niros.spirituality_worldview import (
    ORIENTATION_SECULAR_HUMANIST,
    SpiritualityWorldviewProfile,
    build_spirituality_worldview_profile,
)
from niros.therapeutic_pattern import (
    DEFAULT_SEED_LIBRARY_PATH,
    TherapeuticPattern,
    TherapeuticPatternLibrary,
    TherapeuticPatternValidationError,
)

VALID_PATTERN = {
    "id": "gentle_self_compassion_loop",
    "name": "Gentle Self-Compassion Loop",
    "psychological_function": ["self_compassion", "self_worth"],
    "good_for": ["shame", "self_criticism"],
    "avoid_if": ["psychosis_risk"],
    "language_style": ["gentle", "permission_based"],
    "rhythm": "slow_repetitive",
    "semantic_cluster": ["kindness", "safety"],
    "spiritual_compatibility": ["secular", "agnostic"],
    "requires_symbols": [],
    "forbidden_symbols": [],
    "intensity": "low",
    "directness": "low",
    "repetition_level": "medium",
    "safety_notes": ["Avoid strong identity claims"],
}


def test_pattern_model_accepts_valid_pattern():
    pattern = TherapeuticPattern.from_dict(VALID_PATTERN)

    assert pattern.id == "gentle_self_compassion_loop"
    assert pattern.name == "Gentle Self-Compassion Loop"
    assert pattern.intensity == "low"
    assert pattern.safety_notes == ("Avoid strong identity claims",)


def test_required_fields_are_enforced():
    payload = dict(VALID_PATTERN)
    del payload["safety_notes"]

    with pytest.raises(TherapeuticPatternValidationError, match="safety_notes"):
        TherapeuticPattern.from_dict(payload)


def test_seed_library_loads():
    library = TherapeuticPatternLibrary.load_seed()

    assert library.patterns
    assert len(library.patterns) == 7


def test_seed_library_loads_from_default_path():
    library = TherapeuticPatternLibrary.load_json(DEFAULT_SEED_LIBRARY_PATH)

    assert library.by_id("gentle_self_compassion_loop") is not None


def test_all_seed_patterns_have_ids():
    library = TherapeuticPatternLibrary.load_seed()

    assert all(pattern.id for pattern in library.patterns)


def test_seed_pattern_ids_are_unique():
    library = TherapeuticPatternLibrary.load_seed()

    assert len(library.ids()) == len(set(library.ids()))


@pytest.mark.parametrize(
    "field_name",
    [
        "psychological_function",
        "good_for",
        "avoid_if",
        "spiritual_compatibility",
        "safety_notes",
    ],
)
def test_each_seed_pattern_has_required_lists(field_name: str):
    library = TherapeuticPatternLibrary.load_seed()

    for pattern in library.patterns:
        assert getattr(pattern, field_name)


def test_pattern_to_dict_round_trip():
    pattern = TherapeuticPattern.from_dict(VALID_PATTERN)
    restored = TherapeuticPattern.from_dict(pattern.to_dict())

    assert restored == pattern


def test_library_rejects_duplicate_ids():
    duplicate_payloads = [VALID_PATTERN, dict(VALID_PATTERN)]

    with pytest.raises(TherapeuticPatternValidationError, match="Duplicate"):
        TherapeuticPatternLibrary.from_dicts(duplicate_payloads)


def _pattern_tag(canonical_id: str) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-tp-schema",
        evidence_id="session-tp-schema:evidence:0",
        canonical_id=canonical_id,
        matched_text=f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _ready_fit_context():
    intake = {
        "main_problem": "I feel ashamed and self-critical.",
        "duration": "months",
        "perceived_causes": "stress",
        "current_impact": "withdrawal",
        "previous_attempts": "journaling",
        "desired_outcome": "feel steadier",
    }
    tags = [_pattern_tag("shame_sensitivity"), _pattern_tag("harsh_self_criticism")]
    completed = {
        "big-five-short": run_big_five_short_assessment(
            language="en",
            output_stream=io.StringIO(),
            answers=neutral_answers_for_module("big-five-short"),
            print_output=False,
        ),
        "self-domain-short": [
            AssessmentResult(
                domain_id="self_domain",
                score=3.0,
                normalized_score=0.6,
                interpretation="Moderate self-domain signal.",
                fingerprint_dimension="self_domain",
            )
        ],
        "emotion-regulation-domain-short": [
            AssessmentResult(
                domain_id="emotion_regulation_domain",
                score=3.0,
                normalized_score=0.6,
                interpretation="Moderate emotion regulation signal.",
                fingerprint_dimension="emotion_regulation_domain",
            )
        ],
        "values-identity-domain-short": [
            AssessmentResult(
                domain_id="values_identity_domain",
                score=3.0,
                normalized_score=0.6,
                interpretation="Moderate values signal.",
                fingerprint_dimension="values_identity_domain",
            )
        ],
        "meaning-purpose-short": [
            AssessmentResult(
                domain_id="meaning",
                score=3.0,
                normalized_score=0.6,
                interpretation="Moderate meaning signal.",
                fingerprint_dimension="meaning",
            )
        ],
    }
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem=intake,
        patterns=tags,
        completed_assessments=completed,
    )
    for domain_id in (
        "self_domain",
        "emotion_regulation_domain",
        "values_identity_domain",
        "meaning",
        "presenting_problem",
        "patterns",
        "big_five",
        "cognitive_patterns_domain",
        "emotional_flexibility_domain",
        "relationships_domain",
    ):
        domain = coverage.domains[domain_id]
        coverage.domains[domain_id] = domain.__class__(
            domain_id=domain_id,
            coverage=1.0,
            confidence=1.0,
            level=COVERAGE_LEVEL_COMPLETE,
        )
    worldview = replace(
        build_spirituality_worldview_profile(presenting_problem=intake),
        worldview_orientation=ORIENTATION_SECULAR_HUMANIST,
    )
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=tags,
        presenting_problem=intake,
        assessment_results=[
            result for module_results in completed.values() for result in module_results
        ],
    )
    fingerprint = {**fingerprint, "spirituality_worldview": worldview.to_dict()}
    strategy = build_intervention_strategy(fingerprint, fingerprint_coverage_report=coverage)
    blueprint = build_scenario_blueprint(fingerprint["patterns"], intervention_strategy=strategy)
    readiness = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    readiness = replace(
        readiness,
        readiness_level=READINESS_READY,
        ready=True,
        overall_readiness=90,
    )
    return fingerprint, coverage, strategy, blueprint, readiness, worldview


def test_pattern_person_fit_accepts_schema_objects():
    fingerprint, coverage, strategy, blueprint, readiness, worldview = _ready_fit_context()
    library = TherapeuticPatternLibrary.load_seed()
    evaluator = PatternPersonFitEvaluator()

    result = evaluator.evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=worldview,
        candidate_patterns=library.patterns,
    )

    assert result.selected_patterns
    assert any(item.id == "gentle_self_compassion_loop" for item in result.selected_patterns)


def test_normalize_candidate_pattern_accepts_dict_and_object():
    library = TherapeuticPatternLibrary.load_seed()
    pattern = library.by_id("grounding_body_safety_loop")
    assert pattern is not None

    from_object = normalize_candidate_pattern(pattern)
    from_dict = normalize_candidate_pattern(pattern.to_dict())

    assert from_object.id == from_dict.id == pattern.id
    assert from_object.safety_notes == pattern.safety_notes


def test_pattern_person_fit_output_is_deterministic_with_seed_library():
    fingerprint, coverage, strategy, blueprint, readiness, worldview = _ready_fit_context()
    library = TherapeuticPatternLibrary.load_seed()
    evaluator = PatternPersonFitEvaluator()

    first = evaluator.evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=worldview,
        candidate_patterns=library.patterns,
    )
    second = evaluator.evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=worldview,
        candidate_patterns=library.patterns,
    )

    assert first == second
    assert first.to_dict() == second.to_dict()
