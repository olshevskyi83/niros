"""Tests for Pattern–Person Fit library ranking."""

from __future__ import annotations

from niros.pattern_person_fit_contracts import PatternFitScore, PersonFitProfile
from niros.pattern_person_fit_ranking import rank_patterns_for_profile, sort_pattern_fit_scores
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


def test_empty_library_returns_empty_tuple():
    profile = _profile()
    library = build_universal_pattern_library(())
    assert rank_patterns_for_profile(profile, library) == ()


def test_single_pattern_returns_one_score():
    profile = _profile(active_signals=("emotional_avoidance",))
    pattern = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        target_signals=("emotional_avoidance",),
        confidence=0.85,
    )
    library = build_universal_pattern_library((pattern,))
    ranked = rank_patterns_for_profile(profile, library)
    assert len(ranked) == 1
    assert isinstance(ranked[0], PatternFitScore)
    assert ranked[0].pattern_id == "canonical_pattern_001"


def test_multiple_patterns_are_ranked_by_fit_score_descending():
    profile = _profile(
        active_signals=("emotional_avoidance", "shame"),
        dominant_domains=("emotion_regulation",),
        needs=("acceptance",),
    )
    high = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        confidence=0.90,
    )
    low = _pattern(
        pattern_id="canonical_pattern_002",
        canonical_name="clarify personal values",
        target_signals=("values_conflict",),
        fit_domains=("values_identity",),
        expected_effects=("clarity",),
        confidence=0.90,
    )
    library = build_universal_pattern_library((low, high))
    ranked = rank_patterns_for_profile(profile, library)
    assert [item.pattern_id for item in ranked] == [
        "canonical_pattern_001",
        "canonical_pattern_002",
    ]
    assert ranked[0].fit_score > ranked[1].fit_score


def test_confidence_is_tie_breaker_when_scores_equal():
    lower_confidence = PatternFitScore(
        pattern_id="canonical_pattern_002",
        canonical_name="accept painful emotions",
        fit_score=0.6000,
        confidence=0.70,
    )
    higher_confidence = PatternFitScore(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        fit_score=0.6000,
        confidence=0.90,
    )
    ranked = sort_pattern_fit_scores((lower_confidence, higher_confidence))
    assert ranked[0].fit_score == ranked[1].fit_score
    assert ranked[0].confidence > ranked[1].confidence
    assert ranked[0].pattern_id == "canonical_pattern_001"


def test_pattern_id_is_final_tie_breaker():
    profile = _profile(active_signals=("emotional_avoidance",))
    second = _pattern(
        pattern_id="canonical_pattern_002",
        canonical_name="accept painful emotions",
        target_signals=("emotional_avoidance",),
        confidence=0.80,
    )
    first = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        target_signals=("emotional_avoidance",),
        confidence=0.80,
    )
    library = build_universal_pattern_library((second, first))
    ranked = rank_patterns_for_profile(profile, library)
    assert ranked[0].fit_score == ranked[1].fit_score
    assert ranked[0].confidence == ranked[1].confidence
    assert [item.pattern_id for item in ranked] == [
        "canonical_pattern_001",
        "canonical_pattern_002",
    ]


def test_all_patterns_are_scored():
    profile = _profile(active_signals=("emotional_avoidance",))
    patterns = (
        _pattern(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            target_signals=("emotional_avoidance",),
        ),
        _pattern(
            pattern_id="canonical_pattern_002",
            canonical_name="clarify personal values",
            target_signals=("values_conflict",),
        ),
        _pattern(
            pattern_id="canonical_pattern_003",
            canonical_name="agency restoration",
            target_signals=("low_agency",),
        ),
    )
    library = build_universal_pattern_library(patterns)
    ranked = rank_patterns_for_profile(profile, library)
    assert len(ranked) == 3
    assert {item.pattern_id for item in ranked} == {
        "canonical_pattern_001",
        "canonical_pattern_002",
        "canonical_pattern_003",
    }


def test_output_is_deterministic():
    profile = _profile(
        active_signals=("emotional_avoidance",),
        dominant_domains=("emotion_regulation",),
    )
    patterns = (
        _pattern(
            pattern_id="canonical_pattern_002",
            canonical_name="clarify personal values",
            target_signals=("values_conflict",),
            fit_domains=("values_identity",),
        ),
        _pattern(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            target_signals=("emotional_avoidance",),
            fit_domains=("emotion_regulation",),
        ),
    )
    library = build_universal_pattern_library(patterns)
    first = rank_patterns_for_profile(profile, library)
    second = rank_patterns_for_profile(profile, library)
    assert first == second


def test_contraindicated_pattern_can_rank_lower_due_to_penalty():
    profile = _profile(
        active_signals=("emotional_avoidance", "shame"),
        dominant_domains=("emotion_regulation",),
        needs=("acceptance",),
        risk_signals=("psychosis_risk",),
    )
    safe = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        confidence=0.90,
    )
    contraindicated = _pattern(
        pattern_id="canonical_pattern_002",
        canonical_name="accept painful emotions with risk",
        target_signals=("emotional_avoidance", "shame"),
        fit_domains=("emotion_regulation",),
        expected_effects=("acceptance",),
        contraindication_signals=("psychosis_risk",),
        confidence=0.90,
    )
    library = build_universal_pattern_library((contraindicated, safe))
    ranked = rank_patterns_for_profile(profile, library)
    assert ranked[0].pattern_id == "canonical_pattern_001"
    assert ranked[1].pattern_id == "canonical_pattern_002"
    assert ranked[0].fit_score > ranked[1].fit_score


def test_ranked_output_contains_pattern_fit_score_objects():
    profile = _profile(active_signals=("emotional_avoidance",))
    pattern = _pattern(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        target_signals=("emotional_avoidance",),
    )
    library = build_universal_pattern_library((pattern,))
    ranked = rank_patterns_for_profile(profile, library)
    assert all(isinstance(item, PatternFitScore) for item in ranked)
