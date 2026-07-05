"""Tests for the Icaros readiness gate."""

from __future__ import annotations

import io

from dataclasses import replace

import pytest

from niros.assessment import AssessmentResult
from niros.assessment_runner import (
    AssessedModuleRun,
    neutral_answers_for_module,
    run_big_five_short_assessment,
)
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_PARTIAL,
    COVERAGE_LEVEL_UNKNOWN,
    FingerprintCoverageAnalyzer,
)
from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.human_profile_report import (
    build_human_profile_report_from_tags,
    render_human_profile_report,
)
from niros.icaros_readiness import (
    IcarosReadinessEvaluator,
    READINESS_NOT_READY,
    READINESS_PARTIALLY_READY,
    READINESS_READY,
    READINESS_READY_WITH_LIMITATIONS,
    SPIRITUAL_ORIENTATION_ATHEIST,
    SPIRITUAL_ORIENTATION_CHRISTIAN,
    SPIRITUAL_ORIENTATION_RELIGION_AVERSE,
    SPIRITUAL_ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
    render_icaros_readiness_section,
)
from niros.intervention_strategy import (
    STRATEGY_CONFIDENCE_HIGH,
    STRATEGY_CONFIDENCE_LOW,
    STRATEGY_CONFIDENCE_MEDIUM,
    build_intervention_strategy,
)
from niros.models import SupportedLanguage
from niros.patterns import PatternTag
from niros.scenario_blueprint import build_scenario_blueprint
from niros.semantic_interpreter.facts import SemanticFact


def _pattern_tag(canonical_id: str, matched_text: str | None = None) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-icaros-readiness",
        evidence_id="session-icaros-readiness:evidence:0",
        canonical_id=canonical_id,
        matched_text=matched_text or f"evidence for {canonical_id}",
        confidence=1.0,
        language=SupportedLanguage.ENGLISH,
    )


def _full_intake() -> dict[str, str]:
    return {
        "main_problem": "I feel ashamed and disconnected after loss.",
        "duration": "months",
        "perceived_causes": "grief and self-criticism",
        "current_impact": "withdrawal and low mood",
        "previous_attempts": "talking with friends",
        "desired_outcome": "feel more like myself",
    }


def _completed_big_five() -> dict[str, list[AssessmentResult]]:
    results = run_big_five_short_assessment(
        language="en",
        output_stream=io.StringIO(),
        answers=neutral_answers_for_module("big-five-short"),
        print_output=False,
    )
    return {"big-five-short": results}


def _build_ready_context(
    pattern_ids: list[str],
    *,
    semantic_facts: list[SemanticFact] | None = None,
    completed_assessments: dict[str, list[AssessmentResult]] | None = None,
):
    tags = [_pattern_tag(pattern_id) for pattern_id in pattern_ids]
    completed = completed_assessments or _completed_big_five()
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem=_full_intake(),
        patterns=tags,
        semantic_facts=semantic_facts,
        completed_assessments=completed,
    )
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=tags,
        presenting_problem=_full_intake(),
        semantic_facts=semantic_facts,
        assessment_results=[
            result
            for module_results in completed.values()
            for result in module_results
        ],
    )
    strategy = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=coverage,
    )
    profile = fingerprint["patterns"]
    blueprint = build_scenario_blueprint(profile, intervention_strategy=strategy)
    return fingerprint, coverage, strategy, blueprint, completed


