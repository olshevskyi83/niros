"""Tests for Pattern-Person Fit Layer."""

from __future__ import annotations

import io
import json
from dataclasses import replace
from pathlib import Path

from niros.assessment import AssessmentResult
from niros.assessment_runner import neutral_answers_for_module, run_big_five_short_assessment
from niros.fingerprint_coverage import (
    COVERAGE_LEVEL_COMPLETE,
    COVERAGE_LEVEL_UNKNOWN,
    FingerprintCoverageAnalyzer,
)
from niros.human_digital_fingerprint import build_human_digital_fingerprint
from niros.icaros_readiness import (
    IcarosReadinessEvaluator,
    READINESS_NOT_READY,
    READINESS_READY,
)
from niros.intervention_strategy import (
    STRATEGY_CONFIDENCE_HIGH,
    STRATEGY_CONFIDENCE_LOW,
    build_intervention_strategy,
)
from niros.models import SupportedLanguage
from niros.pattern_person_fit import (
    FIT_LEVEL_STRONG,
    PatternPersonFitEvaluator,
    CandidateTherapeuticPattern,
    render_pattern_person_fit_section,
)
from niros.patterns import PatternTag
from niros.scenario_blueprint import build_scenario_blueprint
from niros.spirituality_worldview import (
    COMFORT_ALLOWED,
    COMFORT_AVOID,
    ORIENTATION_AGNOSTIC,
    ORIENTATION_ATHEIST,
    ORIENTATION_CHRISTIAN,
    ORIENTATION_RELIGION_AVERSE,
    ORIENTATION_SECULAR_HUMANIST,
    ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
    SpiritualityWorldviewProfile,
    build_spirituality_worldview_profile,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_therapeutic_patterns.json"


def _load_candidate_patterns() -> list[CandidateTherapeuticPattern]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return [CandidateTherapeuticPattern.from_dict(item) for item in payload]


def _pattern_tag(canonical_id: str, matched_text: str | None = None) -> PatternTag:
    return PatternTag(
        id=f"tag-{canonical_id}",
        session_id="session-ppf",
        evidence_id="session-ppf:evidence:0",
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


def _worldview(**overrides: object) -> SpiritualityWorldviewProfile:
    base = build_spirituality_worldview_profile(
        presenting_problem={"main_problem": "general stress"},
    )
    return replace(base, **overrides)


def _build_context(
    pattern_ids: list[str],
    *,
    worldview: SpiritualityWorldviewProfile | None = None,
    completed_assessments: dict[str, list[AssessmentResult]] | None = None,
    ensure_ready: bool = True,
):
    tags = [_pattern_tag(pattern_id) for pattern_id in pattern_ids]
    completed = completed_assessments or {
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
        presenting_problem=_full_intake(),
        patterns=tags,
        completed_assessments=completed,
    )
    if ensure_ready:
        for domain_id in (
            "self_domain",
            "emotion_regulation_domain",
            "values_identity_domain",
            "meaning",
            "cognitive_patterns_domain",
            "emotional_flexibility_domain",
            "relationships_domain",
            "presenting_problem",
            "patterns",
            "big_five",
        ):
            domain = coverage.domains[domain_id]
            coverage.domains[domain_id] = domain.__class__(
                domain_id=domain_id,
                coverage=1.0,
                confidence=1.0,
                level=COVERAGE_LEVEL_COMPLETE,
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
                "presenting_problem",
                "patterns",
            }
        ]
    fingerprint = build_human_digital_fingerprint(
        detected_patterns=tags,
        presenting_problem=_full_intake(),
        assessment_results=[
            result for module_results in completed.values() for result in module_results
        ],
    )
    if worldview is not None:
        fingerprint = {**fingerprint, "spirituality_worldview": worldview.to_dict()}
    strategy = build_intervention_strategy(
        fingerprint,
        fingerprint_coverage_report=coverage,
    )
    blueprint = build_scenario_blueprint(fingerprint["patterns"], intervention_strategy=strategy)
    readiness = IcarosReadinessEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        completed_assessments=completed,
    )
    profile = (
        worldview
        or SpiritualityWorldviewProfile.from_dict(fingerprint["spirituality_worldview"])
    )
    return fingerprint, coverage, strategy, blueprint, readiness, profile


