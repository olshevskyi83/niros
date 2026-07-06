"""Pattern Review Queue — prepare canonical drafts for human review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from niros_tle.canonical_pattern_builder import PENDING_HUMAN_REVIEW, CanonicalPatternDraft

HIGH_PRIORITY = "high"
MEDIUM_PRIORITY = "medium"
LOW_PRIORITY = "low"


@dataclass(frozen=True)
class PatternReviewItem:
    review_id: str
    pattern_id: str
    canonical_name: str
    source_families: tuple[str, ...]
    member_pattern_ids: tuple[str, ...]
    confidence: float
    review_status: str = PENDING_HUMAN_REVIEW
    priority: str = LOW_PRIORITY
    reviewer_notes: str = ""


def build_pattern_review_queue(
    canonical_pattern_drafts: Iterable[CanonicalPatternDraft],
) -> tuple[PatternReviewItem, ...]:
    """Build a deterministic review queue from canonical pattern drafts."""
    sorted_drafts = tuple(
        sorted(
            canonical_pattern_drafts,
            key=lambda draft: (-draft.confidence, draft.pattern_id),
        )
    )
    if not sorted_drafts:
        return ()

    return tuple(
        PatternReviewItem(
            review_id=f"pattern_review_{index:03d}",
            pattern_id=draft.pattern_id,
            canonical_name=draft.canonical_name,
            source_families=draft.source_families,
            member_pattern_ids=draft.member_pattern_ids,
            confidence=draft.confidence,
            review_status=draft.review_status,
            priority=calculate_priority(draft.confidence),
            reviewer_notes="",
        )
        for index, draft in enumerate(sorted_drafts, start=1)
    )


def calculate_priority(confidence: float) -> str:
    """Deterministic review priority from draft confidence."""
    if confidence >= 0.85:
        return HIGH_PRIORITY
    if confidence >= 0.65:
        return MEDIUM_PRIORITY
    return LOW_PRIORITY
