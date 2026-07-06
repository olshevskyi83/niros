"""Tests for semantic extraction prompt generation."""

from __future__ import annotations

from niros.raw_source import RawSource, RawSourceSegment
from niros.semantic_extraction_prompt import (
    REQUIRED_EXTRACTION_FIELDS,
    build_semantic_extraction_prompt,
)


def _source() -> RawSource:
    return RawSource(
        source_id="source_001",
        source_family="mazatec_tradition",
        title="Chant collection",
        language="mazatec",
        source_type="chant",
        author="Anonymous",
        year=1956,
    )


def _segment() -> RawSourceSegment:
    return RawSourceSegment(
        segment_id="source_001_segment_001",
        source_id="source_001",
        sequence_index=1,
        raw_text="May the heart be softened and fear released.",
    )


def test_contains_source_metadata() -> None:
    prompt = build_semantic_extraction_prompt(_source(), _segment())
    assert "source_id: source_001" in prompt
    assert "source_family: mazatec_tradition" in prompt
    assert "title: Chant collection" in prompt
    assert "language: mazatec" in prompt
    assert "source_type: chant" in prompt
    assert "author: Anonymous" in prompt
    assert "year: 1956" in prompt


def test_contains_raw_text() -> None:
    prompt = build_semantic_extraction_prompt(_source(), _segment())
    assert "May the heart be softened and fear released." in prompt
    assert "segment_id: source_001_segment_001" in prompt


def test_contains_required_extraction_fields() -> None:
    prompt = build_semantic_extraction_prompt(_source(), _segment())
    for field in REQUIRED_EXTRACTION_FIELDS:
        assert field in prompt


def test_requests_json() -> None:
    prompt = build_semantic_extraction_prompt(_source(), _segment())
    assert "valid JSON only" in prompt
    assert '"confidence": 0.0' in prompt


def test_deterministic() -> None:
    source = _source()
    segment = _segment()
    first = build_semantic_extraction_prompt(source, segment)
    second = build_semantic_extraction_prompt(source, segment)
    assert first == second


def test_prompt_contains_do_not_invent() -> None:
    prompt = build_semantic_extraction_prompt(_source(), _segment())
    assert "do not invent" in prompt.lower()


def test_prompt_contains_therapeutic_function() -> None:
    prompt = build_semantic_extraction_prompt(_source(), _segment())
    assert "therapeutic_function" in prompt
