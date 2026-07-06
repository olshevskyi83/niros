"""Tests for Universal Pattern contract."""

from __future__ import annotations

from niros_tle.approved_canonical_pattern import ApprovedCanonicalPattern, approve_review_item
from niros_tle.pattern_review_queue import PatternReviewItem
from niros_tle.universal_pattern import (
    ACTIVE_LIBRARY_STATUS,
    UNSPECIFIED_VALUE,
    UniversalPattern,
    build_universal_pattern,
)


def _approved_pattern() -> ApprovedCanonicalPattern:
    review_item = PatternReviewItem(
        review_id="pattern_review_001",
        pattern_id="canonical_pattern_001",
        canonical_name="accept painful emotions",
        source_families=("act", "cft", "ifs"),
        member_pattern_ids=("act_accept_001", "cft_accept_001", "ifs_accept_001"),
        confidence=0.8933,
        priority="high",
    )
    return approve_review_item(
        review_item,
        reviewer_notes="Cross-tradition acceptance wording confirmed.",
    )


def test_build_universal_pattern_creates_universal_pattern():
    pattern = build_universal_pattern(_approved_pattern())
    assert isinstance(pattern, UniversalPattern)


def test_pattern_id_preserved():
    approved = _approved_pattern()
    assert build_universal_pattern(approved).pattern_id == approved.pattern_id


def test_canonical_name_preserved():
    approved = _approved_pattern()
    assert build_universal_pattern(approved).canonical_name == approved.canonical_name


def test_source_families_preserved():
    approved = _approved_pattern()
    assert build_universal_pattern(approved).source_families == approved.source_families


def test_member_pattern_ids_preserved():
    approved = _approved_pattern()
    assert build_universal_pattern(approved).member_pattern_ids == approved.member_pattern_ids


def test_confidence_preserved():
    approved = _approved_pattern()
    assert build_universal_pattern(approved).confidence == approved.confidence


def test_target_signals_defaults_to_empty_tuple():
    assert build_universal_pattern(_approved_pattern()).target_signals == ()


def test_contraindication_signals_defaults_to_empty_tuple():
    assert build_universal_pattern(_approved_pattern()).contraindication_signals == ()


def test_fit_domains_defaults_to_empty_tuple():
    assert build_universal_pattern(_approved_pattern()).fit_domains == ()


def test_expected_effects_defaults_to_empty_tuple():
    assert build_universal_pattern(_approved_pattern()).expected_effects == ()


def test_intervention_style_defaults_to_unspecified():
    pattern = build_universal_pattern(_approved_pattern())
    assert pattern.intervention_style == UNSPECIFIED_VALUE
    assert pattern.intervention_style == "unspecified"


def test_session_phase_defaults_to_unspecified():
    pattern = build_universal_pattern(_approved_pattern())
    assert pattern.session_phase == UNSPECIFIED_VALUE
    assert pattern.session_phase == "unspecified"


def test_library_status_defaults_to_active():
    pattern = build_universal_pattern(_approved_pattern())
    assert pattern.library_status == ACTIVE_LIBRARY_STATUS
    assert pattern.library_status == "active"


def test_output_is_deterministic():
    approved = _approved_pattern()
    first = build_universal_pattern(approved)
    second = build_universal_pattern(approved)
    assert first == second