def _evaluate(
    pattern_ids: list[str],
    *,
    worldview: SpiritualityWorldviewProfile | None = None,
):
    fingerprint, coverage, strategy, blueprint, readiness, profile = _build_context(
        pattern_ids,
        worldview=worldview,
    )
    return PatternPersonFitEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=profile,
        candidate_patterns=_load_candidate_patterns(),
    )


def _pattern_by_id(result, pattern_id: str):
    for item in result.selected_patterns:
        if item.id == pattern_id:
            return item
    return None


def _rejection_reasons(result, pattern_id: str) -> tuple[str, ...]:
    for item in result.rejected_patterns:
        if item.id == pattern_id:
            return item.reason
    return ()


def test_not_ready_blocks_all_pattern_selection():
    fingerprint, coverage, strategy, blueprint, readiness, profile = _build_context(
        ["shame_sensitivity", "harsh_self_criticism"],
        ensure_ready=False,
    )
    blocked = replace(
        readiness,
        readiness_level=READINESS_NOT_READY,
        ready=False,
        overall_readiness=25,
    )
    result = PatternPersonFitEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=blocked,
        spirituality_worldview=profile,
        candidate_patterns=_load_candidate_patterns(),
    )

    assert result.blocking_reason
    assert not result.selected_patterns
    assert "Not Ready" in result.blocking_reason


def test_atheist_worldview_rejects_religious_patterns():
    worldview = _worldview(
        worldview_orientation=ORIENTATION_ATHEIST,
        religious_language_comfort=COMFORT_AVOID,
        avoided_symbolic_language=("god", "prayer", "religion"),
        icaros_language_constraints=("use secular language", "avoid religious claims"),
    )
    result = _evaluate(
        ["shame_sensitivity", "harsh_self_criticism"],
        worldview=worldview,
    )

    assert _pattern_by_id(result, "identity_reconstruction_loop") is not None
    assert _rejection_reasons(result, "divine_surrender_prayer_loop")
    assert _rejection_reasons(result, "christian_hope_light_loop")


def test_secular_worldview_allows_secular_identity_and_grounding_patterns():
    worldview = _worldview(
        worldview_orientation=ORIENTATION_SECULAR_HUMANIST,
        religious_language_comfort=COMFORT_AVOID,
        icaros_language_constraints=("use secular language",),
    )
    result = _evaluate(
        ["shame_sensitivity", "emotional_overwhelm"],
        worldview=worldview,
    )

    assert _pattern_by_id(result, "identity_reconstruction_loop") is not None
    assert _pattern_by_id(result, "secular_grounding_breath_loop") is not None


def test_religion_averse_rejects_religious_patterns():
    worldview = _worldview(
        worldview_orientation=ORIENTATION_RELIGION_AVERSE,
        religious_language_comfort=COMFORT_AVOID,
        avoided_symbolic_language=("god", "prayer", "religion"),
    )
    result = _evaluate(["control_resistance"], worldview=worldview)

    assert _rejection_reasons(result, "divine_surrender_prayer_loop")
    assert _rejection_reasons(result, "christian_hope_light_loop")


def test_christian_worldview_allows_christian_patterns_only_with_explicit_comfort():
    without_comfort = _worldview(
        worldview_orientation=ORIENTATION_CHRISTIAN,
        religious_language_comfort=COMFORT_AVOID,
        symbolic_language_preferences=("christ", "light"),
    )
    blocked = _evaluate(["hopelessness_signal", "meaning_seeking"], worldview=without_comfort)
    assert _rejection_reasons(blocked, "christian_hope_light_loop")

    with_comfort = _worldview(
        worldview_orientation=ORIENTATION_CHRISTIAN,
        religious_language_comfort=COMFORT_ALLOWED,
        symbolic_language_preferences=("christ", "light"),
    )
    allowed = _evaluate(["hopelessness_signal", "meaning_seeking"], worldview=with_comfort)
    selected = _pattern_by_id(allowed, "christian_hope_light_loop")
    assert selected is not None
    assert selected.fit_score >= 40


