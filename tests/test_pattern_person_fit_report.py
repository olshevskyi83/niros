"""Tests for Pattern–Person Fit report builder."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import (
    NOT_RECOMMENDED,
    RECOMMENDED,
    USE_WITH_CAUTION,
    PatternFitReport,
    PatternFitScore,
    PersonFitProfile,
)
from niros.pattern_person_fit_report import build_pattern_fit_report
from niros_tle.universal_pattern import UniversalPattern
from niros_tle.universal_pattern_library import build_universal_pattern_library


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
    pattern_id: str,
    canonical_name: str,
    confidence: float = 0.80,
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


def _mixed_library():
    profile = _profile(
        profile_id="profile_001",
        active_signals=("emotional_avoidance", "shame"),
        dominant_domains=("emotion_regulation",),
        needs=("acceptance",),
        risk_signals=("psychosis_risk",),
    )
    recommended = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        confidence=0.90,
    )
    caution = _pattern(
        pattern_id="canonical_pattern_002",
        canonical_name="accept with caution",
        target_signals=("emotional_avoidance",),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        contraindication_signals=("psychosis_risk",),
        confidence=0.90,
    )
    excluded = _pattern(
        pattern_id="canonical_pattern_003",
        canonical_name="clarify personal values",
        target_signals=("values_conflict",),
        fit_domains=("values_identity",),
        expected_effects=("clarity",),
        confidence=0.10,
    )
    library = build_universal_pattern_library((excluded, caution, recommended))
    return profile, library


def test_empty_library_returns_empty_report():
    profile = _profile(profile_id="profile_001")
    library = build_universal_pattern_library(())
    report = build_pattern_fit_report(profile, library)
    assert isinstance(report, PatternFitReport)
    assert report.profile_id == "profile_001"
    assert report.ranked_matches == ()
    assert report.recommended_patterns == ()
    assert report.caution_patterns == ()
    assert report.excluded_patterns == ()


def test_profile_id_is_preserved():
    profile, library = _mixed_library()
    report = build_pattern_fit_report(profile, library)
    assert report.profile_id == "profile_001"


def test_ranked_matches_are_populated():
    profile, library = _mixed_library()
    report = build_pattern_fit_report(profile, library)
    assert len(report.ranked_matches) == 3
    assert all(isinstance(score, PatternFitScore) for score in report.ranked_matches)


def test_recommended_patterns_contains_only_recommended():
    profile, library = _mixed_library()
    report = build_pattern_fit_report(profile, library)
    assert report.recommended_patterns
    assert all(
        score.recommendation_status == RECOMMENDED
        for score in report.recommended_patterns
    )


def test_caution_patterns_contains_only_use_with_caution():
    profile, library = _mixed_library()
    report = build_pattern_fit_report(profile, library)
    assert report.caution_patterns
    assert all(
        score.recommendation_status == USE_WITH_CAUTION
        for score in report.caution_patterns
    )


def test_excluded_patterns_contains_only_not_recommended():
    profile, library = _mixed_library()
    report = build_pattern_fit_report(profile, library)
    assert report.excluded_patterns
    assert all(
        score.recommendation_status == NOT_RECOMMENDED
        for score in report.excluded_patterns
    )


def test_group_order_follows_ranked_order():
    profile, library = _mixed_library()
    report = build_pattern_fit_report(profile, library)
    grouped = (
        report.recommended_patterns
        + report.caution_patterns
        + report.excluded_patterns
    )
    recommended_ids = [score.pattern_id for score in report.recommended_patterns]
    caution_ids = [score.pattern_id for score in report.caution_patterns]
    excluded_ids = [score.pattern_id for score in report.excluded_patterns]
    ranked_ids = [score.pattern_id for score in report.ranked_matches]
    assert recommended_ids == [
        pattern_id
        for pattern_id in ranked_ids
        if pattern_id in set(recommended_ids)
    ]
    assert caution_ids == [
        pattern_id for pattern_id in ranked_ids if pattern_id in set(caution_ids)
    ]
    assert excluded_ids == [
        pattern_id for pattern_id in ranked_ids if pattern_id in set(excluded_ids)
    ]
    assert [score.pattern_id for score in grouped] == ranked_ids


def test_all_patterns_appear_exactly_once_across_groups():
    profile, library = _mixed_library()
    report = build_pattern_fit_report(profile, library)
    grouped_ids = [
        score.pattern_id
        for score in (
            report.recommended_patterns
            + report.caution_patterns
            + report.excluded_patterns
        )
    ]
    ranked_ids = [score.pattern_id for score in report.ranked_matches]
    assert grouped_ids == ranked_ids
    assert len(set(grouped_ids)) == len(grouped_ids)


def test_output_is_deterministic():
    profile, library = _mixed_library()
    first = build_pattern_fit_report(profile, library)
    second = build_pattern_fit_report(profile, library)
    assert first == second


def test_report_contains_pattern_fit_score_objects():
    profile, library = _mixed_library()
    report = build_pattern_fit_report(profile, library)
    all_scores = (
        report.ranked_matches
        + report.recommended_patterns
        + report.caution_patterns
        + report.excluded_patterns
    )
    assert all(isinstance(score, PatternFitScore) for score in all_scores)
