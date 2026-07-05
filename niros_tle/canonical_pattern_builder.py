"""Canonical Pattern Builder — convert similarity clusters into review-ready drafts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from niros_tle.pattern_similarity_engine import SimilarityCluster

PENDING_HUMAN_REVIEW = "pending_human_review"


@dataclass(frozen=True)
class CanonicalPatternDraft:
    pattern_id: str
    canonical_name: str
    member_pattern_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    representative_label: str
    evidence_source_count: int
    average_similarity: float
    confidence: float
    review_status: str = PENDING_HUMAN_REVIEW
    notes: str = ""


def build_canonical_pattern_drafts(
    similarity_clusters: Iterable[SimilarityCluster],
) -> tuple[CanonicalPatternDraft, ...]:
    """Build canonical pattern drafts from similarity clusters."""
    sorted_clusters = tuple(sorted(similarity_clusters, key=lambda cluster: cluster.cluster_id))
    if not sorted_clusters:
        return ()

    drafts: list[CanonicalPatternDraft] = []
    for index, cluster in enumerate(sorted_clusters, start=1):
        source_families = tuple(sorted(set(cluster.contributing_sources)))
        source_count = len(source_families)
        drafts.append(
            CanonicalPatternDraft(
                pattern_id=f"canonical_pattern_{index:03d}",
                canonical_name=cluster.suggested_canonical_name,
                member_pattern_ids=tuple(
                    sorted(member.pattern_id for member in cluster.members)
                ),
                source_families=source_families,
                representative_label=cluster.representative_label,
                evidence_source_count=source_count,
                average_similarity=cluster.average_similarity,
                confidence=calculate_confidence(
                    cluster.average_similarity,
                    source_count,
                ),
                review_status=PENDING_HUMAN_REVIEW,
                notes="",
            )
        )
    return tuple(drafts)


def calculate_confidence(average_similarity: float, source_count: int) -> float:
    """Deterministic confidence from cluster similarity and source diversity."""
    diversity_bonus = min(0.15, 0.03 * max(0, source_count - 1))
    bounded = min(1.0, max(0.0, average_similarity + diversity_bonus))
    return round(bounded, 4)
