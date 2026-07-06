"""Tests for Pattern–Person Fit contract dataclasses."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import (
    NOT_RECOMMENDED,
    RECOMMENDED,
    USE_WITH_CAUTION,
    PatternFitReport,
    PatternFitScore,
    PersonFitProfile,
)


def test_person_fit_profile_defaults():
    profile = PersonFitProfile(profile_id="profile_001")
    assert profile.profile_id == "profile_001"
    assert profile.active_signals == ()
    assert profile.dominant_domains == ()
    assert profile.risk_signals == ()
    assert profile.needs == ()
    assert profile.session_phase == "unspecified"


def test_pattern_fit_score_defaults():
    score = PatternFitScore(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        fit_score=0.0,
        confidence=0.0,
    )
    assert score.matched_signals == ()
    assert score.matched_domains == ()
    assert score.matched_needs == ()
    assert score.contraindication_hits == ()
    assert score.recommendation_status == NOT_RECOMMENDED
    assert score.reason == ""


def test_pattern_fit_report_defaults():
    report = PatternFitReport(profile_id="profile_001")
    assert report.ranked_matches == ()
    assert report.recommended_patterns == ()
    assert report.caution_patterns == ()
    assert report.excluded_patterns == ()


def test_recommendation_constants():
    assert RECOMMENDED == "recommended"
    assert USE_WITH_CAUTION == "use_with_caution"
    assert NOT_RECOMMENDED == "not_recommended"


def test_tuple_fields_are_immutable_style_tuples():
    profile = PersonFitProfile(
        profile_id="profile_001",
        active_signals=("emotional_avoidance",),
        dominant_domains=("emotion_regulation",),
        risk_signals=("psychosis_risk",),
        needs=("acceptance",),
    )
    assert isinstance(profile.active_signals, tuple)
    assert isinstance(profile.dominant_domains, tuple)
    assert isinstance(profile.risk_signals, tuple)
    assert isinstance(profile.needs, tuple)

    score = PatternFitScore(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        fit_score=0.82,
        confidence=0.88,
        matched_signals=("emotional_avoidance",),
        matched_domains=("emotion_regulation",),
        matched_needs=("acceptance",),
        contraindication_hits=("acute_dissociation",),
    )
    assert isinstance(score.matched_signals, tuple)
    assert isinstance(score.matched_domains, tuple)
    assert isinstance(score.matched_needs, tuple)
    assert isinstance(score.contraindication_hits, tuple)


def test_explicit_values_are_preserved():
    profile = PersonFitProfile(
        profile_id="profile_002",
        active_signals=("low_agency", "shame"),
        dominant_domains=("self", "values_identity"),
        risk_signals=("mania_risk",),
        needs=("agency_restoration",),
        session_phase="exploration",
    )
    assert profile.active_signals == ("low_agency", "shame")
    assert profile.dominant_domains == ("self", "values_identity")
    assert profile.risk_signals == ("mania_risk",)
    assert profile.needs == ("agency_restoration",)
    assert profile.session_phase == "exploration"

    score = PatternFitScore(
        pattern_id="canonical_pattern_002",
        canonical_name="agency restoration",
        fit_score=0.91,
        confidence=0.87,
        matched_signals=("low_agency",),
        matched_domains=("self",),
        matched_needs=("agency_restoration",),
        contraindication_hits=(),
        recommendation_status=RECOMMENDED,
        reason="Strong signal overlap with low agency need.",
    )
    assert score.fit_score == 0.91
    assert score.recommendation_status == RECOMMENDED
    assert score.reason == "Strong signal overlap with low agency need."

    report = PatternFitReport(
        profile_id="profile_002",
        ranked_matches=(score,),
        recommended_patterns=(score,),
        caution_patterns=(),
        excluded_patterns=(),
    )
    assert report.profile_id == "profile_002"
    assert report.ranked_matches == (score,)
    assert report.recommended_patterns == (score,)


def test_empty_fit_report_is_deterministic():
    first = PatternFitReport(profile_id="profile_001")
    second = PatternFitReport(profile_id="profile_001")
    assert first == second
