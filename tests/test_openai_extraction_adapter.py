"""Tests for OpenAI therapeutic extraction adapter contracts."""

from __future__ import annotations

from niros.openai_extraction_adapter import (
    DEFAULT_ADAPTER_VERSION,
    DEFAULT_EXTRACTION_PROMPT_VERSION,
    ExtractionRequest,
    ExtractionResponse,
    build_extraction_request,
    build_extraction_response,
    validate_extraction_response,
)
from niros.raw_source import RawSource, RawSourceSegment
from niros.therapeutic_extraction import TherapeuticFunctionExtraction


def _source() -> RawSource:
    return RawSource(
        source_id="source_001",
        source_family="mazatec_tradition",
        title="Chant source",
        language="mazatec",
        source_type="chant",
    )


def _segment() -> RawSourceSegment:
    return RawSourceSegment(
        segment_id="segment_001",
        source_id="source_001",
        sequence_index=0,
        raw_text="Original chant line.",
    )


def _extraction(**overrides) -> TherapeuticFunctionExtraction:
    base = {
        "extraction_id": "extraction_source_001_segment_001_self_compassion",
        "source_id": "source_001",
        "segment_id": "segment_001",
        "therapeutic_function": "self_compassion",
        "evidence_text": "Evidence from the chant segment.",
    }
    base.update(overrides)
    return TherapeuticFunctionExtraction(**base)


def test_request_defaults() -> None:
    request = ExtractionRequest(
        source_id="source_001",
        segment_id="segment_001",
        raw_text="Line.",
        language="mazatec",
        source_family="mazatec_tradition",
    )
    assert request.extraction_prompt_version == DEFAULT_EXTRACTION_PROMPT_VERSION


def test_request_mapping() -> None:
    request = build_extraction_request(_segment(), _source())
    assert request.source_id == "source_001"
    assert request.segment_id == "segment_001"
    assert request.raw_text == "Original chant line."
    assert request.language == "mazatec"
    assert request.source_family == "mazatec_tradition"


def test_response_defaults() -> None:
    request = build_extraction_request(_segment(), _source())
    response = build_extraction_response(request, _extraction())
    assert response.raw_llm_output == ""
    assert response.adapter_version == DEFAULT_ADAPTER_VERSION


def test_response_preserves_extraction() -> None:
    request = build_extraction_request(_segment(), _source())
    extraction = _extraction()
    response = build_extraction_response(request, extraction)
    assert response.extraction == extraction
    assert response.request == request


def test_validation_success() -> None:
    request = build_extraction_request(_segment(), _source())
    response = build_extraction_response(request, _extraction())
    assert validate_extraction_response(response) == ()


def test_validation_mismatch_source() -> None:
    request = build_extraction_request(_segment(), _source())
    response = build_extraction_response(
        request,
        _extraction(source_id="source_other"),
    )
    issues = validate_extraction_response(response)
    assert "extraction source_id must match request source_id" in issues


def test_validation_mismatch_segment() -> None:
    request = build_extraction_request(_segment(), _source())
    response = build_extraction_response(
        request,
        _extraction(segment_id="segment_other"),
    )
    issues = validate_extraction_response(response)
    assert "extraction segment_id must match request segment_id" in issues


def test_deterministic_output() -> None:
    request = build_extraction_request(_segment(), _source())
    extraction = _extraction()
    first = build_extraction_response(request, extraction)
    second = build_extraction_response(request, extraction)
    assert first == second
    assert validate_extraction_response(first) == validate_extraction_response(second)
