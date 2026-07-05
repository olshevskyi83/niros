"""Tests for deterministic Pattern Similarity Engine."""

from __future__ import annotations

from niros_tle.candidate_pattern_builder import CandidatePattern
from niros_tle.pattern_similarity_engine import (
    DEFAULT_SIMILARITY_THRESHOLD,
    PatternSimilarityEngine,
    SimilarityInputPattern,
    cluster_patterns,
)


def _input_pattern(
    *,
    pattern_id: str,
    source_family: str,
    label: str,
    mechanism_description: str | None = None,
    therapeutic_intent: str = "",
) -> SimilarityInputPattern:
    return SimilarityInputPattern(
        pattern_id=pattern_id,
        source_family=source_family,
        label=label,
        mechanism_description=mechanism_description or label,
        therapeutic_intent=therapeutic_intent,
    )


def _candidate_pattern(
    *,
    candidate_id: str,
    source_family: str,
    proposed_name: str,
    therapeutic_goal: str = "",
    evidence_summary: str = "",
) -> CandidatePattern:
    return CandidatePattern(
        candidate_id=candidate_id,
        source_document=f"{source_family}_sample_txt",
        source_family=source_family,
        meaning_unit_ids=(f"{candidate_id}_mu_001",),
        proposed_name=proposed_name,
        psychological_functions=("acceptance",),
        language_mechanisms=("permission_based",),
        therapeutic_goal=therapeutic_goal or proposed_name,
        possible_good_for=("emotional_avoidance",),
        possible_avoid_for=("psychosis_risk",),
        confidence="medium",
        supporting_evidence=(
            {
                "meaning_unit_id": f"{candidate_id}_mu_001",
                "summary": evidence_summary or proposed_name,
            },
        ),
        status="candidate",
    )


def _acceptance_candidates() -> tuple[SimilarityInputPattern, ...]:
    return (
        _input_pattern(
            pattern_id="act_accept_001",
            source_family="act",
            label="accept painful emotions",
            therapeutic_intent="reduce struggle with painful internal experience",
        ),
        _input_pattern(
            pattern_id="cft_accept_001",
            source_family="cft",
            label="accept difficult internal experience",
            therapeutic_intent="reduce threat response to difficult emotion",
        ),
        _input_pattern(
            pattern_id="ifs_accept_001",
            source_family="ifs",
            label="allow unwanted feelings to be present",
            therapeutic_intent="allow protective part to soften toward emotion",
        ),
    )


def _unrelated_candidates() -> tuple[SimilarityInputPattern, ...]:
    return (
        _input_pattern(
            pattern_id="act_values_001",
            source_family="act",
            label="clarify personal values",
        ),
        _input_pattern(
            pattern_id="cbt_activation_001",
            source_family="cbt",
            label="increase behavioral activation",
        ),
        _input_pattern(
            pattern_id="ifs_attachment_001",
            source_family="ifs",
            label="repair attachment rupture",
        ),
    )


def test_empty_input_returns_empty_list():
    assert PatternSimilarityEngine().cluster(()) == ()
    assert cluster_patterns(()) == ()


def test_single_mechanism_returns_one_cluster():
    pattern = _input_pattern(
        pattern_id="act_accept_001",
        source_family="act",
        label="accept painful emotions",
    )
    clusters = PatternSimilarityEngine().cluster((pattern,))
    assert len(clusters) == 1
    assert len(clusters[0].members) == 1
    assert clusters[0].average_similarity == 1.0


def test_identical_mechanisms_cluster_together():
    patterns = (
        _input_pattern(
            pattern_id="act_accept_001",
            source_family="act",
            label="accept painful emotions",
        ),
        _input_pattern(
            pattern_id="cft_accept_002",
            source_family="cft",
            label="accept painful emotions",
        ),
    )
    clusters = PatternSimilarityEngine().cluster(patterns)
    assert len(clusters) == 1
    assert len(clusters[0].members) == 2
    assert clusters[0].suggested_canonical_name == "accept painful emotions"


