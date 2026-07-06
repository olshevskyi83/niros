"""Tests for Approved Canonical Pattern contract."""

from __future__ import annotations

from niros_tle.approved_canonical_pattern import (
    APPROVED_STATUS,
    DEFAULT_APPROVED_BY,
    READY_FOR_LIBRARY_STATUS,
    ApprovedCanonicalPattern,
    approve_review_item,
)
from niros_tle.canonical_pattern_builder import PENDING_HUMAN_REVIEW
from niros_tle.pattern_review_queue import PatternReviewItem


def _review_item(
    *,
    pattern_id: str = "canonical_pattern_001",
    canonical_name: str = "accept painful emotions",
    source_families: tuple[str, ...] = ("act", "cft", "ifs"),
    member_pattern_ids: tuple[str, ...] = (
        "act_accept_001",
        "cft_accept_001",
        "ifs_accept_001",
    ),
    confidence: float = 0.8933,
    review_status: str = PENDING_HUMAN_REVIEW,
) -> PatternReviewItem:
    return PatternReviewItem(
        review_id="pattern_review_001",
        pattern_id=pattern_id,
        canonical_name=canonical_name,
        source_families=source_families,
        member_pattern_ids=member_pattern_ids,
        confidence=confidence,
        review_status=review_status,
        priority="high",
        reviewer_notes="",
    )


def test_approve_review_item_creates_approved_canonical_pattern():
    approved = approve_review_item(_review_item())
    assert isinstance(approved, ApprovedCanonicalPattern)


def test_pattern_id_preserved():
    item = _review_item(pattern_id="canonical_pattern_007")
    assert approve_review_item(item).pattern_id == "canonical_pattern_007"


def test_canonical_name_preserved():
    item = _review_item(canonical_name="accept difficult internal experience")
    assert approve_review_item(item).canonical_name == "accept difficult internal experience"


def test_source_families_preserved():
    item = _review_item(source_families=("act", "cft", "ifs"))
    assert approve_review_item(item).source_families == ("act", "cft", "ifs")


def test_member_pattern_ids_preserved():
    member_ids = ("act_accept_001", "cft_accept_001", "ifs_accept_001")
    item = _review_item(member_pattern_ids=member_ids)
    assert approve_review_item(item).member_pattern_ids == member_ids


def test_confidence_preserved():
    item = _review_item(confidence=0.8933)
    assert approve_review_item(item).confidence == 0.8933


def test_approval_status_defaults_to_approved():
    approved = approve_review_item(_review_item())
    assert approved.approval_status == APPROVED_STATUS
    assert approved.approval_status == "approved"


def test_library_status_defaults_to_ready_for_library():
    approved = approve_review_item(_review_item())
    assert approved.library_status == READY_FOR_LIBRARY_STATUS
    assert approved.library_status == "ready_for_library"


def test_approved_by_defaults_to_human_reviewer():
    approved = approve_review_item(_review_item())
    assert approved.approved_by == DEFAULT_APPROVED_BY
    assert approved.approved_by == "human_reviewer"


def test_approved_by_can_be_overridden():
    approved = approve_review_item(_review_item(), approved_by="clinical_lead")
    assert approved.approved_by == "clinical_lead"


def test_reviewer_notes_defaults_to_empty_string():
    approved = approve_review_item(_review_item())
    assert approved.reviewer_notes == ""


def test_reviewer_notes_can_be_provided():
    approved = approve_review_item(
        _review_item(),
        reviewer_notes="Cross-tradition acceptance wording confirmed.",
    )
    assert approved.reviewer_notes == "Cross-tradition acceptance wording confirmed."


def test_output_is_deterministic():
    item = _review_item()
    first = approve_review_item(
        item,
        approved_by="clinical_lead",
        reviewer_notes="Confirmed.",
    )
    second = approve_review_item(
        item,
        approved_by="clinical_lead",
        reviewer_notes="Confirmed.",
    )
    assert first == second


def test_approval_allowed_when_review_status_is_not_pending():
    item = _review_item(review_status="approved")
    approved = approve_review_item(item)
    assert approved.approval_status == "approved"
    assert approved.pattern_id == item.pattern_id
