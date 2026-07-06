"""Tests for raw source contracts."""

from __future__ import annotations

from niros.raw_source import (
    RawSource,
    RawSourceCorpus,
    RawSourceSegment,
    build_raw_source_corpus,
    validate_raw_segment,
    validate_raw_source,
)


def _source(**overrides) -> RawSource:
    base = {
        "source_id": "source_001",
        "source_family": "mazatec_tradition",
        "title": "Therapeutic chant excerpt",
        "language": "mazatec",
        "source_type": "chant",
        "author": "Anonymous",
        "year": 1956,
    }
    base.update(overrides)
    return RawSource(**base)


def _segment(**overrides) -> RawSourceSegment:
    base = {
        "segment_id": "segment_001",
        "source_id": "source_001",
        "sequence_index": 0,
        "raw_text": "Original chant line.",
    }
    base.update(overrides)
    return RawSourceSegment(**base)


def test_default_values() -> None:
    source = RawSource(
        source_id="source_001",
        source_family="meditation",
        title="Breathing guidance",
        language="en",
        source_type="script",
    )
    segment = RawSourceSegment(
        segment_id="segment_001",
        source_id="source_001",
        sequence_index=0,
        raw_text="Breathe slowly.",
    )

    assert source.metadata == {}
    assert source.author == ""
    assert source.year is None
    assert segment.translation == ""
    assert segment.timestamp_start is None
    assert segment.timestamp_end is None
    assert segment.notes == ""


def test_corpus_ordering() -> None:
    source = _source()
    segments = (
        _segment(segment_id="segment_003", sequence_index=2, raw_text="Third line."),
        _segment(segment_id="segment_001", sequence_index=0, raw_text="First line."),
        _segment(segment_id="segment_002", sequence_index=1, raw_text="Second line."),
    )
    corpus = build_raw_source_corpus(source, segments)
    assert isinstance(corpus, RawSourceCorpus)
    assert [segment.segment_id for segment in corpus.segments] == [
        "segment_001",
        "segment_002",
        "segment_003",
    ]


def test_validate_raw_source_valid() -> None:
    assert validate_raw_source(_source()) == ()


def test_validate_raw_source_invalid() -> None:
    issues = validate_raw_source(
        RawSource(
            source_id="",
            source_family="",
            title="",
            language="",
            source_type="",
            year=-1,
        )
    )
    assert "source_id must not be empty" in issues
    assert "source_family must not be empty" in issues
    assert "title must not be empty" in issues
    assert "language must not be empty" in issues
    assert "source_type must not be empty" in issues
    assert "year must be non-negative when provided" in issues


def test_validate_raw_segment_valid() -> None:
    assert validate_raw_segment(_segment()) == ()


def test_validate_raw_segment_invalid() -> None:
    issues = validate_raw_segment(
        RawSourceSegment(
            segment_id="",
            source_id="",
            sequence_index=-1,
            raw_text="",
            timestamp_start=10.0,
            timestamp_end=5.0,
        )
    )
    assert "segment_id must not be empty" in issues
    assert "source_id must not be empty" in issues
    assert "sequence_index must be non-negative" in issues
    assert "raw_text must not be empty" in issues
    assert "timestamp_end must not be before timestamp_start" in issues


def test_deterministic_output() -> None:
    source = _source()
    segments = (
        _segment(segment_id="segment_002", sequence_index=1, raw_text="Second."),
        _segment(segment_id="segment_001", sequence_index=0, raw_text="First."),
    )
    first = build_raw_source_corpus(source, segments)
    second = build_raw_source_corpus(source, segments)
    assert first == second
