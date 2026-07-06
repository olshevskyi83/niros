"""Tests for TXT source importer."""

from __future__ import annotations

from pathlib import Path

from niros.raw_source import RawSourceCorpus
from niros.source_registry import KnowledgeSourceRecord
from niros.txt_source_importer import (
    import_txt_as_raw_corpus,
    read_txt_source,
    split_text_into_segments,
)


def _source_record() -> KnowledgeSourceRecord:
    return KnowledgeSourceRecord(
        source_id="source_001",
        source_family="mazatec_tradition",
        title="Chant collection",
        source_type="chant",
        language="mazatec",
        author="Anonymous",
        year=1956,
    )


def test_read_txt_source_reads_file(tmp_path: Path) -> None:
    path = tmp_path / "chants.txt"
    path.write_text("First line.\nSecond line.", encoding="utf-8")
    assert read_txt_source(path) == "First line.\nSecond line."


def test_line_endings_normalized(tmp_path: Path) -> None:
    path = tmp_path / "chants.txt"
    path.write_bytes(b"Line one.\r\nLine two.\rOld mac.")
    assert read_txt_source(path) == "Line one.\nLine two.\nOld mac."


def test_split_text_into_segments_splits_paragraphs() -> None:
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    segments = split_text_into_segments(text, "source_001")
    assert len(segments) == 3
    assert [segment.raw_text for segment in segments] == [
        "First paragraph.",
        "Second paragraph.",
        "Third paragraph.",
    ]


def test_empty_paragraphs_ignored() -> None:
    text = "First paragraph.\n\n\n\nSecond paragraph."
    segments = split_text_into_segments(text, "source_001")
    assert len(segments) == 2
    assert segments[0].raw_text == "First paragraph."
    assert segments[1].raw_text == "Second paragraph."


def test_segment_ids_deterministic() -> None:
    text = "Alpha.\n\nBeta."
    segments = split_text_into_segments(text, "source_001")
    assert [segment.segment_id for segment in segments] == [
        "source_001_segment_001",
        "source_001_segment_002",
    ]


def test_sequence_index_deterministic() -> None:
    text = "Alpha.\n\nBeta.\n\nGamma."
    segments = split_text_into_segments(text, "source_001")
    assert [segment.sequence_index for segment in segments] == [1, 2, 3]


def test_import_txt_as_raw_corpus_creates_raw_source_corpus(tmp_path: Path) -> None:
    path = tmp_path / "chants.txt"
    path.write_text("Opening chant.\n\nClosing chant.", encoding="utf-8")
    corpus = import_txt_as_raw_corpus(path, _source_record())
    assert isinstance(corpus, RawSourceCorpus)
    assert len(corpus.segments) == 2
    assert corpus.segments[0].raw_text == "Opening chant."
    assert corpus.segments[1].raw_text == "Closing chant."


def test_source_metadata_preserved(tmp_path: Path) -> None:
    path = tmp_path / "chants.txt"
    path.write_text("One paragraph.", encoding="utf-8")
    corpus = import_txt_as_raw_corpus(path, _source_record())
    assert corpus.source.source_id == "source_001"
    assert corpus.source.source_family == "mazatec_tradition"
    assert corpus.source.title == "Chant collection"
    assert corpus.source.source_type == "chant"
    assert corpus.source.language == "mazatec"
    assert corpus.source.author == "Anonymous"
    assert corpus.source.year == 1956


def test_long_paragraph_split_respects_max_chars() -> None:
    sentence = "Word " * 40
    long_paragraph = f"{sentence.strip()}. {sentence.strip()}."
    segments = split_text_into_segments(long_paragraph, "source_001", max_chars=120)
    assert len(segments) > 1
    assert all(len(segment.raw_text) <= 120 for segment in segments)

    no_sentence_break = "x" * 250
    hard_split_segments = split_text_into_segments(
        no_sentence_break,
        "source_001",
        max_chars=100,
    )
    assert len(hard_split_segments) == 3
    assert [len(segment.raw_text) for segment in hard_split_segments] == [100, 100, 50]


def test_output_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "chants.txt"
    path.write_text("First.\n\nSecond.\n\nThird.", encoding="utf-8")
    record = _source_record()
    first = import_txt_as_raw_corpus(path, record)
    second = import_txt_as_raw_corpus(path, record)
    assert first == second