def test_ready_profile_can_reach_high_readiness():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        [
            "spiritual_openness",
            "meaning_seeking",
            "shame_sensitivity",
            "harsh_self_criticism",
            "emotional_suppression",
        ],
        semantic_facts=[
            SemanticFact(
                category="meaning",
                attribute="meaning_sense",
                value="seeking",
                evidence="searching for meaning",
            ),
            SemanticFact(
                category="session",
                attribute="session_openness",
                value="open",
                evidence="open to symbolic language",
            ),
        ],
        completed_assessments={
            **_completed_big_five(),
            "self-domain-short": [
                AssessmentResult(
                    domain_id="self_domain",
                    score=3.0,
                    normalized_score=0.6,
                    interpretation="Moderate self-domain signal.",
                    fingerprint_dimension="self_domain",
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
            "emotion-regulation-domain-short": [
                AssessmentResult(
                    domain_id="emotion_regulation_domain",
                    score=3.0,
                    normalized_score=0.6,
                    interpretation="Moderate emotion regulation signal.",
                    fingerprint_dimension="emotion_regulation_domain",
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
        },
    )

    for domain_id in (
        "self_domain",
        "emotion_regulation_domain",
        "values_identity_domain",
        "meaning",
        "presenting_problem",
        "patterns",
        "big_five",
    ):
        domain = coverage.domains[domain_id]
        coverage.domains[domain_id] = domain.__class__(
            domain_id=domain_id,
            coverage=1.0,
            confidence=1.0,
            level="complete",
        )
    coverage.missing_domains = [
        domain_id
        for domain_id in coverage.missing_domains
        if domain_id
        not in {
            "self_domain",
            "emotion_regulation_domain",
            "values_identity_domain",
            "meaning",
            "big_five",
        }
    ]
    strategy = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=coverage,
    )
    blueprint = build_scenario_blueprint(fingerprint["patterns"], intervention_strategy=strategy)

    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )

    assert result.overall_readiness >= 85
    assert result.ready is True
    assert result.confidence == "high"
    assert result.readiness_level == READINESS_READY
    assert not result.blocking_domains


def test_unknown_self_domain_blocks_readiness():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        ["social_withdrawal"],
    )
    coverage.domains["self_domain"] = coverage.domains["self_domain"].__class__(
        domain_id="self_domain",
        coverage=0.0,
        confidence=0.0,
        level=COVERAGE_LEVEL_UNKNOWN,
    )
    if "self_domain" not in coverage.missing_domains:
        coverage.missing_domains.append("self_domain")

    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )

    assert result.overall_readiness <= 39
    assert result.ready is False
    assert "self_domain" in result.blocking_domains
    assert result.readiness_level == READINESS_NOT_READY
    assert any("Self domain" in warning for warning in result.warnings)


def test_unknown_spiritual_orientation_limits_readiness():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        ["shame_sensitivity", "harsh_self_criticism"],
    )

    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )

    assert result.overall_readiness <= 84
    assert result.ready is False
    assert "spiritual_orientation" in result.missing_information
    assert any("symbolic language" in warning.lower() for warning in result.warnings)
    assert result.readiness_level in {
        READINESS_READY_WITH_LIMITATIONS,
        READINESS_PARTIALLY_READY,
        READINESS_NOT_READY,
    }


def test_unknown_values_identity_limits_readiness():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        ["spiritual_openness", "meaning_seeking"],
        semantic_facts=[
            SemanticFact(
                category="session",
                attribute="session_openness",
                value="open",
                evidence="open to inner work",
            )
        ],
    )
    coverage.domains["values_identity_domain"] = coverage.domains["values_identity_domain"].__class__(
        domain_id="values_identity_domain",
        coverage=0.0,
        confidence=0.0,
        level=COVERAGE_LEVEL_UNKNOWN,
    )

    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )

    assert result.overall_readiness <= 84
    assert any("Identity domain" in warning for warning in result.warnings)


def test_low_profile_confidence_blocks_readiness():
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=[],
        presenting_problem=_full_intake(),
    )
    coverage = FingerprintCoverageAnalyzer().analyze(
        presenting_problem=_full_intake(),
        patterns=[],
    )
    strategy = build_intervention_strategy(fingerprint, fingerprint_coverage_report=coverage)
    blueprint = build_scenario_blueprint(fingerprint["patterns"], intervention_strategy=strategy)

    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
    )

    assert result.ready is False
    assert "human_profile" in result.blocking_domains
    assert result.overall_readiness <= 39


def test_multiple_critical_unknown_domains_block_readiness():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        ["social_withdrawal"],
    )
    for domain_id in ("self_domain", "values_identity_domain"):
        coverage.domains[domain_id] = coverage.domains[domain_id].__class__(
            domain_id=domain_id,
            coverage=0.0,
            confidence=0.0,
            level=COVERAGE_LEVEL_UNKNOWN,
        )

    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )

    assert "multiple_critical_domains" in result.blocking_domains
    assert result.overall_readiness <= 39


def test_strategy_low_self_confidence_reduces_readiness():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        ["spiritual_openness", "meaning_seeking", "shame_sensitivity"],
        semantic_facts=[
            SemanticFact(
                category="session",
                attribute="session_openness",
                value="open",
                evidence="open",
            )
        ],
    )

    low_self_strategy = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=coverage,
    )
    adjusted_focus = tuple(
        replace(item, confidence=STRATEGY_CONFIDENCE_LOW)
        if item.focus_area == "self-worth / self-criticism"
        else item
        for item in low_self_strategy.focus_confidence
    )
    low_self_strategy = replace(low_self_strategy, focus_confidence=adjusted_focus)

    strong = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    weaker = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=low_self_strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )

    assert weaker.overall_readiness <= strong.overall_readiness


