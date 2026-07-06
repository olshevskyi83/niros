"""Semantic validation pipeline — connect text fixtures to Pattern–Person Fit."""

from __future__ import annotations

from test_pattern_person_fit_human_cases import (
    PATTERN_ACCEPTANCE,
    PATTERN_DEEP_EXPOSURE,
    PATTERN_DEFUSION,
    PATTERN_IDENTITY,
    PATTERN_MEANING,
    PATTERN_SELF_COMPASSION,
    PATTERN_STABILIZATION,
    PATTERN_VALUES,
    human_case_pattern_library,
)
from test_semantic_validation_fixtures import (
    SemanticValidationCase,
    build_profile_from_case,
    semantic_validation_cases,
)

from niros.pattern_person_fit_report import build_pattern_fit_report
from niros.strategy_candidate_builder import build_strategy_candidate
from niros.strategy_explanation import StrategyExplanation, build_strategy_explanation
from niros_tle.universal_pattern import UniversalPattern
from niros_tle.universal_pattern_library import build_universal_pattern_library

PATTERN_AGENCY_SUPPORT = "pattern_agency_support"
PATTERN_BOUNDARY_SUPPORT = "pattern_boundary_support"


def _case(case_id: str) -> SemanticValidationCase:
    return next(case for case in semantic_validation_cases() if case.case_id == case_id)


def semantic_validation_pattern_library() -> tuple[UniversalPattern, ...]:
    """Human-case library plus patterns needed for semantic validation cases."""
    return human_case_pattern_library() + (
        UniversalPattern(
            pattern_id=PATTERN_AGENCY_SUPPORT,
            canonical_name="agency support",
            source_families=("act",),
            member_pattern_ids=(f"{PATTERN_AGENCY_SUPPORT}_member",),
            confidence=0.82,
            target_signals=("low_agency", "learned_helplessness"),
            fit_domains=("self", "values"),
            expected_effects=("agency_support",),
        ),
        UniversalPattern(
            pattern_id=PATTERN_BOUNDARY_SUPPORT,
            canonical_name="boundary and emotional expression support",
            source_families=("cft",),
            member_pattern_ids=(f"{PATTERN_BOUNDARY_SUPPORT}_member",),
            confidence=0.83,
            target_signals=(
                "rejection_sensitivity",
                "people_pleasing",
                "emotional_suppression",
            ),
            fit_domains=("relationships", "emotion_regulation"),
            expected_effects=("boundary_support", "emotional_expression"),
        ),
    )


def run_semantic_pipeline(
    case: SemanticValidationCase,
    *,
    max_patterns: int = 3,
) -> tuple[object, object, StrategyExplanation]:
    """Map a semantic case to a profile and run the fit pipeline."""
    profile = build_profile_from_case(case)
    library = build_universal_pattern_library(semantic_validation_pattern_library())
    fit_report = build_pattern_fit_report(profile, library)
    strategy = build_strategy_candidate(fit_report, max_patterns=max_patterns)
    explanation = build_strategy_explanation(strategy)
    return fit_report, strategy, explanation


def _selected_ids(strategy) -> set[str]:
    return {pattern.pattern_id for pattern in strategy.selected_patterns}


def _caution_ids(strategy) -> set[str]:
    return {pattern.pattern_id for pattern in strategy.caution_patterns}


def _rank_index(fit_report, pattern_id: str) -> int:
    return next(
        index
        for index, score in enumerate(fit_report.ranked_matches)
        if score.pattern_id == pattern_id
    )


def test_semantic_shame_case_pipeline():
    _, strategy, explanation = run_semantic_pipeline(_case("semantic_case_shame_self_criticism"))
    selected = _selected_ids(strategy)
    caution = _caution_ids(strategy)

    assert PATTERN_SELF_COMPASSION in selected
    assert PATTERN_ACCEPTANCE in selected
    assert PATTERN_DEEP_EXPOSURE in caution
    assert PATTERN_DEEP_EXPOSURE not in selected
    assert PATTERN_VALUES not in selected
    assert explanation.explanation_items


def test_semantic_values_confusion_case_pipeline():
    _, strategy, _explanation = run_semantic_pipeline(_case("semantic_case_values_confusion"))
    selected = _selected_ids(strategy)

    assert PATTERN_VALUES in selected
    assert PATTERN_SELF_COMPASSION not in selected
    assert PATTERN_ACCEPTANCE not in selected


def test_semantic_meaning_emptiness_case_pipeline():
    fit_report, strategy, _explanation = run_semantic_pipeline(
        _case("semantic_case_meaning_emptiness")
    )
    selected = _selected_ids(strategy)

    assert PATTERN_MEANING in selected
    assert _rank_index(fit_report, PATTERN_MEANING) < _rank_index(fit_report, PATTERN_VALUES)


def test_semantic_identity_diffusion_case_pipeline():
    _, strategy, _explanation = run_semantic_pipeline(_case("semantic_case_identity_diffusion"))
    selected = _selected_ids(strategy)

    assert PATTERN_IDENTITY in selected


def test_semantic_rumination_case_pipeline():
    _, strategy, _explanation = run_semantic_pipeline(
        _case("semantic_case_rumination_catastrophizing")
    )
    selected = _selected_ids(strategy)

    assert PATTERN_DEFUSION in selected
    assert PATTERN_SELF_COMPASSION not in selected
    assert PATTERN_VALUES not in selected


def test_semantic_overwhelm_case_pipeline():
    _, strategy, _explanation = run_semantic_pipeline(_case("semantic_case_overwhelm_instability"))
    selected = _selected_ids(strategy)
    caution = _caution_ids(strategy)

    assert PATTERN_STABILIZATION in selected
    assert PATTERN_DEEP_EXPOSURE in caution
    assert PATTERN_DEEP_EXPOSURE not in selected


def test_semantic_low_agency_case_pipeline():
    _, strategy, _explanation = run_semantic_pipeline(_case("semantic_case_low_agency"))
    selected = _selected_ids(strategy)

    assert PATTERN_AGENCY_SUPPORT in selected


def test_semantic_rejection_sensitivity_case_pipeline():
    _, strategy, _explanation = run_semantic_pipeline(_case("semantic_case_rejection_sensitivity"))
    selected = _selected_ids(strategy)

    assert PATTERN_BOUNDARY_SUPPORT in selected


def test_semantic_validation_pipeline_is_deterministic():
    results = []
    for case in semantic_validation_cases():
        first = run_semantic_pipeline(case)
        second = run_semantic_pipeline(case)
        first_selected = tuple(score.pattern_id for score in first[1].selected_patterns)
        second_selected = tuple(score.pattern_id for score in second[1].selected_patterns)
        assert first_selected == second_selected
        assert first[2].summary == second[2].summary
        results.append((case.case_id, first_selected, first[2].summary))

    assert len(results) == len(semantic_validation_cases())
