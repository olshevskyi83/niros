"""Tests for Pattern Review Queue."""

from __future__ import annotations

from niros_tle.canonical_pattern_builder import PENDING_HUMAN_REVIEW, CanonicalPatternDraft
from niros_tle.pattern_review_queue import (
    HIGH_PRIORITY,
    LOW_PRIORITY,
    MEDIUM_PRIORITY,
    PatternReviewItem,
    build_pattern_review_queue,
    calculate_priority,
)


def _draft(
    *,
    pattern_id: str,
    canonical_name: str,
    confidence: float,
    source_families: tuple[str, ...] = ("act",),
    member_pattern_ids: tuple[str, ...] = ("act_accept_001",),
    review_status: str = PENDING_HUMAN_REVIEW,
) -> CanonicalPatternDraft:
    return CanonicalPatternDraft(
        pattern_id=pattern_id,
        canonical_name=canonical_name,
        member_pattern_ids=member_pattern_ids,
        source_families=source_families,
        representative_label=canonical_name,
        evidence_source_count=len(source_families),
        average_similarity=confidence,
        confidence=confidence,
        review_status=review_status,
        notes="",
    )


def test_empty_input_returns_empty_tuple():
    assert build_pattern_review_queue(()) == ()


def test_single_draft_creates_one_review_item():
    draft = _draft(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        confidence=0.88,
    )
    queue = build_pattern_review_queue((draft,))
    assert len(queue) == 1
    assert isinstance(queue[0], PatternReviewItem)


def test_review_id_is_deterministic():
    drafts = (
        _draft(
            pattern_id="canonical_pattern_002",
            canonical_name="clarify personal values",
            confidence=0.70,
        ),
        _draft(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            confidence=0.90,
        ),
    )
    queue = build_pattern_review_queue(drafts)
    assert [item.review_id for item in queue] == [
        "pattern_review_001",
        "pattern_review_002",
    ]


def test_source_families_preserved():
    draft = _draft(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        confidence=0.88,
        source_families=("act", "cft", "ifs"),
    )
    item = build_pattern_review_queue((draft,))[0]
    assert item.source_families == ("act", "cft", "ifs")


def test_member_pattern_ids_preserved():
    draft = _draft(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        confidence=0.88,
        member_pattern_ids=("act_accept_001", "cft_accept_001", "ifs_accept_001"),
    )
    item = build_pattern_review_queue((draft,))[0]
    assert item.member_pattern_ids == ("act_accept_001", "cft_accept_001", "ifs_accept_001")


def test_review_status_defaults_to_pending_human_review():
    item = build_pattern_review_queue(
        (
            _draft(
                pattern_id="canonical_pattern_001",
                canonical_name="accept painful emotions",
                confidence=0.88,
            ),
        )
    )[0]
    assert item.review_status == PENDING_HUMAN_REVIEW
    assert item.review_status == "pending_human_review"


def test_reviewer_notes_defaults_to_empty_string():
    item = build_pattern_review_queue(
        (
            _draft(
                pattern_id="canonical_pattern_001",
                canonical_name="accept painful emotions",
                confidence=0.88,
            ),
        )
    )[0]
    assert item.reviewer_notes == ""


def test_high_priority_threshold():
    assert calculate_priority(0.85) == HIGH_PRIORITY
    assert calculate_priority(0.95) == HIGH_PRIORITY


def test_medium_priority_threshold():
    assert calculate_priority(0.65) == MEDIUM_PRIORITY
    assert calculate_priority(0.84) == MEDIUM_PRIORITY


def test_low_priority_threshold():
    assert calculate_priority(0.64) == LOW_PRIORITY
    assert calculate_priority(0.10) == LOW_PRIORITY


def test_queue_sorted_by_confidence_descending():
    drafts = (
        _draft(
            pattern_id="canonical_pattern_003",
            canonical_name="repair attachment rupture",
            confidence=0.60,
        ),
        _draft(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            confidence=0.90,
        ),
        _draft(
            pattern_id="canonical_pattern_002",
            canonical_name="clarify personal values",
            confidence=0.75,
        ),
    )
    queue = build_pattern_review_queue(drafts)
    assert [item.confidence for item in queue] == [0.90, 0.75, 0.60]


def test_tie_breaker_sorted_by_pattern_id_ascending():
    drafts = (
        _draft(
            pattern_id="canonical_pattern_002",
            canonical_name="clarify personal values",
            confidence=0.80,
        ),
        _draft(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            confidence=0.80,
        ),
    )
    queue = build_pattern_review_queue(drafts)
    assert [item.pattern_id for item in queue] == [
        "canonical_pattern_001",
        "canonical_pattern_002",
    ]


def test_output_is_deterministic():
    drafts = (
        _draft(
            pattern_id="canonical_pattern_002",
            canonical_name="clarify personal values",
            confidence=0.70,
        ),
        _draft(
            pattern_id="canonical_pattern_001",
            canonical_name="accept painful emotions",
            confidence=0.90,
        ),
    )
    first = build_pattern_review_queue(drafts)
    second = build_pattern_review_queue(reversed(drafts))
    assert first == second


def test_review_item_preserves_draft_metadata():
    draft = _draft(
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        confidence=0.88,
        source_families=("act", "cft", "ifs"),
        member_pattern_ids=("act_accept_001", "cft_accept_001"),
    )
    item = build_pattern_review_queue((draft,))[0]
    assert item.pattern_id == draft.pattern_id
    assert item.canonical_name == draft.canonical_name
    assert item.confidence == draft.confidence
    assert item.priority == HIGH_PRIORITY