def test_scenario_exploratory_only_reduces_readiness():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        ["spiritual_openness", "meaning_seeking"],
        semantic_facts=[
            SemanticFact(
                category="session",
                attribute="session_openness",
                value="open",
                evidence="open",
            )
        ],
    )

    with_blueprint = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    without_blueprint = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=None,
        completed_assessments=completed,
    )

    assert with_blueprint.overall_readiness >= without_blueprint.overall_readiness


@pytest.mark.parametrize(
    ("pattern_ids", "semantic_facts", "expected_orientation"),
    [
        (
            ["spiritual_resistance"],
            [],
            SPIRITUAL_ORIENTATION_RELIGION_AVERSE,
        ),
        (
            ["spiritual_openness", "meaning_seeking"],
            [],
            SPIRITUAL_ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
        ),
        (
            [],
            [
                SemanticFact(
                    category="meaning",
                    attribute="meaning_sense",
                    value="seeking",
                    evidence="I am Christian and pray often",
                )
            ],
            SPIRITUAL_ORIENTATION_CHRISTIAN,
        ),
        (
            [],
            [
                SemanticFact(
                    category="meaning",
                    attribute="meaning_sense",
                    value="seeking",
                    evidence="I am an atheist",
                )
            ],
            SPIRITUAL_ORIENTATION_ATHEIST,
        ),
    ],
)
def test_spiritual_adaptation_inference(
    pattern_ids: list[str],
    semantic_facts: list[SemanticFact],
    expected_orientation: str,
):
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        pattern_ids,
        semantic_facts=semantic_facts,
    )
    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )

    assert result.spiritual_orientation == expected_orientation
    if expected_orientation == SPIRITUAL_ORIENTATION_ATHEIST:
        assert result.recommended_symbolic_style["religious"] == "avoid"
    if expected_orientation == SPIRITUAL_ORIENTATION_CHRISTIAN:
        assert result.recommended_symbolic_style["religious"] == "preferred"
    if expected_orientation == SPIRITUAL_ORIENTATION_RELIGION_AVERSE:
        assert result.recommended_symbolic_style["religious"] == "avoid"


def test_language_and_symbol_recommendations_are_structured():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        ["spiritual_openness", "meaning_seeking", "shame_sensitivity"],
        semantic_facts=[
            SemanticFact(
                category="session",
                attribute="session_openness",
                value="open",
                evidence="open",
            )
        ],
    )
    result = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )

    assert set(result.recommended_language_style) >= {
        "directness",
        "metaphor",
        "repetition",
        "rhythm",
        "affirmation",
        "identity_language",
    }
    assert set(result.recommended_symbolic_style) >= {
        "nature",
        "religious",
        "ancestral",
        "light",
        "body",
    }
    assert result.recommended_language_style["directness"] == strategy.directness
    assert result.recommended_language_style["rhythm"] == strategy.pacing


def test_icaros_readiness_output_is_deterministic():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        ["spiritual_openness", "meaning_seeking", "shame_sensitivity"],
        semantic_facts=[
            SemanticFact(
                category="session",
                attribute="session_openness",
                value="open",
                evidence="open",
            )
        ],
    )
    evaluator = IcarosReadinessEvaluator()
    first = evaluator.evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    second = evaluator.evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )

    assert first == second
    assert first.to_dict() == second.to_dict()
    assert render_icaros_readiness_section(first) == render_icaros_readiness_section(second)


def test_human_profile_report_appends_icaros_readiness_section():
    fingerprint, coverage, strategy, blueprint, completed = _build_ready_context(
        ["spiritual_openness", "meaning_seeking"],
        semantic_facts=[
            SemanticFact(
                category="session",
                attribute="session_openness",
                value="open",
                evidence="open",
            )
        ],
    )
    readiness = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    report = build_human_profile_report_from_tags(
        [_pattern_tag("spiritual_openness"), _pattern_tag("meaning_seeking")],
        presenting_problem=_full_intake(),
        fingerprint_coverage_report=coverage,
    )
    report.icaros_readiness = readiness
    rendered = render_human_profile_report(report)

    assert "===== ICAROS READINESS =====" in rendered
    assert "Overall readiness:" in rendered
    assert "Language recommendation:" in rendered
    assert "Symbol recommendation:" in rendered
