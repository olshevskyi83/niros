"""Raw Corpus I/O — deterministic JSON serialization for RawSourceCorpus artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from niros.raw_source import (
    RawSource,
    RawSourceCorpus,
    RawSourceSegment,
    build_raw_source_corpus,
)


def serialize_raw_source(source: RawSource) -> dict[str, Any]:
    """Return a JSON-serializable dictionary for one raw source."""
    return asdict(source)


def serialize_raw_segment(segment: RawSourceSegment) -> dict[str, Any]:
    """Return a JSON-serializable dictionary for one raw source segment."""
    return asdict(segment)


def serialize_raw_corpus(corpus: RawSourceCorpus) -> dict[str, Any]:
    """Return a JSON-serializable dictionary for one raw source corpus."""
    return {
        "source": serialize_raw_source(corpus.source),
        "segments": [serialize_raw_segment(segment) for segment in corpus.segments],
    }


def deserialize_raw_source(data: dict[str, Any]) -> RawSource:
    """Build a RawSource from serialized data."""
    return RawSource(**data)


def deserialize_raw_segment(data: dict[str, Any]) -> RawSourceSegment:
    """Build a RawSourceSegment from serialized data."""
    return RawSourceSegment(**data)


def deserialize_raw_corpus(data: dict[str, Any]) -> RawSourceCorpus:
    """Build a RawSourceCorpus from serialized data."""
    source = deserialize_raw_source(data["source"])
    segments = tuple(
        deserialize_raw_segment(segment_data) for segment_data in data.get("segments", [])
    )
    return build_raw_source_corpus(source, segments)


def save_raw_corpus(corpus: RawSourceCorpus, path: str | Path) -> Path:
    """Write one raw source corpus to JSON, creating parent directories if needed."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        serialize_raw_corpus(corpus),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )
    output_path.write_text(payload + "\n", encoding="utf-8")
    return output_path


def load_raw_corpus(path: str | Path) -> RawSourceCorpus:
    """Read one raw source corpus from JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return deserialize_raw_corpus(data)
