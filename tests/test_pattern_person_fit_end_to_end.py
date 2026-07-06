"""End-to-end smoke test for Pattern–Person Fit through Strategy Explanation."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import (
    NOT_RECOMMENDED,
    RECOMMENDED,
    USE_WITH_CAUTION,
    PersonFitProfile,
)
from niros.pattern_person_fit_report import build_pattern_fit_report
from niros.strategy_candidate_builder import build_strategy_candidate
from niros.strategy_explanation import build_strategy_explanation
from niros_tle.universal_pattern import UniversalPattern
from niros_tle.universal_pattern_library import build_universal_pattern_library

SELF_COMPASSION_ID = "canonical_pattern_self_compassion"
ACCEPTANCE_ID = "canonical_pattern_acceptance"
DEEP_EXPOSURE_ID = "canonical_pattern_deep_exposure"
VALUES_ID = "canonical_pattern_values"


def _profile() -> PersonFitProfile:
    return PersonFitProfile(
        profile_id="profile_shame_avoidance_001",
        active_signals=(
            "shame_sensitivity",
            "harsh_self_criticism",
            "emotional_avoidance",
        ),
        dominant_domains=("self", "emotion_regulation"),
        risk_signals=("overwhelm_risk",),
        needs=("self_compassion", "emotional_tolerance", "stabilization"),
        session_phase="preparation",
    )


def _patterns() -> tuple[UniversalPattern, ...]:
    return (
        UniversalPattern(
            pattern_id=SELF_COMPASSION_ID,
            canonical_name="self compassion for shame",
            source_families=("cft",),
            member_pattern_ids=(f"{SELF_COMPASSION_ID}_member",),
            confidence=0.90,
            target_signals=("shame_sensitivity", "harsh_self_criticism"),
            fit_domains=("self",),
            expected_effects=("self_compassion",),
        ),
        UniversalPattern(
            pattern_id=ACCEPTANCE_ID,
            canonical_name="acceptance of difficult emotions",
            source_families=("act",),
            member_pattern_ids=(f"{ACCEPTANCE_ID}_member",),
            confidence=0.85,
            target_signals=("emotional_avoidance",),
            fit_domains=("emotion_regulation",),
            expected_effects=("emotional_tolerance",),
        ),
        UniversalPattern(
            pattern_id=DEEP_EXPOSURE_ID,
            canonical_name="deep emotional exposure",
            source_families=("act",),
            member_pattern_ids=(f"{DEEP_EXPOSURE_ID}_member",),
            confidence=0.90,
            target_signals=("emotional_avoidance",),
            fit_domains=("emotion_regulation",),
            expected_effects=("emotional_tolerance",),
            contraindication_signals=("overwhelm_risk",),
        ),
        UniversalPattern(
            pattern_id=VALUES_ID,
            canonical_name="values clarification",
            source_families=("act",),
            member_pattern_ids=(f"{VALUES_ID}_member",),
            confidence=0.80,
            target_signals=("values_confusion",),
            fit_domains=("values",),
            expected_effects=("values_alignment",),
        ),
    )


def _pattern_ids(scores: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(score.pattern_id for score in scores)


def _run_pipeline():
    library = build_universal_pattern_library(_patterns())
    profile = _profile()
    fit_report = build_pattern_fit_report(profile, library)
    strategy = build_strategy_candidate(fit_report, max_patterns=3)
    explanation = build_strategy_explanation(strategy)
    return profile, fit_report, strategy, explanation


def test_pattern_person_fit_end_to_end_smoke():
    profile, fit_report, strategy, explanation = _run_pipeline()

    assert fit_report.ranked_matches
    assert fit_report.profile_id == profile.profile_id

    recommended_ids = set(_pattern_ids(fit_report.recommended_patterns))
    caution_ids = set(_pattern_ids(fit_report.caution_patterns))
    excluded_ids = set(_pattern_ids(fit_report.excluded_patterns))

    assert SELF_COMPASSION_ID in recommended_ids
    assert ACCEPTANCE_ID in recommended_ids
    assert DEEP_EXPOSURE_ID in caution_ids
    assert VALUES_ID in excluded_ids

    ranked_ids = _pattern_ids(fit_report.ranked_matches)
    assert ranked_ids.index(SELF_COMPASSION_ID) < ranked_ids.index(ACCEPTANCE_ID)
    assert ranked_ids.index(ACCEPTANCE_ID) < ranked_ids.index(DEEP_EXPOSURE_ID)
    assert ranked_ids.index(DEEP_EXPOSURE_ID) < ranked_ids.index(VALUES_ID)

    selected_ids = set(_pattern_ids(strategy.selected_patterns))
    assert SELF_COMPASSION_ID in selected_ids
    assert ACCEPTANCE_ID in selected_ids
    assert DEEP_EXPOSURE_ID not in selected_ids
    assert set(_pattern_ids(strategy.caution_patterns)) == {DEEP_EXPOSURE_ID}

    assert explanation.strategy_id == strategy.strategy_id
    assert explanation.profile_id == profile.profile_id
    assert explanation.summary == "selected=2; caution=1; excluded=1"

    for pattern in strategy.selected_patterns:
        matching_items = [
            item
            for item in explanation.explanation_items
            if item.pattern_id == pattern.pattern_id
        ]
        assert len(matching_items) == 1
        assert matching_items[0].fit_score == pattern.fit_score

    self_compassion_item = next(
        item
        for item in explanation.explanation_items
        if item.pattern_id == SELF_COMPASSION_ID
    )
    assert self_compassion_item.recommendation_status == RECOMMENDED
    assert self_compassion_item.matched_signals == (
        "harsh_self_criticism",
        "shame_sensitivity",
    )

    deep_exposure_item = next(
        item
        for item in explanation.explanation_items
        if item.pattern_id == DEEP_EXPOSURE_ID
    )
    assert deep_exposure_item.recommendation_status == USE_WITH_CAUTION
    assert deep_exposure_item.contraindication_hits == ("overwhelm_risk",)

    values_item = next(
        item for item in explanation.explanation_items if item.pattern_id == VALUES_ID
    )
    assert values_item.recommendation_status == NOT_RECOMMENDED


def test_pattern_person_fit_end_to_end_is_deterministic():
    first = _run_pipeline()
    second = _run_pipeline()
    assert first[1] == second[1]
    assert first[2] == second[2]
    assert first[3] == second[3]
