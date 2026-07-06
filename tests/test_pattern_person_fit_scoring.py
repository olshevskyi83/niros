"""Tests for Pattern–Person Fit scoring."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import (
    NOT_RECOMMENDED,
    RECOMMENDED,
    USE_WITH_CAUTION,
    PersonFitProfile,
)
from niros.pattern_person_fit_scoring import score_pattern_fit
from niros_tle.universal_pattern import UniversalPattern


def _profile(
    *,
    profile_id: str = "profile_001",
    active_signals: tuple[str, ...] = (),
    dominant_domains: tuple[str, ...] = (),
    risk_signals: tuple[str, ...] = (),
    needs: tuple[str, ...] = (),
) -> PersonFitProfile:
    return PersonFitProfile(
        profile_id=profile_id,
        active_signals=active_signals,
        dominant_domains=dominant_domains,
        risk_signals=risk_signals,
        needs=needs,
    )


def _pattern(
    *,
    pattern_id: str = "canonical_pattern_001",
    canonical_name: str = "accept painful emotions",
    confidence: float = 0.90,
    target_signals: tuple[str, ...] = (),
    contraindication_signals: tuple[str, ...] = (),
    fit_domains: tuple[str, ...] = (),
    expected_effects: tuple[str, ...] = (),
) -> UniversalPattern:
    return UniversalPattern(
        pattern_id=pattern_id,
        canonical_name=canonical_name,
        source_families=("act",),
        member_pattern_ids=(f"{pattern_id}_member",),
        confidence=confidence,
        target_signals=target_signals,
        contraindication_signals=contraindication_signals,
        fit_domains=fit_domains,
        expected_effects=expected_effects,
    )


def test_exact_signal_domain_need_match_produces_high_score():
    profile = _profile(
        active_signals=("emotional_avoidance", "shame"),
        dominant_domains=("emotion_regulation",),
        needs=("acceptance",),
    )
    pattern = _pattern(
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        confidence=0.90,
    )
    result = score_pattern_fit(profile, pattern)
    assert result.fit_score >= 0.65
    assert result.recommendation_status == RECOMMENDED
    assert result.matched_signals == ("emotional_avoidance", "shame")
    assert result.matched_domains == ("emotion_regulation",)
    assert result.matched_needs == ("acceptance",)


def test_no_matches_produces_low_score():
    profile = _profile(
        active_signals=("low_agency",),
        dominant_domains=("self",),
        needs=("agency_restoration",),
    )
    pattern = _pattern(
        target_signals=("emotional_avoidance",),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        confidence=0.20,
    )
    result = score_pattern_fit(profile, pattern)
    assert result.fit_score < 0.50
    assert result.recommendation_status == NOT_RECOMMENDED
    assert result.matched_signals == ()
    assert result.matched_domains == ()
    assert result.matched_needs == ()


def test_contraindication_lowers_score():
    profile = _profile(
        active_signals=("emotional_avoidance",),
        dominant_domains=("emotion_regulation",),
        needs=("acceptance",),
        risk_signals=("psychosis_risk",),
    )
    pattern_without = _pattern(
        target_signals=("emotional_avoidance",),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        confidence=0.90,
    )
    pattern_with = _pattern(
        target_signals=("emotional_avoidance",),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        contraindication_signals=("psychosis_risk",),
        confidence=0.90,
    )
    without_hits = score_pattern_fit(profile, pattern_without)
    with_hits = score_pattern_fit(profile, pattern_with)
    assert with_hits.fit_score < without_hits.fit_score
    assert with_hits.contraindication_hits == ("psychosis_risk",)


def test_contraindication_changes_recommendation_to_use_with_caution():
    profile = _profile(
        active_signals=("emotional_avoidance", "shame"),
        dominant_domains=("emotion_regulation",),
        needs=("acceptance",),
        risk_signals=("psychosis_risk",),
    )
    pattern = _pattern(
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        contraindication_signals=("psychosis_risk",),
        confidence=0.90,
    )
    result = score_pattern_fit(profile, pattern)
    assert result.recommendation_status == USE_WITH_CAUTION


def test_empty_pattern_fields_do_not_divide_by_zero():
    profile = _profile(active_signals=("emotional_avoidance",))
    pattern = _pattern(confidence=0.50)
    result = score_pattern_fit(profile, pattern)
    assert result.fit_score == 0.075
    assert result.matched_signals == ()


def test_score_is_clamped_between_zero_and_one():
    profile = _profile(
        active_signals=("a", "b", "c"),
        dominant_domains=("d1", "d2"),
        needs=("n1", "n2"),
    )
    pattern = _pattern(
        target_signals=("a", "b", "c"),
        fit_domains=("d1", "d2"),
        expected_effects=("n1", "n2"),
        confidence=1.0,
    )
    result = score_pattern_fit(profile, pattern)
    assert 0.0 <= result.fit_score <= 1.0


def test_score_is_deterministic():
    profile = _profile(
        active_signals=("emotional_avoidance",),
        dominant_domains=("emotion_regulation",),
        needs=("acceptance",),
    )
    pattern = _pattern(
        target_signals=("emotional_avoidance",),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        confidence=0.88,
    )
    first = score_pattern_fit(profile, pattern)
    second = score_pattern_fit(profile, pattern)
    assert first == second


def test_matched_tuples_are_sorted():
    profile = _profile(
        active_signals=("shame", "emotional_avoidance"),
        dominant_domains=("emotion_regulation", "self"),
        needs=("acceptance", "grounding"),
        risk_signals=("psychosis_risk", "acute_dissociation"),
    )
    pattern = _pattern(
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("self", "emotion_regulation"),
        expected_effects=("grounding", "acceptance"),
        contraindication_signals=("acute_dissociation", "psychosis_risk"),
    )
    result = score_pattern_fit(profile, pattern)
    assert result.matched_signals == ("emotional_avoidance", "shame")
    assert result.matched_domains == ("emotion_regulation", "self")
    assert result.matched_needs == ("acceptance", "grounding")
    assert result.contraindication_hits == ("acute_dissociation", "psychosis_risk")


def test_recommended_threshold_works():
    profile = _profile(
        active_signals=("emotional_avoidance", "shame"),
        dominant_domains=("emotion_regulation",),
        needs=("acceptance",),
    )
    pattern = _pattern(
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        confidence=0.90,
    )
    result = score_pattern_fit(profile, pattern)
    assert result.fit_score >= 0.65
    assert result.recommendation_status == RECOMMENDED


def test_use_with_caution_threshold_works():
    profile = _profile(
        active_signals=("emotional_avoidance",),
        dominant_domains=("emotion_regulation",),
        needs=(),
    )
    pattern = _pattern(
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        confidence=0.60,
    )
    result = score_pattern_fit(profile, pattern)
    assert 0.50 <= result.fit_score < 0.65
    assert result.recommendation_status == USE_WITH_CAUTION


def test_not_recommended_threshold_works():
    profile = _profile()
    pattern = _pattern(confidence=0.10)
    result = score_pattern_fit(profile, pattern)
    assert result.fit_score < 0.50
    assert result.recommendation_status == NOT_RECOMMENDED


def test_reason_is_deterministic():
    profile = _profile(
        active_signals=("emotional_avoidance", "shame"),
        dominant_domains=("emotion_regulation",),
        needs=("acceptance",),
        risk_signals=("psychosis_risk",),
    )
    pattern = _pattern(
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        contraindication_signals=("psychosis_risk",),
    )
    result = score_pattern_fit(profile, pattern)
    assert result.reason == "signals=2; domains=1; needs=1; contraindications=1"
