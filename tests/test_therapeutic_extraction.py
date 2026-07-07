"""Tests for therapeutic function extraction contracts."""

from __future__ import annotations

from niros.therapeutic_extraction import (
    DEFAULT_EXTRACTOR,
    DEFAULT_REVIEW_STATUS,
    MAX_SAFE_ARTIFACT_ID_LENGTH,
    PENDING_HUMAN_REVIEW_STATUS,
    TherapeuticFunctionExtraction,
    build_ctpc_pattern_from_extraction,
    build_extraction_id,
    validate_extraction,
)
from niros.human_review_workflow import HumanReviewWorkflow, build_review_id


def _extraction(**overrides) -> TherapeuticFunctionExtraction:
    source_id = overrides.get("source_id", "source_001")
    segment_id = overrides.get("segment_id", "segment_001")
    therapeutic_function = overrides.get("therapeutic_function", "self_compassion")
    psychological_function = overrides.get("psychological_function", "")
    base = {
        "extraction_id": build_extraction_id(
            source_id,
            segment_id,
            therapeutic_function,
            psychological_function,
        ),
        "source_id": source_id,
        "segment_id": segment_id,
        "therapeutic_function": therapeutic_function,
        "psychological_function": psychological_function,
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
    assert first.startswith("extraction_source_001_segment_001_")
    assert first.rsplit("_", 1)[-1] == "e3838d2b"


def test_long_therapeutic_function_produces_short_extraction_id() -> None:
    long_function = "self_compassion " * 200
    extraction_id = build_extraction_id(
        "source_maria_sabina_chants",
        "source_maria_sabina_chants_batch_003",
        long_function,
        "reduce self-criticism",
    )
    review_id = build_review_id(extraction_id)
    pattern_id = f"ctp_from_{extraction_id}"

    assert len(extraction_id) < MAX_SAFE_ARTIFACT_ID_LENGTH
    assert len(review_id) < MAX_SAFE_ARTIFACT_ID_LENGTH
    assert len(pattern_id) < MAX_SAFE_ARTIFACT_ID_LENGTH
    assert extraction_id.endswith(extraction_id.rsplit("_", 1)[-1])
    assert len(extraction_id.rsplit("_", 1)[-1]) == 8


def test_review_json_saves_with_long_therapeutic_function(tmp_path) -> None:
    long_function = "therapeutic release through symbolic water imagery " * 50
    extraction = _extraction(
        source_id="source_maria_sabina_chants",
        segment_id="source_maria_sabina_chants_batch_003",
        therapeutic_function=long_function,
        psychological_function="reduce self-criticism",
    )
    workflow = HumanReviewWorkflow(
        workspace_root=str(tmp_path / "knowledge_factory"),
        timestamp_fn=lambda: "2026-07-06T12:00:00+00:00",
    )
    review = workflow.create_pending_review(extraction)
    saved_path = workflow.save_review(review)

    assert saved_path.exists()
    assert len(saved_path.name) < MAX_SAFE_ARTIFACT_ID_LENGTH


def test_existing_manual_extraction_id_still_validates() -> None:
    legacy = TherapeuticFunctionExtraction(
        extraction_id="extraction_source_001_segment_001_self_compassion",
        source_id="source_001",
        segment_id="segment_001",
        therapeutic_function="self_compassion",
        evidence_text="Legacy extraction id remains valid.",
    )
    assert validate_extraction(legacy) == ()


def test_ctpc_compiler_filename_stays_under_safe_length() -> None:
    long_function = "acceptance and release " * 100
    extraction = _extraction(
        source_id="source_maria_sabina_chants",
        segment_id="source_maria_sabina_chants_batch_003",
        therapeutic_function=long_function,
    )
    pattern = build_ctpc_pattern_from_extraction(extraction)
    filename = f"{pattern.pattern_id}.json"

    assert len(filename) < MAX_SAFE_ARTIFACT_ID_LENGTH


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
    assert first.pattern_id == f"ctp_from_{extraction.extraction_id}"
    assert first == second


def test_output_deterministic() -> None:
    extraction = _extraction()
    assert validate_extraction(extraction) == validate_extraction(extraction)
    assert build_ctpc_pattern_from_extraction(extraction) == build_ctpc_pattern_from_extraction(extraction)
