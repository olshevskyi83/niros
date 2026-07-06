"""Tests for therapeutic function extraction contracts."""

from __future__ import annotations

from niros.therapeutic_extraction import (
    DEFAULT_EXTRACTOR,
    DEFAULT_REVIEW_STATUS,
    PENDING_HUMAN_REVIEW_STATUS,
    TherapeuticFunctionExtraction,
    build_ctpc_pattern_from_extraction,
    build_extraction_id,
    validate_extraction,
)


def _extraction(**overrides) -> TherapeuticFunctionExtraction:
    base = {
        "extraction_id": "extraction_source_001_segment_001_self_compassion",
        "source_id": "source_001",
        "segment_id": "segment_001",
        "therapeutic_function": "self_compassion",
        "evidence_text": "The chant invites gentle acceptance of suffering.",
        "generation_rules": ("Use second-person supportive phrasing.",),
        "voice_rules": ("Keep tempo slow.",),
        "symbolic_elements": ("water", "light"),
        "confidence": 0.82,
    }
    base.update(overrides)
    return TherapeuticFunctionExtraction(**base)


def test_default_values() -> None:
    extraction = TherapeuticFunctionExtraction(
        extraction_id="extraction_001",
        source_id="source_001",
        segment_id="segment_001",
        therapeutic_function="acceptance",
    )
    assert extraction.psychological_function == ""
    assert extraction.evidence_text == ""
    assert extraction.symbolic_elements == ()
    assert extraction.generation_rules == ()
    assert extraction.voice_rules == ()
    assert extraction.repetition_rules == ()
    assert extraction.pause_rules == ()
    assert extraction.candidate_targets == ()
    assert extraction.contraindications == ()
    assert extraction.confidence == 0.0
    assert extraction.extractor == DEFAULT_EXTRACTOR
    assert extraction.review_status == DEFAULT_REVIEW_STATUS


def test_validate_valid_extraction_returns_empty_tuple() -> None:
    assert validate_extraction(_extraction()) == ()


def test_validate_missing_required_fields_returns_issues() -> None:
    issues = validate_extraction(
        TherapeuticFunctionExtraction(
            extraction_id="",
            source_id="",
            segment_id="",
            therapeutic_function="",
            evidence_text="",
        )
    )
    assert "extraction_id must not be empty" in issues
    assert "source_id must not be empty" in issues
    assert "segment_id must not be empty" in issues
    assert "therapeutic_function must not be empty" in issues
    assert "evidence_text must not be empty" in issues


def test_validate_confidence_bounds() -> None:
    low = _extraction(confidence=-0.1)
    high = _extraction(confidence=1.1)
    assert "confidence must be between 0.0 and 1.0" in validate_extraction(low)
    assert "confidence must be between 0.0 and 1.0" in validate_extraction(high)


def test_build_extraction_id_deterministic() -> None:
    first = build_extraction_id("Source-001", "Segment 001", "Self Compassion")
    second = build_extraction_id("Source-001", "Segment 001", "Self Compassion")
    assert first == second
    assert first == "extraction_source_001_segment_001_self_compassion"


def test_build_ctpc_pattern_from_extraction_preserves_function() -> None:
    pattern = build_ctpc_pattern_from_extraction(_extraction())
    assert pattern.therapeutic_function == "self_compassion"
    assert pattern.name == "Self Compassion"


def test_build_ctpc_pattern_preserves_source_id_as_source_family() -> None:
    pattern = build_ctpc_pattern_from_extraction(_extraction())
    assert pattern.source_family == "source_001"


def test_build_ctpc_pattern_preserves_segment_id_as_source_reference() -> None:
    pattern = build_ctpc_pattern_from_extraction(_extraction())
    assert pattern.source_reference == "segment_001"


def test_build_ctpc_pattern_preserves_generation_rules() -> None:
    pattern = build_ctpc_pattern_from_extraction(_extraction())
    assert pattern.generation_rules == ("Use second-person supportive phrasing.",)


def test_build_ctpc_pattern_preserves_voice_rules() -> None:
    pattern = build_ctpc_pattern_from_extraction(_extraction())
    assert pattern.voice_rules == ("Keep tempo slow.",)


def test_build_ctpc_pattern_preserves_symbolic_elements() -> None:
    pattern = build_ctpc_pattern_from_extraction(_extraction())
    assert pattern.symbolic_elements == ("water", "light")


def test_build_ctpc_pattern_sets_pending_human_review() -> None:
    pattern = build_ctpc_pattern_from_extraction(_extraction())
    assert pattern.review_status == PENDING_HUMAN_REVIEW_STATUS
    assert pattern.evidence_level == "source_segment"


def test_build_ctpc_pattern_uses_provided_pattern_id() -> None:
    pattern = build_ctpc_pattern_from_extraction(_extraction(), pattern_id="custom_pattern_001")
    assert pattern.pattern_id == "custom_pattern_001"


def test_build_ctpc_pattern_default_pattern_id_deterministic() -> None:
    extraction = _extraction()
    first = build_ctpc_pattern_from_extraction(extraction)
    second = build_ctpc_pattern_from_extraction(extraction)
    assert first.pattern_id == "ctp_from_extraction_source_001_segment_001_self_compassion"
    assert first == second


def test_output_deterministic() -> None:
    extraction = _extraction()
    assert validate_extraction(extraction) == validate_extraction(extraction)
    assert build_ctpc_pattern_from_extraction(extraction) == build_ctpc_pattern_from_extraction(extraction)
