"""TXT Source Importer — deterministic plain-text ingestion into RawSourceCorpus."""

from __future__ import annotations

import re
from pathlib import Path

from niros.raw_source import (
    RawSource,
    RawSourceCorpus,
    RawSourceSegment,
    build_raw_source_corpus,
)
from niros.source_registry import KnowledgeSourceRecord

_SENTENCE_BOUNDARY = re.compile(r"[.!?](?:\s+|$)")


def read_txt_source(path: str | Path, encoding: str = "utf-8") -> str:
    """Read a text file and normalize line endings to ``\\n``."""
    content = Path(path).read_text(encoding=encoding)
    return content.replace("\r\n", "\n").replace("\r", "\n")


def _find_sentence_split_point(text: str) -> int | None:
    """Return the end index of the last sentence boundary within *text*, if any."""
    split_point: int | None = None
    for match in _SENTENCE_BOUNDARY.finditer(text):
        split_point = match.end()
    return split_point


def _split_paragraph_into_chunks(paragraph: str, max_chars: int) -> list[str]:
    """Split one paragraph into chunks no longer than *max_chars*."""
    if len(paragraph) <= max_chars:
        return [paragraph]

    chunks: list[str] = []
    remaining = paragraph

    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break

        window = remaining[:max_chars]
        split_point = _find_sentence_split_point(window)

        if split_point is None or split_point <= 0:
            chunks.append(remaining[:max_chars])
            remaining = remaining[max_chars:].lstrip()
            continue

        chunks.append(remaining[:split_point].rstrip())
        remaining = remaining[split_point:].lstrip()

    return [chunk for chunk in chunks if chunk.strip()]


def split_text_into_segments(
    text: str,
    source_id: str,
    max_chars: int = 1200,
) -> tuple[RawSourceSegment, ...]:
    """Split text into deterministic raw source segments by paragraph."""
    paragraphs = re.split(r"\n\s*\n", text)
    chunk_texts: list[str] = []

    for paragraph in paragraphs:
        stripped = paragraph.strip()
        if not stripped:
            continue
        chunk_texts.extend(_split_paragraph_into_chunks(stripped, max_chars))

    segments: list[RawSourceSegment] = []
    for index, raw_text in enumerate(chunk_texts, start=1):
        segments.append(
            RawSourceSegment(
                segment_id=f"{source_id}_segment_{index:03d}",
                source_id=source_id,
                sequence_index=index,
                raw_text=raw_text.strip(),
            )
        )

    return tuple(segments)


def import_txt_as_raw_corpus(
    path: str | Path,
    source_record: KnowledgeSourceRecord,
    max_chars: int = 1200,
    encoding: str = "utf-8",
) -> RawSourceCorpus:
    """Read a TXT file and build a deterministic RawSourceCorpus."""
    text = read_txt_source(path, encoding=encoding)
    source = RawSource(
        source_id=source_record.source_id,
        source_family=source_record.source_family,
        title=source_record.title,
        language=source_record.language,
        source_type=source_record.source_type,
        author=source_record.author,
        year=source_record.year,
    )
    segments = split_text_into_segments(
        text,
        source_record.source_id,
        max_chars=max_chars,
    )
    return build_raw_source_corpus(source, segments)
