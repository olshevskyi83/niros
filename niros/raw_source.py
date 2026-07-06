"""Raw Source — generic contracts for therapeutic chant and script material."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RawSource:
    source_id: str
    source_family: str
    title: str
    language: str
    source_type: str
    author: str = ""
    year: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RawSourceSegment:
    segment_id: str
    source_id: str
    sequence_index: int
    raw_text: str
    translation: str = ""
    timestamp_start: float | None = None
    timestamp_end: float | None = None
    notes: str = ""


@dataclass(frozen=True)
class RawSourceCorpus:
    source: RawSource
    segments: tuple[RawSourceSegment, ...] = field(default_factory=tuple)


def build_raw_source_corpus(
    source: RawSource,
    segments: tuple[RawSourceSegment, ...] | list[RawSourceSegment],
) -> RawSourceCorpus:
    """Build a raw source corpus with segments sorted by sequence_index."""
    return RawSourceCorpus(
        source=source,
        segments=tuple(sorted(segments, key=lambda segment: segment.sequence_index)),
    )


def validate_raw_source(source: RawSource) -> tuple[str, ...]:
    """Return validation issue strings for a raw source."""
    issues: list[str] = []

    if not source.source_id.strip():
        issues.append("source_id must not be empty")
    if not source.source_family.strip():
        issues.append("source_family must not be empty")
    if not source.title.strip():
        issues.append("title must not be empty")
    if not source.language.strip():
        issues.append("language must not be empty")
    if not source.source_type.strip():
        issues.append("source_type must not be empty")
    if source.year is not None and source.year < 0:
        issues.append("year must be non-negative when provided")

    return tuple(issues)


def validate_raw_segment(segment: RawSourceSegment) -> tuple[str, ...]:
    """Return validation issue strings for a raw source segment."""
    issues: list[str] = []

    if not segment.segment_id.strip():
        issues.append("segment_id must not be empty")
    if not segment.source_id.strip():
        issues.append("source_id must not be empty")
    if segment.sequence_index < 0:
        issues.append("sequence_index must be non-negative")
    if not segment.raw_text.strip():
        issues.append("raw_text must not be empty")
    if (
        segment.timestamp_start is not None
        and segment.timestamp_end is not None
        and segment.timestamp_end < segment.timestamp_start
    ):
        issues.append("timestamp_end must not be before timestamp_start")

    return tuple(issues)