def test_similar_mechanisms_cluster_together():
    clusters = PatternSimilarityEngine(threshold=DEFAULT_SIMILARITY_THRESHOLD).cluster(
        _acceptance_candidates()
    )
    assert len(clusters) == 1
    assert len(clusters[0].members) == 3
    assert clusters[0].contributing_sources == ("act", "cft", "ifs")
    assert "accept" in clusters[0].suggested_canonical_name


def test_unrelated_mechanisms_do_not_cluster_together():
    clusters = PatternSimilarityEngine(threshold=DEFAULT_SIMILARITY_THRESHOLD).cluster(
        _unrelated_candidates()
    )
    assert len(clusters) == 3


def test_clustering_is_deterministic():
    patterns = _acceptance_candidates() + _unrelated_candidates()
    first = PatternSimilarityEngine().cluster(patterns)
    second = PatternSimilarityEngine().cluster(patterns)
    assert [cluster.cluster_id for cluster in first] == [cluster.cluster_id for cluster in second]
    assert [cluster.suggested_canonical_name for cluster in first] == [
        cluster.suggested_canonical_name for cluster in second
    ]


def test_threshold_affects_clustering():
    patterns = _acceptance_candidates()
    strict = PatternSimilarityEngine(threshold=0.95).cluster(patterns)
    relaxed = PatternSimilarityEngine(threshold=0.55).cluster(patterns)
    assert len(strict) >= len(relaxed)
    assert len(relaxed) == 1


def test_contributing_sources_are_preserved():
    clusters = PatternSimilarityEngine().cluster(_acceptance_candidates())
    assert clusters[0].contributing_sources == ("act", "cft", "ifs")


def test_cluster_patterns_accepts_candidate_patterns():
    candidates = (
        _candidate_pattern(
            candidate_id="candidate_act_accept_001",
            source_family="act",
            proposed_name="accept painful emotions",
            therapeutic_goal="reduce struggle with painful internal experience",
        ),
        _candidate_pattern(
            candidate_id="candidate_cft_accept_001",
            source_family="cft",
            proposed_name="accept difficult internal experience",
            therapeutic_goal="reduce threat response to difficult emotion",
        ),
        _candidate_pattern(
            candidate_id="candidate_ifs_accept_001",
            source_family="ifs",
            proposed_name="allow unwanted feelings to be present",
            therapeutic_goal="allow protective part to soften toward emotion",
        ),
    )
    clusters = cluster_patterns(candidates)
    assert len(clusters) == 1
    assert clusters[0].contributing_sources == ("act", "cft", "ifs")


def test_similarity_score_is_bounded_and_deterministic():
    left = _acceptance_candidates()[0]
    right = _acceptance_candidates()[1]
    score = PatternSimilarityEngine().score(left, right)
    assert 0.0 <= score <= 1.0
    assert score == PatternSimilarityEngine().score(left, right)
    assert score >= DEFAULT_SIMILARITY_THRESHOLD

    unrelated = _unrelated_candidates()[0]
    low_score = PatternSimilarityEngine().score(left, unrelated)
    assert low_score < DEFAULT_SIMILARITY_THRESHOLD


def test_from_candidate_pattern_preserves_similarity_fields():
    candidate = _candidate_pattern(
        candidate_id="candidate_act_accept_001",
        source_family="act",
        proposed_name="accept painful emotions",
        therapeutic_goal="reduce struggle with painful internal experience",
    )
    adapted = SimilarityInputPattern.from_candidate_pattern(candidate)
    assert adapted.pattern_id == candidate.candidate_id
    assert adapted.source_family == candidate.source_family
    assert adapted.label == candidate.proposed_name
    assert adapted.therapeutic_intent == candidate.therapeutic_goal
    assert candidate.proposed_name in adapted.mechanism_description
    assert "acceptance" in adapted.mechanism_description
