"""Approved Canonical Pattern — contract for human-reviewed therapeutic patterns."""

from __future__ import annotations

from dataclasses import dataclass

from niros_tle.pattern_review_queue import PatternReviewItem

APPROVED_STATUS = "approved"
READY_FOR_LIBRARY_STATUS = "ready_for_library"
DEFAULT_APPROVED_BY = "human_reviewer"


@dataclass(frozen=True)
class ApprovedCanonicalPattern:
    pattern_id: str
    canonical_name: str
    source_families: tuple[str, ...]
    member_pattern_ids: tuple[str, ...]
    confidence: float
    approval_status: str = APPROVED_STATUS
    approved_by: str = DEFAULT_APPROVED_BY
    reviewer_notes: str = ""
    library_status: str = READY_FOR_LIBRARY_STATUS


def approve_review_item(
    review_item: PatternReviewItem,
    *,
    approved_by: str = DEFAULT_APPROVED_BY,
    reviewer_notes: str = "",
) -> ApprovedCanonicalPattern:
    """Approve a review queue item for future library ingestion."""
    return ApprovedCanonicalPattern(
        pattern_id=review_item.pattern_id,
        canonical_name=review_item.canonical_name,
        source_families=review_item.source_families,
        member_pattern_ids=review_item.member_pattern_ids,
        confidence=review_item.confidence,
        approval_status=APPROVED_STATUS,
        approved_by=approved_by,
        reviewer_notes=reviewer_notes,
        library_status=READY_FOR_LIBRARY_STATUS,
    )
