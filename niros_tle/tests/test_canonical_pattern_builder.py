"""Tests for Canonical Pattern Builder."""

from __future__ import annotations

from niros_tle.canonical_pattern_builder import (
    PENDING_HUMAN_REVIEW,
    CanonicalPatternDraft,
    build_canonical_pattern_drafts,
    calculate_confidence,
)
from niros_tle.pattern_similarity_engine import SimilarityCluster, SimilarityMatch


def _similarity_cluster(
    *,
    cluster_id: str,
    representative_label: str,
    suggested_canonical_name: str,
    members: tuple[SimilarityMatch, ...],
    contributing_sources: tuple[str, ...],
    average_similarity: float,
) -> SimilarityCluster:
    return SimilarityCluster(
        cluster_id=cluster_id,
        representative_label=representative_label,
        members=members,
        contributing_sources=contributing_sources,
        average_similarity=average_similarity,
        suggested_canonical_name=suggested_canonical_name,
    )


def _member(
    *,
    pattern_id: str,
    source_family: str,
    label: str,
    similarity_score: float = 0.9,
) -> SimilarityMatch:
    return SimilarityMatch(
        pattern_id=pattern_id,
        source_family=source_family,
        label=label,
        similarity_score=similarity_score,
    )


def _acceptance_cluster() -> SimilarityCluster:
    return _similarity_cluster(
        cluster_id="similarity_cluster_001",
        representative_label="accept painful emotions",
        suggested_canonical_name="accept painful emotions",
        members=(
            _member(
                pattern_id="act_accept_001",
                source_family="act",
                label="accept painful emotions",
            ),
            _member(
                pattern_id="cft_accept_001",
                source_family="cft",
                label="accept difficult internal experience",
                similarity_score=0.82,
            ),
            _member(
                pattern_id="ifs_accept_001",
                source_family="ifs",
                label="allow unwanted feelings to be present",
                similarity_score=0.78,
            ),
        ),
        contributing_sources=("act", "cft", "ifs"),
        average_similarity=0.8333,
    )


def test_empty_input_returns_empty_tuple():
    assert build_canonical_pattern_drafts(()) == ()


def test_single_cluster_creates_one_draft():
    drafts = build_canonical_pattern_drafts((_acceptance_cluster(),))
    assert len(drafts) == 1
    assert drafts[0].pattern_id == "canonical_pattern_001"


def test_member_pattern_ids_are_preserved():
    draft = build_canonical_pattern_drafts((_acceptance_cluster(),))[0]
    assert draft.member_pattern_ids == (
        "act_accept_001",
        "cft_accept_001",
        "ifs_accept_001",
    )


def test_source_families_are_sorted_and_preserved():
    draft = build_canonical_pattern_drafts((_acceptance_cluster(),))[0]
    assert draft.source_families == ("act", "cft", "ifs")


def test_evidence_source_count_is_correct():
    draft = build_canonical_pattern_drafts((_acceptance_cluster(),))[0]
    assert draft.evidence_source_count == 3


def test_canonical_name_comes_from_suggested_canonical_name():
    draft = build_canonical_pattern_drafts((_acceptance_cluster(),))[0]
    assert draft.canonical_name == "accept painful emotions"


def test_confidence_is_bounded_between_zero_and_one():
    draft = build_canonical_pattern_drafts((_acceptance_cluster(),))[0]
    assert 0.0 <= draft.confidence <= 1.0
    assert calculate_confidence(1.5, 4) == 1.0
    assert calculate_confidence(-0.5, 1) == 0.0


def test_confidence_increases_with_source_diversity():
    single_source = calculate_confidence(0.80, 1)
    multi_source = calculate_confidence(0.80, 3)
    assert multi_source > single_source
    assert multi_source == round(min(1.0, 0.80 + min(0.15, 0.03 * 2)), 4)


def test_output_is_deterministic():
    clusters = (
        _acceptance_cluster(),
        _similarity_cluster(
            cluster_id="similarity_cluster_002",
            representative_label="clarify personal values",
            suggested_canonical_name="clarify personal values",
            members=(
                _member(
                    pattern_id="act_values_001",
                    source_family="act",
                    label="clarify personal values",
                ),
            ),
            contributing_sources=("act",),
            average_similarity=1.0,
        ),
    )
    first = build_canonical_pattern_drafts(clusters)
    second = build_canonical_pattern_drafts(reversed(clusters))
    assert first == second


def test_review_status_defaults_to_pending_human_review():
    draft = build_canonical_pattern_drafts((_acceptance_cluster(),))[0]
    assert draft.review_status == PENDING_HUMAN_REVIEW
    assert draft.review_status == "pending_human_review"


def test_draft_fields_match_cluster_metadata():
    cluster = _acceptance_cluster()
    draft = build_canonical_pattern_drafts((cluster,))[0]
    assert isinstance(draft, CanonicalPatternDraft)
    assert draft.representative_label == cluster.representative_label
    assert draft.average_similarity == cluster.average_similarity
    assert draft.notes == ""
