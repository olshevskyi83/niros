from niros.human_profile_summary import (
    NO_EVIDENCE_PROFILE_TEXT,
    PATTERN_INTERPRETATIONS,
    build_human_profile_summary,
)
from niros.models import SupportedLanguage
from niros.patterns import PatternTag


def _pattern_tag(
    tag_id: str,
    canonical_id: str,
    confidence: float = 1.0,
) -> PatternTag:
    return PatternTag(
        id=tag_id,
        session_id="session-001",
        evidence_id="session-001:evidence:0",
        canonical_id=canonical_id,
        matched_text="example",
        confidence=confidence,
        language=SupportedLanguage.ENGLISH,
    )


def test_no_patterns_returns_no_evidence_summary():
    summary = build_human_profile_summary([])

    assert summary["primary_pattern"] is None
    assert summary["secondary_patterns"] == []
    assert summary["pattern_counts"] == {}
    assert summary["profile_text"] == NO_EVIDENCE_PROFILE_TEXT


def test_single_pattern_becomes_primary():
    summary = build_human_profile_summary([_pattern_tag("tag-1", "identity_uncertainty")])

    assert summary["primary_pattern"]["canonical_id"] == "identity_uncertainty"
    assert summary["secondary_patterns"] == []
    assert summary["pattern_counts"] == {"identity_uncertainty": 1}


def test_repeated_pattern_beats_single_pattern():
    tags = [
        _pattern_tag("tag-1", "identity_uncertainty"),
        _pattern_tag("tag-2", "identity_uncertainty"),
        _pattern_tag("tag-3", "low_self_efficacy"),
    ]

    summary = build_human_profile_summary(tags)

    assert summary["primary_pattern"]["canonical_id"] == "identity_uncertainty"
    assert summary["pattern_counts"]["identity_uncertainty"] == 2
    assert summary["pattern_counts"]["low_self_efficacy"] == 1


def test_tie_uses_confidence():
    tags = [
        _pattern_tag("tag-1", "identity_uncertainty", confidence=0.7),
        _pattern_tag("tag-2", "low_self_efficacy", confidence=0.9),
    ]

    summary = build_human_profile_summary(tags)

    assert summary["primary_pattern"]["canonical_id"] == "low_self_efficacy"
    assert summary["secondary_patterns"][0]["canonical_id"] == "identity_uncertainty"


def test_secondary_patterns_are_included():
    tags = [
        _pattern_tag("tag-1", "identity_uncertainty"),
        _pattern_tag("tag-2", "identity_uncertainty"),
        _pattern_tag("tag-3", "low_self_efficacy"),
        _pattern_tag("tag-4", "shame_sensitivity"),
    ]

    summary = build_human_profile_summary(tags)

    secondary_ids = [pattern["canonical_id"] for pattern in summary["secondary_patterns"]]
    assert secondary_ids == ["low_self_efficacy", "shame_sensitivity"]


def test_identity_uncertainty_returns_expected_interpretation_text():
    summary = build_human_profile_summary([_pattern_tag("tag-1", "identity_uncertainty")])

    assert summary["profile_text"] == PATTERN_INTERPRETATIONS["identity_uncertainty"]