def test_agnostic_worldview_prefers_symbolic_uncertainty():
    worldview = _worldview(
        worldview_orientation=ORIENTATION_AGNOSTIC,
        symbolic_language_preferences=("light", "inner_wisdom"),
    )
    result = _evaluate(["meaning_seeking", "identity_uncertainty"], worldview=worldview)

    symbolic = _pattern_by_id(result, "symbolic_open_question_loop")
    assert symbolic is not None
    assert any(
        "uncertainty" in reason.lower() or "agnostic" in reason.lower()
        for reason in symbolic.why_selected
    )
    assert _rejection_reasons(result, "dogmatic_certainty_loop")


def test_spiritual_not_religious_prefers_nature_breath_light_patterns():
    worldview = _worldview(
        worldview_orientation=ORIENTATION_SPIRITUAL_NOT_RELIGIOUS,
        symbolic_language_preferences=("nature", "breath", "light", "inner_wisdom"),
    )
    result = _evaluate(["meaning_seeking", "spiritual_openness"], worldview=worldview)

    nature = _pattern_by_id(result, "nature_inner_wisdom_loop")
    assert nature is not None
    assert any(
        "nature" in reason.lower() or "inner wisdom" in reason.lower()
        for reason in nature.why_selected
    )


def test_low_self_confidence_blocks_intense_identity_patterns():
    fingerprint, coverage, strategy, blueprint, readiness, profile = _build_context(
        ["shame_sensitivity", "harsh_self_criticism"],
    )
    coverage.domains["self_domain"] = coverage.domains["self_domain"].__class__(
        domain_id="self_domain",
        coverage=0.1,
        confidence=0.1,
        level=COVERAGE_LEVEL_UNKNOWN,
    )
    adjusted_focus = tuple(
        replace(item, confidence=STRATEGY_CONFIDENCE_LOW)
        if item.focus_area == "self-worth / self-criticism"
        else item
        for item in strategy.focus_confidence
    )
    strategy = replace(strategy, focus_confidence=adjusted_focus)

    result = PatternPersonFitEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=profile,
        candidate_patterns=_load_candidate_patterns(),
    )

    assert _rejection_reasons(result, "identity_reconstruction_loop")


def test_low_emotion_regulation_prefers_grounding_patterns():
    fingerprint, coverage, strategy, blueprint, readiness, profile = _build_context(
        ["emotional_overwhelm", "emotional_suppression"],
    )
    coverage.domains["emotion_regulation_domain"] = coverage.domains[
        "emotion_regulation_domain"
    ].__class__(
        domain_id="emotion_regulation_domain",
        coverage=0.1,
        confidence=0.1,
        level=COVERAGE_LEVEL_UNKNOWN,
    )
    strategy = replace(strategy, grounding_priority="high")

    result = PatternPersonFitEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=profile,
        candidate_patterns=_load_candidate_patterns(),
    )

    grounding = _pattern_by_id(result, "secular_grounding_breath_loop")
    assert grounding is not None
    assert any("grounding" in reason.lower() for reason in grounding.why_selected)


def test_values_identity_unknown_blocks_destiny_mission_language():
    fingerprint, coverage, strategy, blueprint, readiness, profile = _build_context(
        ["identity_confusion", "loss_of_meaning"],
    )
    coverage.domains["values_identity_domain"] = coverage.domains[
        "values_identity_domain"
    ].__class__(
        domain_id="values_identity_domain",
        coverage=0.0,
        confidence=0.0,
        level=COVERAGE_LEVEL_UNKNOWN,
    )

    result = PatternPersonFitEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=profile,
        candidate_patterns=_load_candidate_patterns(),
    )

    assert _rejection_reasons(result, "destiny_mission_purpose_loop")


def test_strategy_match_increases_score():
    fingerprint, coverage, strategy, blueprint, readiness, profile = _build_context(
        ["shame_sensitivity", "harsh_self_criticism"],
        worldview=_worldview(worldview_orientation=ORIENTATION_SECULAR_HUMANIST),
    )
    adjusted_focus = tuple(
        replace(item, confidence=STRATEGY_CONFIDENCE_HIGH)
        if item.focus_area == "self-worth / self-criticism"
        else item
        for item in strategy.focus_confidence
    )
    strategy = replace(strategy, focus_confidence=adjusted_focus)
    for domain_id in ("self_domain", "values_identity_domain", "emotion_regulation_domain"):
        coverage.domains[domain_id] = coverage.domains[domain_id].__class__(
            domain_id=domain_id,
            coverage=1.0,
            confidence=1.0,
            level=COVERAGE_LEVEL_COMPLETE,
        )

    result = PatternPersonFitEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=profile,
        candidate_patterns=_load_candidate_patterns(),
    )

    identity = _pattern_by_id(result, "identity_reconstruction_loop")
    assert identity is not None
    assert any("strategy" in reason.lower() for reason in identity.why_selected)
    assert identity.fit_score >= 70


