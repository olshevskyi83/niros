"""Tests for raw corpus JSON I/O."""

from __future__ import annotations

import json
from pathlib import Path

from niros.raw_corpus_io import (
    deserialize_raw_corpus,
    deserialize_raw_segment,
    deserialize_raw_source,
    load_raw_corpus,
    save_raw_corpus,
    serialize_raw_corpus,
    serialize_raw_segment,
    serialize_raw_source,
)
from niros.raw_source import RawSource, RawSourceCorpus, RawSourceSegment, build_raw_source_corpus


def _source() -> RawSource:
    return RawSource(
        source_id="source_001",
        source_family="mazatec_tradition",
        title="Chant collection",
        language="mazatec",
        source_type="chant",
        author="Anonymous",
        year=1956,
        metadata={"region": "Sierra Mazateca"},
    )


def _segment(**overrides) -> RawSourceSegment:
    base = {
        "segment_id": "source_001_segment_001",
        "source_id": "source_001",
        "sequence_index": 1,
        "raw_text": "Opening chant.",
        "translation": "Translated opening.",
        "timestamp_start": 0.0,
        "timestamp_end": 12.5,
        "notes": "Intro section.",
    }
    base.update(overrides)
    return RawSourceSegment(**base)


def _corpus() -> RawSourceCorpus:
    return build_raw_source_corpus(
        _source(),
        (
            _segment(),
            _segment(
                segment_id="source_001_segment_002",
                sequence_index=2,
                raw_text="Closing chant.",
                translation="",
                timestamp_start=None,
                timestamp_end=None,
                notes="",
            ),
        ),
    )


def test_serialize_source() -> None:
    payload = serialize_raw_source(_source())
    assert payload == {
        "source_id": "source_001",
        "source_family": "mazatec_tradition",
        "title": "Chant collection",
        "language": "mazatec",
        "source_type": "chant",
        "author": "Anonymous",
        "year": 1956,
        "metadata": {"region": "Sierra Mazateca"},
    }


def test_serialize_segment() -> None:
    payload = serialize_raw_segment(_segment())
    assert payload["segment_id"] == "source_001_segment_001"
    assert payload["raw_text"] == "Opening chant."
    assert payload["translation"] == "Translated opening."
    assert payload["timestamp_start"] == 0.0
    assert payload["timestamp_end"] == 12.5
    assert payload["notes"] == "Intro section."


def test_serialize_corpus() -> None:
    payload = serialize_raw_corpus(_corpus())
    assert set(payload.keys()) == {"source", "segments"}
    assert payload["source"]["source_id"] == "source_001"
    assert len(payload["segments"]) == 2
    assert payload["segments"][0]["segment_id"] == "source_001_segment_001"
    assert payload["segments"][1]["segment_id"] == "source_001_segment_002"


def test_deserialize_source() -> None:
    source = deserialize_raw_source(serialize_raw_source(_source()))
    assert source == _source()


def test_deserialize_segment() -> None:
    segment = deserialize_raw_segment(serialize_raw_segment(_segment()))
    assert segment == _segment()


def test_deserialize_corpus() -> None:
    corpus = deserialize_raw_corpus(serialize_raw_corpus(_corpus()))
    assert corpus == _corpus()


def test_roundtrip_preserves_source() -> None:
    corpus = _corpus()
    loaded = deserialize_raw_corpus(serialize_raw_corpus(corpus))
    assert loaded.source == corpus.source


def test_roundtrip_preserves_segments() -> None:
    corpus = _corpus()
    loaded = deserialize_raw_corpus(serialize_raw_corpus(corpus))
    assert loaded.segments == corpus.segments


def test_save_load_works_with_tmp_path(tmp_path: Path) -> None:
    corpus = _corpus()
    output_path = tmp_path / "raw_corpus" / "source_001.json"
    save_raw_corpus(corpus, output_path)
    loaded = load_raw_corpus(output_path)
    assert loaded == corpus


def test_save_creates_parent_directory(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "raw_corpus" / "source_001.json"
    save_raw_corpus(_corpus(), output_path)
    assert output_path.exists()
    assert output_path.parent.exists()


def test_output_deterministic(tmp_path: Path) -> None:
    corpus = _corpus()
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    save_raw_corpus(corpus, first_path)
    save_raw_corpus(corpus, second_path)
    first_text = first_path.read_text(encoding="utf-8")
    second_text = second_path.read_text(encoding="utf-8")
    assert first_text == second_text
    assert json.loads(first_text) == json.loads(second_text)
