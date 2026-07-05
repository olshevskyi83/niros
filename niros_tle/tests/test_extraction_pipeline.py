"""Tests for Universal Pattern Extraction Pipeline."""

from __future__ import annotations

import json

import pytest

from niros_tle.extraction_pipeline import (
    ExtractionPipelineResult,
    SourceFragment,
    UniversalPatternExtractionPipeline,
)
from niros_tle.pattern_contract import validate_tle_pattern_record

ACCEPTANCE_FRAGMENT = SourceFragment(
    source_family="act",
    source_reference="act_conceptual_fragment_01",
    language="en",
    fragment_text="You do not need to fight every thought.",
    metadata={"stage": "placeholder"},
)

MULTI_UNIT_FRAGMENT = SourceFragment(
    source_family="act",
    source_reference="act_conceptual_fragment_02",
    language="en",
    fragment_text="You may pause. You do not need to fight every thought.",
    metadata={"stage": "placeholder"},
)


@pytest.fixture
def pipeline() -> UniversalPatternExtractionPipeline:
    return UniversalPatternExtractionPipeline()


def test_source_fragment_created():
    fragment = ACCEPTANCE_FRAGMENT
    assert fragment.source_family == "act"
    assert fragment.fragment_text.startswith("You do not need")


def test_meaning_units_produced(pipeline: UniversalPatternExtractionPipeline):
    units = pipeline.extract_meaning_units(ACCEPTANCE_FRAGMENT)
    assert len(units) == 1
    assert units[0].provisional_function == "acceptance"


def test_candidate_pattern_produced(pipeline: UniversalPatternExtractionPipeline):
    units = pipeline.extract_meaning_units(ACCEPTANCE_FRAGMENT)
    candidate = pipeline.build_candidate_pattern(ACCEPTANCE_FRAGMENT, units)
    assert candidate.pattern_id == "acceptance_loop"
    assert "acceptance" in candidate.psychological_function


def test_validation_stage_executed(pipeline: UniversalPatternExtractionPipeline):
    units = pipeline.extract_meaning_units(ACCEPTANCE_FRAGMENT)
    candidate = pipeline.build_candidate_pattern(ACCEPTANCE_FRAGMENT, units)
    validated = pipeline.validate_candidate(ACCEPTANCE_FRAGMENT, candidate, units)
    assert validated.is_valid is True
    assert validated.validation_notes


def test_tle_pattern_record_exported(pipeline: UniversalPatternExtractionPipeline):
    result = pipeline.extract_from_fragment(ACCEPTANCE_FRAGMENT)
    assert result.tle_pattern_record is not None
    assert result.tle_pattern_record.id == "acceptance_loop"
    validate_tle_pattern_record(result.tle_pattern_record)


def test_empty_fragment_handled_safely(pipeline: UniversalPatternExtractionPipeline):
    empty_fragment = SourceFragment(
        source_family="act",
        source_reference="empty",
        language="en",
        fragment_text="   ",
    )
    result = pipeline.extract_from_fragment(empty_fragment)
    assert result.meaning_units == ()
    assert result.candidate_pattern is None
    assert result.tle_pattern_record is None
    assert result.validated_pattern is not None
    assert result.validated_pattern.is_valid is False


def test_multiple_meaning_units_supported(pipeline: UniversalPatternExtractionPipeline):
    result = pipeline.extract_from_fragment(MULTI_UNIT_FRAGMENT)
    assert len(result.meaning_units) == 2
    functions = {unit.provisional_function for unit in result.meaning_units}
    assert "permission" in functions
    assert "acceptance" in functions
    assert result.candidate_pattern is not None
    assert len(result.candidate_pattern.evidence_units) == 2


def test_deterministic_output(pipeline: UniversalPatternExtractionPipeline):
    first = pipeline.extract_from_fragment(ACCEPTANCE_FRAGMENT)
    second = pipeline.extract_from_fragment(ACCEPTANCE_FRAGMENT)
    assert first.tle_pattern_record is not None
    assert second.tle_pattern_record is not None
    assert first.tle_pattern_record.to_dict() == second.tle_pattern_record.to_dict()


def test_no_copyrighted_text_stored_outside_source_fragment(
    pipeline: UniversalPatternExtractionPipeline,
):
    result = pipeline.extract_from_fragment(ACCEPTANCE_FRAGMENT)
    assert result.tle_pattern_record is not None

    serialized = json.dumps(result.tle_pattern_record.to_dict())
    assert ACCEPTANCE_FRAGMENT.fragment_text not in serialized

    if result.candidate_pattern is not None:
        candidate_blob = json.dumps(
            {
                "pattern_id": result.candidate_pattern.pattern_id,
                "psychological_function": list(result.candidate_pattern.psychological_function),
                "language_characteristics": list(result.candidate_pattern.language_characteristics),
                "symbolic_characteristics": list(result.candidate_pattern.symbolic_characteristics),
                "therapeutic_intention": result.candidate_pattern.therapeutic_intention,
            }
        )
        assert ACCEPTANCE_FRAGMENT.fragment_text not in candidate_blob


def test_export_compatible_with_pattern_contract(pipeline: UniversalPatternExtractionPipeline):
    result = pipeline.extract_from_fragment(ACCEPTANCE_FRAGMENT)
    assert isinstance(result, ExtractionPipelineResult)
    assert result.tle_pattern_record is not None
    validate_tle_pattern_record(result.tle_pattern_record)

    exported = result.tle_pattern_record.to_dict()
    assert "fragment_text" not in exported
    assert "evidence_refs" in exported