def test_avoid_if_blocks_pattern():
    fingerprint, coverage, strategy, blueprint, readiness, profile = _build_context(
        ["shame_sensitivity"],
    )
    candidate = CandidateTherapeuticPattern(
        id="test_avoid_pattern",
        psychological_function=("agency",),
        good_for=("shame",),
        avoid_if=("shame_sensitivity",),
        language_style=("grounding_language",),
        rhythm="steady",
        semantic_cluster=("grounding",),
        spiritual_compatibility=("secular",),
    )
    result = PatternPersonFitEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=profile,
        candidate_patterns=[candidate],
    )

    assert _rejection_reasons(result, "test_avoid_pattern")


def test_avoided_symbols_block_pattern():
    worldview = _worldview(
        worldview_orientation=ORIENTATION_RELIGION_AVERSE,
        avoided_symbolic_language=("prayer", "god"),
        religious_language_comfort=COMFORT_AVOID,
    )
    result = _evaluate(["control_resistance"], worldview=worldview)

    assert _rejection_reasons(result, "divine_surrender_prayer_loop")


def test_selected_patterns_include_why_selected():
    result = _evaluate(
        ["shame_sensitivity", "harsh_self_criticism"],
        worldview=_worldview(worldview_orientation=ORIENTATION_SECULAR_HUMANIST),
    )
    selected = _pattern_by_id(result, "identity_reconstruction_loop")
    assert selected is not None
    assert selected.why_selected
    assert selected.constraints


def test_rejected_patterns_include_reasons():
    result = _evaluate(
        ["control_resistance"],
        worldview=_worldview(
            worldview_orientation=ORIENTATION_ATHEIST,
            avoided_symbolic_language=("god", "prayer"),
        ),
    )
    reasons = _rejection_reasons(result, "divine_surrender_prayer_loop")
    assert reasons


def test_output_is_deterministic():
    worldview = _worldview(worldview_orientation=ORIENTATION_SECULAR_HUMANIST)
    first = _evaluate(["shame_sensitivity", "harsh_self_criticism"], worldview=worldview)
    second = _evaluate(["shame_sensitivity", "harsh_self_criticism"], worldview=worldview)

    assert first == second
    assert first.to_dict() == second.to_dict()
    assert render_pattern_person_fit_section(first) == render_pattern_person_fit_section(second)


def test_strong_fit_level_at_high_score():
    fingerprint, coverage, strategy, blueprint, readiness, profile = _build_context(
        ["shame_sensitivity", "harsh_self_criticism"],
        worldview=_worldview(worldview_orientation=ORIENTATION_SECULAR_HUMANIST),
    )
    for domain_id in (
        "self_domain",
        "values_identity_domain",
        "emotion_regulation_domain",
        "spirituality_worldview",
    ):
        coverage.domains[domain_id] = coverage.domains[domain_id].__class__(
            domain_id=domain_id,
            coverage=1.0,
            confidence=1.0,
            level=COVERAGE_LEVEL_COMPLETE,
        )
    readiness = replace(
        readiness,
        readiness_level=READINESS_READY,
        ready=True,
        overall_readiness=90,
    )

    result = PatternPersonFitEvaluator().evaluate(
        fingerprint=fingerprint,
        coverage_report=coverage,
        strategy=strategy,
        scenario_blueprint=blueprint,
        icaros_readiness=readiness,
        spirituality_worldview=profile,
        candidate_patterns=_load_candidate_patterns(),
    )

    identity = _pattern_by_id(result, "identity_reconstruction_loop")
    assert identity is not None
    assert identity.fit_level == FIT_LEVEL_STRONG
    assert result.overall_fit_confidence in {"high", "medium"}
